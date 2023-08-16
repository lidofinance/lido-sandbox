from min_first_allocation_strategy import MinFirstAllocationStrategy
from locator import Locator
from staking_module import StakingModule
from objects.staking_module import (
    StakingModuleData,
    StakingModuleStatus,
    StakingModuleCache,
)


class StakingRouter:
    _locator: Locator

    _withdrawal_credentials: str = "withdrawal_credentials"
    _staking_module_indices_mapping: dict[int, int]
    _staking_modules_mapping: dict[int, StakingModuleData]
    _staking_modules: dict[str, StakingModule]
    _last_staking_module_id: int = 0
    _staking_modules_count: int = 0

    FEE_PRECISION_POINTS: int = 10**20
    TOTAL_BASIS_POINTS: int = 10000
    DEPOSIT_SIZE: int = 32 * 10**18
    MAX_STAKING_MODULES_COUNT: int = 32

    def __init__(self, locator: Locator):
        self._withdrawal_credentials = "lido_withdrawal_credentials"
        self._locator = locator
        self._staking_module_indices_mapping = {}
        self._staking_modules_mapping = {}
        self._staking_modules = {}

    def add_staking_module(
        self,
        name: str,
        staking_module_address: str,
        target_share: int,
        staking_module_fee: int,
        treasury_fee: int,
    ) -> tuple[int, int]:
        assert target_share <= self.TOTAL_BASIS_POINTS
        assert staking_module_fee + treasury_fee <= self.TOTAL_BASIS_POINTS
        assert len(name) != 0

        new_staking_module_index = self.get_staking_modules_count()
        assert new_staking_module_index < self.MAX_STAKING_MODULES_COUNT

        for i in range(new_staking_module_index):
            assert (
                staking_module_address
                != self._get_staking_module_by_index(i).staking_module_address
            )

        new_staking_module = StakingModuleData(
            self._last_staking_module_id + 1,
            staking_module_address,
            staking_module_fee,
            treasury_fee,
            target_share,
            StakingModuleStatus.Active,
            name,
            0,
        )

        self._staking_modules_mapping[new_staking_module_index] = new_staking_module
        self._set_staking_module_index_by_id(
            new_staking_module.id, new_staking_module_index
        )
        self._last_staking_module_id = new_staking_module.id
        self._staking_modules_count = new_staking_module_index + 1
        self._staking_modules[staking_module_address] = StakingModule('some_type', self._locator, staking_module_address)

        return new_staking_module.id, new_staking_module_index

    def update_staking_module(
        self,
        staking_module_id: int,
        target_share: int,
        staking_module_fee: int,
        treasury_fee: int,
    ) -> None:
        assert target_share <= self.TOTAL_BASIS_POINTS
        assert staking_module_fee + treasury_fee <= self.TOTAL_BASIS_POINTS

        staking_module = self._get_staking_module_by_id(staking_module_id)
        staking_module.target_share = target_share
        staking_module.treasury_fee = treasury_fee
        staking_module.staking_module_fee = staking_module_fee

    def update_target_validators_limits(
        self,
        staking_module_id: int,
        node_operator_id: int,
        is_target_limit_active: bool,
        target_limit: int,
    ) -> None:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)
        module.update_target_validators_limits(
            node_operator_id, is_target_limit_active, target_limit
        )

    def update_refunded_validators_count(
        self,
        staking_module_id: int,
        node_operator_id: int,
        refunded_validators_count: int,
    ) -> None:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)
        module.update_refunded_validators_count(
            node_operator_id, refunded_validators_count
        )

    def report_rewards_minted(
        self, staking_module_ids: list[int], total_shares: list[int]
    ) -> None:
        assert len(staking_module_ids) == len(total_shares)

        for i in range(len(staking_module_ids)):
            if total_shares[i] > 0:
                module_data = self._get_staking_module_by_id(staking_module_ids[i])
                module = self.get_staking_module_instance(
                    module_data.staking_module_address
                )
                module.on_rewards_minted(total_shares[i])

    def update_exited_validators_count_by_staking_module(
        self, staking_module_ids: list[int], exited_validators_counts: list[int]
    ) -> int:
        assert len(staking_module_ids) == len(exited_validators_counts)

        newly_exited_validators_count: int = 0

        for i in range(len(staking_module_ids)):
            module_data = self._get_staking_module_by_id(staking_module_ids[i])

            prev_reported_exited_validators_count = module_data.exited_validators_count
            assert exited_validators_counts[i] >= prev_reported_exited_validators_count

            module = self.get_staking_module_instance(
                module_data.staking_module_address
            )
            _, total_deposited_validators = module.get_staking_module_summary()

            assert exited_validators_counts[i] <= total_deposited_validators

            newly_exited_validators_count += (
                exited_validators_counts[i] - prev_reported_exited_validators_count
            )
            module_data.exited_validators_count = exited_validators_counts[i]

        return newly_exited_validators_count

    def report_staking_module_exited_validators_count_by_node_operator(
        self,
        staking_module_id: int,
        node_operator_ids: list[int],
        exited_validators_counts: list[int],
    ) -> None:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)
        module.update_exited_validators_count(
            node_operator_ids, exited_validators_counts
        )

    def on_validators_counts_by_node_operator_reporting_finished(self) -> None:
        staking_modules_count: int = self.get_staking_modules_count()

        for module_index in range(staking_modules_count):
            module_data = self._get_staking_module_by_index(module_index)
            module = self.get_staking_module_instance(
                module_data.staking_module_address
            )

            exited_validators_count, _, _ = module.get_staking_module_summary()
            if exited_validators_count == module_data.exited_validators_count:
                module.on_exited_and_stuck_validators_counts_updated()

    def get_staking_modules(self) -> list[StakingModuleData]:
        staking_modules_count: int = self.get_staking_modules_count()
        staking_modules: list[StakingModuleData] = [None] * staking_modules_count

        for i in range(staking_modules_count):
            staking_modules[i] = self._get_staking_module_by_index(i)
        return staking_modules

    def get_staking_module_ids(self) -> list[int]:
        staking_modules_count: int = self.get_staking_modules_count()
        staking_module_ids: list[int] = [None] * staking_modules_count

        for i in range(staking_modules_count):
            staking_module_ids[i] = self._get_staking_module_by_index(i).id
        return staking_module_ids

    def get_staking_module(self, staking_module_id: int) -> StakingModule:
        return self._get_staking_module_by_id(staking_module_id)

    def get_staking_modules_count(self) -> int:
        return self._staking_modules_count

    def has_staking_module(self, staking_module_id: int) -> bool:
        return self._staking_module_indices_mapping[staking_module_id] != 0

    def get_staking_module_status(self, staking_module_id: int) -> StakingModuleStatus:
        return self._get_staking_module_by_id(staking_module_id).status

    def get_node_operator_digests(
        self, staking_module_id: int, offset: int, limit: int
    ) -> list[tuple[int, bool, str]]:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)
        node_operator_ids = module.get_node_operator_ids(offset, limit)
        digests = []
        for node_operator_id in node_operator_ids:
            is_active = module.get_node_operator_is_active(node_operator_id)
            summary = self.get_node_operator_summary(
                staking_module_id, node_operator_id
            )
            digests.append((node_operator_id, is_active, summary))
        return digests

    def set_staking_module_status(
        self, staking_module_id: int, status: StakingModuleStatus
    ) -> None:
        staking_module = self._get_staking_module_by_id(staking_module_id)
        assert staking_module.status != status
        self._set_staking_module_status(staking_module, status)

    def pause_staking_module(self, staking_module_id: int) -> None:
        staking_module = self._get_staking_module_by_id(staking_module_id)
        assert staking_module.status == StakingModuleStatus.Active
        self._set_staking_module_status(
            staking_module, StakingModuleStatus.DepositsPaused
        )

    def resume_staking_module(self, staking_module_id: int) -> None:
        staking_module = self._get_staking_module_by_id(staking_module_id)
        assert staking_module.status == StakingModuleStatus.DepositsPaused
        self._set_staking_module_status(staking_module, StakingModuleStatus.Active)

    def get_staking_module_is_stopped(self, staking_module_id: int) -> bool:
        return (
            self.get_staking_module_status(staking_module_id)
            == StakingModuleStatus.Stopped
        )

    def get_staking_module_is_deposits_paused(self, staking_module_id: int) -> bool:
        return (
            self.get_staking_module_status(staking_module_id)
            == StakingModuleStatus.DepositsPaused
        )

    def get_staking_module_is_active(self, staking_module_id: int) -> bool:
        return (
            self.get_staking_module_status(staking_module_id)
            == StakingModuleStatus.Active
        )

    def get_staking_module_nonce(self, staking_module_id: int) -> int:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)
        return module.get_nonce()

    def get_staking_module_active_validators_count(self, staking_module_id: int) -> int:
        module_data = self._get_staking_module_by_id(staking_module_id)
        module = self.get_staking_module_instance(module_data.staking_module_address)

        (
            total_exited_validators,
            total_deposited_validators,
            _,
        ) = module.get_staking_module_summary()
        active_validators_count = total_deposited_validators - max(
            module_data.exited_validators_count, total_exited_validators
        )
        return active_validators_count

    def get_staking_module_max_deposits_count(
        self, staking_module_id: int, max_deposits_value: int
    ) -> int:
        (
            _,
            new_deposits_allocation,
            staking_modules_cache,
        ) = self._get_deposits_allocation(max_deposits_value // self.DEPOSIT_SIZE)
        staking_module_index = self._get_staking_module_index_by_id(staking_module_id)
        return (
            new_deposits_allocation[staking_module_index]
            - staking_modules_cache[staking_module_index].active_validators_count
        )

    def get_staking_fee_aggregate_distribution(self) -> tuple[int, int, int]:
        module_fees = []
        (
            _,
            _,
            module_fees,
            total_fee,
            base_precision,
        ) = self.get_staking_rewards_distribution()

        modules_fee = sum(module_fees)
        treasury_fee = total_fee - modules_fee
        return modules_fee, treasury_fee, base_precision

    def get_staking_rewards_distribution(
        self,
    ) -> tuple[list[str], list[int], list[int], int, int]:
        recipients: list[str] = []
        staking_module_ids: list[int] = []
        staking_module_fees: list[int] = []
        total_fee: int = 0
        precision_points: int = 0

        (
            total_active_validators,
            staking_modules_cache,
        ) = self._load_staking_modules_cache()
        staking_modules_count = len(staking_modules_cache)

        if staking_modules_count == 0 or total_active_validators == 0:
            return [], [], [], 0, self.FEE_PRECISION_POINTS

        precision_points = self.FEE_PRECISION_POINTS

        for i in range(staking_modules_count):
            if staking_modules_cache[i].active_validators_count > 0:
                staking_module_ids.append(staking_modules_cache[i].staking_module_id)
                staking_module_validators_share = (
                    staking_modules_cache[i].active_validators_count * precision_points
                ) // total_active_validators

                recipients.append(str(staking_modules_cache[i].staking_module_address))
                staking_module_fee = (
                    staking_module_validators_share
                    * staking_modules_cache[i].staking_module_fee
                ) // self.TOTAL_BASIS_POINTS

                if staking_modules_cache[i].status != StakingModuleStatus.Stopped:
                    staking_module_fees.append(staking_module_fee)

                total_fee += (
                    staking_module_validators_share
                    * staking_modules_cache[i].treasury_fee
                ) // self.TOTAL_BASIS_POINTS + staking_module_fee

        assert total_fee <= precision_points

        if len(staking_module_ids) < staking_modules_count:
            staking_module_ids = staking_module_ids[: len(staking_module_ids)]
            recipients = recipients[: len(staking_module_ids)]
            staking_module_fees = staking_module_fees[: len(staking_module_ids)]

        return (
            recipients,
            staking_module_ids,
            staking_module_fees,
            total_fee,
            precision_points,
        )

    def get_total_fee_e4_precision(self) -> int:
        (
            _,
            _,
            _,
            total_fee_in_high_precision,
            precision,
        ) = self.get_staking_rewards_distribution()
        return self._to_e4_precision(total_fee_in_high_precision, precision)

    def get_staking_fee_aggregate_distribution_e4_precision(self) -> tuple[int, int]:
        (
            modules_fee_high_precision,
            treasury_fee_high_precision,
            precision,
        ) = self.get_staking_fee_aggregate_distribution()
        modules_fee = self._to_e4_precision(modules_fee_high_precision, precision)
        treasury_fee = self._to_e4_precision(treasury_fee_high_precision, precision)
        return modules_fee, treasury_fee

    def get_deposits_allocation(self, deposits_count: int) -> tuple[int, list[int]]:
        allocated, allocations, _ = self._get_deposits_allocation(deposits_count)
        return allocated, allocations

    def get_withdrawal_credentials(self) -> str:
        return self._withdrawal_credentials

    def deposit(self, deposit_value: int, deposits_count: int, staking_module_id: int) -> None:
        module_data = self._get_staking_module_by_id(staking_module_id)
        assert module_data.status == StakingModuleStatus.Active
        assert deposit_value == deposits_count * self.DEPOSIT_SIZE

        if deposits_count > 0:
            module = self.get_staking_module_instance(module_data.staking_module_address)
            module.obtain_deposit_data(deposits_count)

    def _load_staking_modules_cache(self) -> tuple[int, list[StakingModuleCache]]:
        total_active_validators = 0
        staking_modules_count = self.get_staking_modules_count()
        staking_modules_cache = [
            self._load_staking_modules_cache_item(module_index)
            for module_index in range(staking_modules_count)
        ]
        for cache_item in staking_modules_cache:
            total_active_validators += cache_item.active_validators_count
        return total_active_validators, staking_modules_cache

    def _load_staking_modules_cache_item(
        self, staking_module_index: int
    ) -> StakingModuleCache:
        module_data = self._get_staking_module_by_index(staking_module_index)
        module = self.get_staking_module_instance(module_data.staking_module_address)

        cache_item = StakingModuleCache(
            staking_module_address=module_data.staking_module_address,
            staking_module_id=module_data.id,
            staking_module_fee=module_data.staking_module_fee,
            treasury_fee=module_data.treasury_fee,
            target_share=module_data.target_share,
            status=module_data.status,
            available_validators_count=0,
            active_validators_count=0,
        )

        (
            total_exited_validators,
            total_deposited_validators,
            depositable_validators_count,
        ) = module.get_staking_module_summary()

        cache_item.available_validators_count = (
            depositable_validators_count
            if cache_item.status == StakingModuleStatus.Active
            else 0
        )
        cache_item.active_validators_count = total_deposited_validators - max(
            total_exited_validators, module_data.exited_validators_count
        )

        return cache_item

    def get_staking_module_instance(self, address: str) -> StakingModule:
        return self._staking_modules[address]

    def _set_staking_module_status(
        self, staking_module: StakingModule, status: StakingModuleStatus
    ) -> None:
        prev_status = staking_module.status
        if prev_status != status:
            staking_module.status = status

    def _get_deposits_allocation(
        self, deposits_to_allocate: int
    ) -> tuple[int, list[int], list[StakingModuleCache]]:
        (
            total_active_validators,
            staking_modules_cache,
        ) = self._load_staking_modules_cache()

        staking_modules_count = len(staking_modules_cache)
        allocations = [0] * staking_modules_count

        if staking_modules_count > 0:
            total_active_validators += deposits_to_allocate
            capacities = [0] * staking_modules_count
            target_validators = 0

            for i in range(staking_modules_count):
                allocations[i] = staking_modules_cache[i].active_validators_count
                target_validators = (
                    staking_modules_cache[i].target_share * total_active_validators
                ) // self.TOTAL_BASIS_POINTS
                capacities[i] = min(
                    target_validators,
                    staking_modules_cache[i].active_validators_count
                    + staking_modules_cache[i].available_validators_count,
                )

            allocated = MinFirstAllocationStrategy.allocate(
                allocations, capacities, deposits_to_allocate
            )
        else:
            allocated = 0

        return allocated, allocations, staking_modules_cache

    def _get_staking_module_index_by_id(self, staking_module_id: int) -> int:
        index_one_based = self._staking_module_indices_mapping[staking_module_id]
        assert index_one_based != 0
        return index_one_based - 1

    def _set_staking_module_index_by_id(
        self, staking_module_id: int, staking_module_index: int
    ) -> None:
        self._staking_module_indices_mapping[staking_module_id] = staking_module_index + 1

    def _get_staking_module_by_id(self, staking_module_id: int) -> StakingModuleData:
        return self._get_staking_module_by_index(
            self._get_staking_module_index_by_id(staking_module_id)
        )

    def _get_staking_module_by_index(
        self, staking_module_index: int
    ) -> StakingModuleData:
        return self._staking_modules_mapping[staking_module_index]

    def _get_staking_module_address_by_id(self, staking_module_id: int) -> str:
        return self._get_staking_module_by_id(staking_module_id).staking_module_address

    def _to_e4_precision(self, value: int, precision: int) -> int:
        return (value * self.TOTAL_BASIS_POINTS) // precision
