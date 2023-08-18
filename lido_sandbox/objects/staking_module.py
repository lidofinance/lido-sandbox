from enum import Enum


class StakingModuleStatus(Enum):
    Active = 0
    DepositsPaused = 1
    Stopped = 2


class StakingModuleData:
    def __init__(
        self,
        id: int,
        staking_module_address: str,
        staking_module_fee: int,
        treasury_fee: int,
        target_share: int,
        status: int,
        name: str,
        exited_validators_count: int,
    ):
        self.id = id
        self.staking_module_address = staking_module_address
        self.staking_module_fee = staking_module_fee
        self.treasury_fee = treasury_fee
        self.target_share = target_share
        self.status = status
        self.name = name
        self.exited_validators_count = exited_validators_count


class StakingModuleCache:
    def __init__(
        self,
        staking_module_address: str,
        staking_module_id: int,
        staking_module_fee: int,
        treasury_fee: int,
        target_share: int,
        status: int,
        active_validators_count: int,
        available_validators_count: int,
    ):
        self.staking_module_address = staking_module_address
        self.staking_module_id = staking_module_id
        self.staking_module_fee = staking_module_fee
        self.treasury_fee = treasury_fee
        self.target_share = target_share
        self.status = status
        self.active_validators_count = active_validators_count
        self.available_validators_count = available_validators_count
