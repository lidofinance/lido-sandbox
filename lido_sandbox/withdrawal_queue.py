from lido_sandbox.objects import (
    BatchesCalculationState,
    Checkpoint,
    WithdrawalRequest,
    WithdrawalRequestStatus,
)
from collections import defaultdict
from time import time


class WithdrawalQueue:
    _is_bunker = False
    _queue: dict[int, WithdrawalRequest]
    _checkpoints: dict[int, Checkpoint]
    _request_by_owner: dict[str, set[int]]
    _last_request_id: int = 0
    _last_finalized_request_id: int = 0
    _last_report_timestamp: int = 0
    _locked_ether_amount: int = 0
    _last_checkpoint_index: int = 0

    E27_PRECISION_BASE: int = 10**27
    MAX_BATCHES_LENGTH: int = 36
    NOT_FOUND: int = 0

    def __init__(self):
        self._queue = defaultdict(lambda: WithdrawalRequest())
        self._checkpoints = defaultdict(lambda: Checkpoint())
        self._request_by_owner = defaultdict(set)

    def is_bunker_mode_active(self) -> bool:
        return self._is_bunker

    def get_last_request_id(self) -> int:
        return self._last_request_id

    def get_last_finalized_request_id(self) -> int:
        return self._last_finalized_request_id

    def get_locked_ether_amount(self) -> int:
        return self._locked_ether_amount

    def get_last_checkpoint_index(self) -> int:
        return self._last_checkpoint_index

    def unfinalized_request_number(self) -> int:
        return self.get_last_request_id() - self.get_last_finalized_request_id()

    def unfinalized_steth(self) -> int:
        queue = self._get_queue()
        return (
            queue[self.get_last_request_id()].cumulative_steth
            - queue[self.get_last_finalized_request_id()].cumulative_steth
        )

    def calculate_finalization_batches(
        self,
        max_share_rate: int,
        max_timestamp: int,
        max_requests_per_call: int,
        state: BatchesCalculationState,
    ) -> BatchesCalculationState:
        assert not state.finished and state.remaining_eth_budget != 0

        current_id = 0
        prev_request = None
        prev_request_share_rate = 0

        if state.batches_length == 0:
            current_id = self.get_last_finalized_request_id() + 1

            prev_request = self._get_queue()[current_id - 1]
        else:
            last_handled_request_id = state.batches[state.batches_length - 1]
            current_id = last_handled_request_id + 1

            prev_request = self._get_queue()[last_handled_request_id]
            prev_request_share_rate, _, _ = self._calc_batch(
                self._get_queue()[last_handled_request_id - 1], prev_request
            )

        next_call_request_id = current_id + max_requests_per_call
        queue_length = self.get_last_request_id() + 1

        while current_id < queue_length and current_id < next_call_request_id:
            request = self._get_queue()[current_id]

            if request.timestamp > max_timestamp:
                break  # max timestamp break

            request_share_rate, eth_to_finalize, shares = self._calc_batch(
                prev_request, request
            )

            if request_share_rate > max_share_rate:
                # discounted
                eth_to_finalize = (shares * max_share_rate) // self.E27_PRECISION_BASE

            if eth_to_finalize > state.remaining_eth_budget:
                break  # budget break
            state.remaining_eth_budget -= eth_to_finalize

            if state.batches_length != 0 and (
                prev_request.report_timestamp == request.report_timestamp
                or (
                    # both requests are below the line
                    prev_request_share_rate <= max_share_rate
                    and request_share_rate <= max_share_rate
                )
                or (
                    # both requests are above the line
                    prev_request_share_rate > max_share_rate
                    and request_share_rate > max_share_rate
                )
            ):
                state.batches[
                    state.batches_length - 1
                ] = current_id  # extend the last batch
            else:
                # to be able to check batches on-chain we need array to have limited length
                if state.batches_length == self.MAX_BATCHES_LENGTH:
                    break

                # create a new batch
                state.batches[state.batches_length] = current_id
                state.batches_length += 1

            prev_request_share_rate = request_share_rate
            prev_request = request
            current_id += 1

        state.finished = current_id == queue_length or current_id < next_call_request_id

        return state

    def prefinalize(self, batches: list[int], max_share_rate: int) -> tuple[int, int]:
        assert max_share_rate != 0
        assert len(batches)

        last_finalized_request_id = self.get_last_finalized_request_id()
        last_request_id = self.get_last_request_id()

        assert batches[0] > last_finalized_request_id
        assert batches[-1] <= last_request_id

        current_batch_index = 0
        prev_batch_end_request_id = last_finalized_request_id
        prev_batch_end = self._get_queue()[prev_batch_end_request_id]
        eth_to_lock = 0
        shares_to_burn = 0

        while current_batch_index < len(batches):
            batch_end_request_id = batches[current_batch_index]
            assert batch_end_request_id > prev_batch_end_request_id

            batch_end = self._get_queue()[batch_end_request_id]
            batch_share_rate, steth, shares = self._calc_batch(
                prev_batch_end, batch_end
            )

            if batch_share_rate > max_share_rate:
                # discounted
                eth_to_lock += shares * max_share_rate // self.E27_PRECISION_BASE
            else:
                # nominal
                eth_to_lock += steth
            shares_to_burn += shares

            prev_batch_end_request_id = batch_end_request_id
            prev_batch_end = batch_end
            current_batch_index += 1

        return eth_to_lock, shares_to_burn

    def _finalize(
        self,
        last_request_id_to_be_finalized: int,
        amount_of_eth: int,
        max_share_rate: int,
    ) -> None:
        assert last_request_id_to_be_finalized <= self.get_last_request_id()
        last_finalized_request_id = self.get_last_finalized_request_id()
        assert last_request_id_to_be_finalized > last_finalized_request_id

        last_finalized_request = self._get_queue()[last_finalized_request_id]
        request_to_finalize = self._get_queue()[last_request_id_to_be_finalized]

        steth_to_finalize = (
            request_to_finalize.cumulative_steth
            - last_finalized_request.cumulative_steth
        )
        assert amount_of_eth <= steth_to_finalize

        first_request_id_to_finalize = last_finalized_request_id + 1
        last_checkpoint_index = self.get_last_checkpoint_index()

        # add a new checkpoint with current finalization max share rate
        self._get_checkpoints()[last_checkpoint_index + 1] = Checkpoint(
            first_request_id_to_finalize, max_share_rate
        )
        self._set_last_checkpoint_index(last_checkpoint_index + 1)

        self._set_locked_ether_amount(self.get_locked_ether_amount() + amount_of_eth)
        self._set_last_finalized_request_id(last_request_id_to_be_finalized)

    def _enqueue(self, amount_of_steth: int, amount_of_shares: int, owner: str) -> int:
        last_request_id = self.get_last_request_id()
        last_request = self._get_queue()[last_request_id]

        cumulative_shares = last_request.cumulative_shares + amount_of_shares
        cumulative_steth = last_request.cumulative_steth + amount_of_steth

        request_id = last_request_id + 1

        self._set_last_request_id(request_id)

        new_request = WithdrawalRequest(
            cumulative_steth,
            cumulative_shares,
            owner,
            int(time()),
            False,
            self._get_last_report_timestamp(),
        )
        self._get_queue()[request_id] = new_request
        assert self._get_requests_by_owner()[owner].add(request_id)

        return request_id

    def _get_status(self, request_id: int) -> WithdrawalRequestStatus:
        assert request_id != 0 and request_id <= self.get_last_request_id()

        request = self._get_queue()[request_id]
        previous_request = self._get_queue()[request_id - 1]

        status = WithdrawalRequestStatus(
            request.cumulative_steth - previous_request.cumulative_steth,
            request.cumulative_shares - previous_request.cumulative_shares,
            request.owner,
            request.timestamp,
            request_id <= self.get_last_finalized_request_id(),
            request.claimed,
        )
        return status

    def _find_checkpoint_hint(self, request_id: int, start: int, end: int) -> int:
        assert request_id != 0 and request_id <= self.get_last_request_id()

        last_checkpoint_index = self.get_last_checkpoint_index()
        assert start != 0 and end <= last_checkpoint_index

        if (
            last_checkpoint_index == 0
            or request_id > self.get_last_finalized_request_id()
            or start > end
        ):
            return self.NOT_FOUND

        # Right boundary
        if request_id >= self._get_checkpoints()[end].from_request_id:
            # it's the last checkpoint, so it's valid
            if end == last_checkpoint_index:
                return end
            # it fits right before the next checkpoint
            if request_id < self._get_checkpoints()[end + 1].from_request_id:
                return end
            return self.NOT_FOUND

        # Left boundary
        if request_id < self._get_checkpoints()[start].from_request_id:
            return self.NOT_FOUND

        # Binary search
        min_index = start
        max_index = end - 1
        while max_index > min_index:
            mid_index = (max_index + min_index + 1) // 2
            if self._get_checkpoints()[mid_index].from_request_id <= request_id:
                min_index = mid_index
            else:
                max_index = mid_index - 1
        return min_index

    def _claim(self, request_id: int, hint: int, recipient: str) -> None:
        assert request_id != 0
        assert request_id <= self.get_last_finalized_request_id()

        request = self._get_queue()[request_id]
        assert not request.claimed

        request.claimed = True
        self._get_requests_by_owner()[request.owner].remove(request_id)

        eth_with_discount = self._calculate_claimable_ether(request, request_id, hint)
        self.locked_ether_amount -= eth_with_discount
        self._send_value(recipient, eth_with_discount)

    def _calculate_claimable_ether(
        self, request: WithdrawalRequest, request_id: int, hint: int
    ) -> int:
        assert hint != 0

        last_checkpoint_index = self.get_last_checkpoint_index()
        assert hint <= last_checkpoint_index

        checkpoint = self._get_checkpoints()[hint]

        assert request_id >= checkpoint.from_request_id
        if hint < last_checkpoint_index:
            next_checkpoint = self._get_checkpoints()[hint + 1]
            assert next_checkpoint.from_request_id > request_id

        prev_request = self._get_queue()[request_id - 1]
        batch_share_rate, eth, shares = self._calc_batch(prev_request, request)

        if batch_share_rate > checkpoint.max_share_rate:
            eth = shares * checkpoint.max_share_rate / self.E27_PRECISION_BASE

        return eth

    def _initialize_queue(self) -> None:
        queue = self._get_queue()
        queue[0] = WithdrawalRequest()
        checkpoints = self._get_checkpoints()
        checkpoints[self.get_last_checkpoint_index()] = Checkpoint(0, 0)

    def _send_value(self, recipient: str, amount: int) -> None:
        pass

    def calc_batch(
        self, pre_start_request: WithdrawalRequest, end_request: WithdrawalRequest
    ) -> tuple[int, int, int]:
        steth = end_request.cumulative_steth - pre_start_request.cumulative_steth
        shares = end_request.cumulative_shares - pre_start_request.cumulative_shares
        share_rate = steth * self.E27_PRECISION_BASE // shares
        return share_rate, steth, shares

    def _get_queue(self) -> dict[int, WithdrawalRequest]:
        return self._queue

    def _get_checkpoints(self) -> dict[int, Checkpoint]:
        return self._checkpoints

    def _get_requests_by_owner(self) -> dict[str, set[WithdrawalRequest]]:
        return self._request_by_owner

    def _get_last_report_timestamp(self) -> int:
        return self._last_report_timestamp

    def _set_last_request_id(self, last_request_id: int) -> None:
        self._last_request_id = last_request_id

    def _set_last_finalized_request_id(self, last_finalized_request_id: int) -> None:
        self._last_finalized_request_id = last_finalized_request_id

    def _set_last_checkpoint_index(self, last_checkpoint_index: int) -> None:
        self._last_checkpoint_index = last_checkpoint_index

    def _set_locked_ether_amount(self, locked_ether_amount: int) -> None:
        self._locked_ether_amount = locked_ether_amount

    def _set_last_report_timestamp(self, last_report_timestamp: int) -> None:
        self._last_report_timestamp = last_report_timestamp
