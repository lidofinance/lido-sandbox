from lido_sandbox.objects import NodeOperator, NodeOperatorSummary
from lido_sandbox.libs import MinFirstAllocationStrategy
from lido_sandbox.locator import Locator
from lido_sandbox.contract import Contract
from time import time


class StakingModule(Contract):
    _locator: Locator

    _node_operators: dict[int, NodeOperator]
    _node_operator_summary: NodeOperatorSummary
    _total_operators_count: int = 0
    _active_node_operators_count: int = 0
    _signing_keys_mapping: dict[int, tuple[str, str]]
    _nonce: int = 0
    _type: str
    _stuck_penalty_delay: int = 30

    MAX_UINT64 = 2**64 - 1
    MAX_NODE_OPERATORS_COUNT: int = 200

    def __init__(self, type: str, locator: Locator, address: str) -> None:
        super().__init__(address)

        self._type = type
        self._locator = locator
        self._node_operators = {}
        self._node_operator_summary = NodeOperatorSummary()
        self._signing_keys_mapping = {}

    def add_node_operator(self, name: str, reward_address: str) -> int:
        id = self.get_node_operators_count()

        assert id < self.MAX_NODE_OPERATORS_COUNT, "MAX_OPERATORS_COUNT_EXCEEDED"

        self._total_operators_count += 1
        self._active_node_operators_count += 1
        self._node_operators[id] = NodeOperator(
            active=True,
            name=name,
            reward_address=reward_address,
        )

        return id

    def activate_node_operator(self, node_operator_id: int) -> None:
        assert not self.get_node_operator_is_active(node_operator_id)

        self._active_node_operators_count += 1
        self._node_operators[node_operator_id].active = True
        self._increase_validators_keys_nonce()

    def deactivate_node_operator(self, node_operator_id: int) -> None:
        assert self.get_node_operator_is_active(node_operator_id)

        node_operator = self._node_operators[node_operator_id]
        self._active_node_operators_count -= 1
        node_operator.active = False

        if (
            node_operator.vetted_signing_keys_count
            > node_operator.deposited_signing_keys_count
        ):
            node_operator.vetted_signing_keys_count = (
                node_operator.deposited_signing_keys_count
            )
            self._update_summary_max_validators_count(node_operator_id)

        self._increase_validators_keys_nonce()

    def set_node_operator_name(self, node_operator_id: int, name: str) -> None:
        node_operator = self._node_operators[node_operator_id]
        assert node_operator.name != name, "SAME_NAME"
        node_operator.name = name

    def set_node_operator_reward_address(
        self, node_operator_id: int, reward_address: str
    ) -> None:
        node_operator = self._node_operators[node_operator_id]
        assert node_operator.reward_address != reward_address, "SAME_REWARD_ADDRESS"
        node_operator.reward_address = reward_address

    def set_node_operator_staking_limit(
        self, node_operator_id: int, vetted_signing_keys_count: int
    ) -> None:
        node_operator = self._node_operators[node_operator_id]
        vetted_signing_keys_count_before = node_operator.vetted_signing_keys_count
        deposited_signing_keys_count = node_operator.deposited_signing_keys_count
        total_signing_keys_count = node_operator.total_signing_keys_count

        vetted_signing_keys_count_after = min(
            total_signing_keys_count,
            max(vetted_signing_keys_count, deposited_signing_keys_count),
        )

        if vetted_signing_keys_count_after == vetted_signing_keys_count_before:
            return

        node_operator.vetted_signing_keys_count = vetted_signing_keys_count_after
        self._update_summary_max_validators_count(node_operator_id)
        self._increase_validators_keys_nonce()

    def add_signing_keys(
        self, node_operator_id: int, keys: list[tuple[str, str]]
    ) -> None:
        self._add_signing_keys(node_operator_id, keys)

    def _add_signing_keys(
        self, node_operator_id: int, keys: list[tuple[str, str]]
    ) -> None:
        keys_count = len(keys)

        assert self.MAX_UINT64 >= keys_count > 0, "INVALID_KEYS_COUNT"

        node_operator = self._node_operators[node_operator_id]
        total_signing_keys_count = node_operator.total_signing_keys_count

        assert (
            self.MAX_UINT64 >= total_signing_keys_count + keys_count
        ), "INVALID_TOTAL_KEYS_COUNT"

        if node_operator_id in self._signing_keys_mapping:
            self._signing_keys_mapping[node_operator_id] += keys
        else:
            self._signing_keys_mapping[node_operator_id] = keys

        node_operator.total_signing_keys_count += keys_count
        self._node_operator_summary.total_keys_count += keys_count
        self._increase_validators_keys_nonce()

    def get_type(self) -> str:
        return self._type

    def get_staking_module_summary(self) -> tuple[int, int, int]:
        return (
            self._node_operator_summary.exited_keys_count,
            self._node_operator_summary.deposited_keys_count,
            self._node_operator_summary.max_validators_count
            - self._node_operator_summary.deposited_keys_count,
        )

    def get_node_operator_summary(
        self, node_operator_id: int
    ) -> tuple[bool, int, int, int, int, int, int, int]:
        node_operator = self._node_operators[node_operator_id]
        depositable_validators_count = (
            node_operator.max_validators_count
            - node_operator.deposited_signing_keys_count
        )

        return (
            node_operator.is_target_limit_active,
            node_operator.target_validators_count,
            node_operator.stuck_validators_count,
            node_operator.refunded_validators_count,
            node_operator.stuck_penalty_end_timestamp,
            node_operator.exited_signing_keys_count,
            node_operator.deposited_signing_keys_count,
            depositable_validators_count,
        )

    def get_nonce(self) -> int:
        return self._nonce

    def get_node_operators_count(self) -> int:
        return self._total_operators_count

    def get_active_node_operators_count(self) -> int:
        return self._active_node_operators_count

    def get_node_operator_is_active(self, node_operator_id: int) -> bool:
        return self._node_operators[node_operator_id].active

    def get_node_operator_ids(self, offset: int, limit: int) -> list[int]:
        node_operators_count = self.get_node_operators_count()
        if offset >= node_operators_count or limit == 0:
            return []
        node_operator_ids = [
            offset + i for i in range(min(limit, node_operators_count - offset))
        ]
        return node_operator_ids

    def on_rewards_minted(self, *args):
        pass

    def update_stuck_validators_count(
        self, node_operator_ids: list[int], stuck_validators_counts: list[int]
    ) -> None:
        assert len(node_operator_ids) == len(stuck_validators_counts)
        node_operators_count = len(node_operator_ids)
        total_node_operators_count = self.get_node_operators_count()

        for i in range(node_operators_count):
            node_operator_id = node_operator_ids[i]
            validators_count = stuck_validators_counts[i]
            assert node_operator_id < total_node_operators_count
            self._update_stuck_validators_count(node_operator_id, validators_count)

        self._increase_validators_keys_nonce()

    def update_exited_validators_count(
        self, node_operator_ids: list[int], exited_validators_counts: list[int]
    ) -> None:
        assert len(node_operator_ids) == len(exited_validators_counts)
        node_operators_count = len(node_operator_ids)
        total_node_operators_count = self.get_node_operators_count()

        for i in range(node_operators_count):
            node_operator_id = node_operator_ids[i]
            validators_count = exited_validators_counts[i]
            assert node_operator_id < total_node_operators_count
            self._update_exited_validators_count(node_operator_id, validators_count)

        self._increase_validators_keys_nonce()

    def update_refunded_validators_count(
        self, node_operator_id: int, refunded_validators_count: int
    ) -> None:
        self._update_refund_validators_keys_count(
            node_operator_id, refunded_validators_count
        )

    def update_target_validators_limits(
        self, node_operator_id: int, is_target_limit_active: bool, target_limit: int
    ) -> None:
        assert target_limit <= self.MAX_UINT64

        self._node_operators[
            node_operator_id
        ].is_target_limit_active = is_target_limit_active
        self._node_operators[node_operator_id].target_validators_count = (
            target_limit if is_target_limit_active else 0
        )

        self._update_summary_max_validators_count(node_operator_id)
        self._increase_validators_keys_nonce()

    def unsafe_update_validators_count(
        self,
        node_operator_id: int,
        exited_validators_count: int,
        stuck_validators_count: int,
    ) -> None:
        self._update_stuck_validators_count(node_operator_id, stuck_validators_count)
        self._update_exited_validators_count(
            node_operator_id, exited_validators_count, True
        )
        self._increase_validators_keys_nonce()

    def obtain_deposit_data(self, deposits_count: int) -> tuple[list[str], list[str]]:
        if deposits_count == 0:
            return [], []

        (
            allocated_keys_count,
            node_operator_ids,
            active_keys_count_after_allocation,
        ) = self._get_signing_keys_allocation_data(deposits_count)

        assert allocated_keys_count == deposits_count

        public_keys, signatures = self._load_allocated_signing_keys(
            allocated_keys_count, node_operator_ids, active_keys_count_after_allocation
        )
        self._increase_validators_keys_nonce()

        return public_keys, signatures

    def on_exited_and_stuck_validators_counts_updated(self):
        self._distribute_rewards()

    def _distribute_rewards(self) -> int:
        lido = self._locator.lido
        burner = self._locator.burner

        shares_to_distribute = lido.shares_of(self.address)
        if shares_to_distribute == 0:
            return 0

        recipients, shares, penalized = self.get_rewards_distribution(
            shares_to_distribute
        )

        distributed = 0
        to_burn = 0

        for idx in range(len(recipients)):
            if shares[idx] < 2:
                continue
            if penalized[idx]:
                shares[idx] >>= 1
                to_burn += shares[idx]

            lido.transfer_shares(self.address, recipients[idx], shares[idx])
            distributed += shares[idx]

        if to_burn > 0:
            burner.request_burn_shares(self.address, to_burn)
        return distributed

    def get_rewards_distribution(
        self, total_reward_shares: int
    ) -> tuple[list[str], list[int], list[bool]]:
        node_operator_count = self.get_node_operators_count()
        active_count = self.get_active_node_operators_count()

        recipients = ["" for _ in range(active_count)]
        shares = [0 for _ in range(active_count)]
        penalized = [False for _ in range(active_count)]
        idx = 0

        total_active_validators_count = 0
        for operator_id in range(node_operator_count):
            if not self.get_node_operator_is_active(operator_id):
                continue

            node_operator = self._node_operators[operator_id]
            total_exited_validators = node_operator.exited_signing_keys_count
            total_deposited_validators = node_operator.deposited_signing_keys_count

            assert total_deposited_validators >= total_exited_validators
            active_validators_count = (
                total_deposited_validators - total_exited_validators
            )

            total_active_validators_count += active_validators_count

            recipients[idx] = node_operator.reward_address
            # prefill shares array with 'key share' for recipient, see below
            shares[idx] = active_validators_count
            penalized[idx] = self.is_operator_penalized(operator_id)

            idx += 1

        if total_active_validators_count == 0:
            return recipients, shares, penalized

        for idx in range(active_count):
            # unsafe division used below for gas savings. It's safe in the current case
            # because SafeMath.div() only validates that the divider isn't equal to zero.
            # total_active_validators_count guaranteed greater than zero.
            shares[idx] = (
                shares[idx] * total_reward_shares // total_active_validators_count
            )

        return recipients, shares, penalized

    def is_operator_penalized(self, node_operator_id: int) -> bool:
        return self._is_operator_penalized(node_operator_id)

    def _is_operator_penalized(self, node_operator_id: int) -> bool:
        node_operator = self._node_operators[node_operator_id]

        return (
            node_operator.refunded_validators_count
            < node_operator.stuck_validators_count
            or int(time()) <= node_operator.stuck_penalty_end_timestamp
        )

    def is_operator_penalty_cleared(self, node_operator_id: int) -> bool:
        node_operator = self._node_operators[node_operator_id]
        return (
            not self._is_operator_penalized(node_operator_id)
            and node_operator.stuck_penalty_end_timestamp == 0
        )

    def _increase_validators_keys_nonce(self) -> None:
        self._nonce += 1

    def _get_signing_keys_allocation_data(
        self, keys_count: int
    ) -> tuple[int, list[int], list[int]]:
        active_node_operators_count: int = self.get_active_node_operators_count()
        node_operator_ids: list[int] = [None] * active_node_operators_count
        active_key_counts_after_allocation: list[int] = [
            None
        ] * active_node_operators_count
        active_keys_capacities: list[int] = [None] * active_node_operators_count

        active_node_operator_index: int = 0
        node_operators_count: int = self.get_node_operators_count()

        for node_operator_id in range(node_operators_count):
            node_operator = self._node_operators[node_operator_id]

            # the node operator has no available signing keys
            if (
                node_operator.deposited_signing_keys_count
                == node_operator.max_validators_count
            ):
                continue

            node_operator_ids[active_node_operator_index] = node_operator_id
            active_key_counts_after_allocation[active_node_operator_index] = (
                node_operator.deposited_signing_keys_count
                - node_operator.exited_signing_keys_count
            )
            active_keys_capacities[active_node_operator_index] = (
                node_operator.max_validators_count
                - node_operator.exited_signing_keys_count
            )
            active_node_operator_index += 1

        if active_node_operator_index == 0:
            return 0, [], []

        # shrink the length of the resulting arrays if some active node operators have no available keys to be deposited
        if active_node_operator_index < active_node_operators_count:
            node_operator_ids = node_operator_ids[:active_node_operator_index]
            active_key_counts_after_allocation = active_key_counts_after_allocation[
                :active_node_operator_index
            ]
            active_keys_capacities = active_keys_capacities[:active_node_operator_index]

        allocated_keys_count = MinFirstAllocationStrategy.allocate(
            active_key_counts_after_allocation, active_keys_capacities, keys_count
        )

        # method NEVER allocates more keys than was requested
        assert keys_count >= allocated_keys_count

        return (
            allocated_keys_count,
            node_operator_ids,
            active_key_counts_after_allocation,
        )

    def _load_allocated_signing_keys(
        self,
        keys_count_to_load: int,
        node_operator_ids: list[int],
        active_key_counts_after_allocation: list[int],
    ) -> tuple[list[str], list[str]]:
        pubkeys: list[str] = [None] * keys_count_to_load
        signatures: list[str] = [None] * keys_count_to_load
        loaded_keys_count = 0

        for i in range(len(node_operator_ids)):
            node_operator = self._node_operators[node_operator_ids[i]]
            deposited_signing_keys_count_before = (
                node_operator.deposited_signing_keys_count
            )
            deposited_signing_keys_count_after = (
                node_operator.exited_signing_keys_count
                + active_key_counts_after_allocation[i]
            )

            if (
                deposited_signing_keys_count_after
                == deposited_signing_keys_count_before
            ):
                continue

            assert (
                deposited_signing_keys_count_after > deposited_signing_keys_count_before
            )

            deposit_data = self._signing_keys_mapping[node_operator_ids[i]][
                deposited_signing_keys_count_before:deposited_signing_keys_count_after
            ]

            for j in range(len(deposit_data)):
                pubkeys[loaded_keys_count + j] = deposit_data[j][0]
                signatures[loaded_keys_count + j] = deposit_data[j][1]

            loaded_keys_count += len(deposit_data)

            node_operator.deposited_signing_keys_count = (
                deposited_signing_keys_count_after
            )
            self._update_summary_max_validators_count(node_operator_ids[i])

        assert loaded_keys_count == keys_count_to_load
        self._node_operator_summary.deposited_keys_count += loaded_keys_count

        return pubkeys, signatures

    def _update_exited_validators_count(
        self, node_operator_id: int, exited_validators_count: int, allow_decrease: bool
    ) -> None:
        node_operator = self._node_operators[node_operator_id]
        cur_exited_validators_count = node_operator.exited_signing_keys_count
        if exited_validators_count == cur_exited_validators_count:
            return

        assert allow_decrease or exited_validators_count > cur_exited_validators_count

        deposited_validators_count = node_operator.deposited_signing_keys_count
        stuck_validators_count = node_operator.stuck_validators_count

        # sustain invariant exited + stuck <= deposited
        assert deposited_validators_count >= stuck_validators_count
        assert (
            exited_validators_count
            <= deposited_validators_count - stuck_validators_count
        )

        node_operator.exited_signing_keys_count = exited_validators_count

        self._node_operator_summary.exited_keys_count += (
            exited_validators_count - cur_exited_validators_count
        )
        self._update_summary_max_validators_count(node_operator_id)

    def _update_stuck_validators_count(
        self, node_operator_id: int, stuck_validators_count: int
    ) -> None:
        node_operator = self._node_operators[node_operator_id]
        cur_stuck_validators_count = node_operator.exited_signing_keys_count
        if stuck_validators_count == cur_stuck_validators_count:
            return

        deposited_validators_count = node_operator.deposited_signing_keys_count
        exited_validators_count = node_operator.exited_signing_keys_count

        # sustain invariant exited + stuck <= deposited
        assert deposited_validators_count >= exited_validators_count
        assert (
            stuck_validators_count
            <= deposited_validators_count - exited_validators_count
        )

        cur_refunded_validators_count = node_operator.refunded_validators_count
        if (
            stuck_validators_count <= cur_refunded_validators_count
            and cur_stuck_validators_count > cur_refunded_validators_count
        ):
            node_operator.stuck_penalty_end_timestamp = (
                int(time()) + self.get_stuck_penalty_delay()
            )

        node_operator.stuck_validators_count = stuck_validators_count
        self._update_summary_max_validators_count(node_operator_id)

    def _update_refund_validators_keys_count(
        self, node_operator_id: int, refunded_validators_count: int
    ) -> None:
        node_operator = self._node_operators[node_operator_id]
        cur_refunded_validators_count = node_operator.refunded_validators_count
        if refunded_validators_count == cur_refunded_validators_count:
            return

        assert refunded_validators_count <= node_operator.deposited_signing_keys_count

        cur_stuck_validators_count = node_operator.stuck_validators_count
        if (
            refunded_validators_count >= cur_stuck_validators_count
            and cur_refunded_validators_count < cur_stuck_validators_count
        ):
            node_operator.stuck_penalty_end_timestamp = (
                int(time()) + self.get_stuck_penalty_delay()
            )

        node_operator.refunded_validators_count = refunded_validators_count
        self._update_summary_max_validators_count(node_operator_id)

    def _update_summary_max_validators_count(self, node_operator_id: int) -> None:
        (
            old_max_signing_keys_count,
            new_max_signing_keys_count,
        ) = self._apply_node_operator_limits(node_operator_id)

        if new_max_signing_keys_count == old_max_signing_keys_count:
            return

        self._node_operator_summary.max_validators_count += (
            new_max_signing_keys_count - old_max_signing_keys_count
        )

    def _apply_node_operator_limits(self, node_operator_id: int) -> tuple[int, int]:
        node_operator = self._node_operators[node_operator_id]

        deposited_signing_keys_count = node_operator.deposited_signing_keys_count

        # It's expected that validators don't suffer from penalties most of the time,
        # so optimistically, set the count of max validators equal to the vetted validators count.
        new_max_signing_keys_count = node_operator.vetted_signing_keys_count

        if not self.is_operator_penalty_cleared(node_operator_id):
            # when the node operator is penalized zeroing its depositable validators count
            new_max_signing_keys_count = deposited_signing_keys_count
        elif node_operator.is_target_limit_active:
            # apply target limit when it's active and the node operator is not penalized
            new_max_signing_keys_count = max(
                # max validators count can't be less than the deposited validators count
                # even when the target limit is less than the current active validators count
                deposited_signing_keys_count,
                min(
                    # max validators count can't be greater than the vetted validators count
                    new_max_signing_keys_count,
                    # SafeMath.add() isn't used below because the sum is always
                    # less or equal to 2 * UINT64_MAX
                    node_operator.exited_signing_keys_count
                    + node_operator.target_validators_count,
                ),
            )

        old_max_signing_keys_count = node_operator.max_validators_count
        if old_max_signing_keys_count != new_max_signing_keys_count:
            node_operator.max_validators_count = new_max_signing_keys_count

        return old_max_signing_keys_count, new_max_signing_keys_count

    def get_stuck_penalty_delay(self):
        return self._stuck_penalty_delay
