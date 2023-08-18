class NodeOperator:
    def __init__(
        self,
        active: bool,
        reward_address: str,
        name: str,
        # signing keys stats
        exited_signing_keys_count: int = 0,
        deposited_signing_keys_count: int = 0,
        vetted_signing_keys_count: int = 0,
        total_signing_keys_count: int = 0,
        # stuck penalty stats
        stuck_validators_count: int = 0,
        refunded_validators_count: int = 0,
        stuck_penalty_end_timestamp: int = 0,
        # target validators stats
        is_target_limit_active: bool = False,
        target_validators_count: int = 0,
        max_validators_count: int = 0,
    ):
        self.active = active
        self.reward_address = reward_address
        self.name = name
        self.exited_signing_keys_count = exited_signing_keys_count
        self.deposited_signing_keys_count = deposited_signing_keys_count
        self.vetted_signing_keys_count = vetted_signing_keys_count
        self.total_signing_keys_count = total_signing_keys_count
        self.stuck_validators_count = stuck_validators_count
        self.refunded_validators_count = refunded_validators_count
        self.stuck_penalty_end_timestamp = stuck_penalty_end_timestamp
        self.is_target_limit_active = is_target_limit_active
        self.target_validators_count = target_validators_count
        self.max_validators_count = max_validators_count


class NodeOperatorSummary:
    def __init__(
        self,
        max_validators_count: int = 0,
        exited_keys_count: int = 0,
        total_keys_count: int = 0,
        deposited_keys_count: int = 0,
    ):
        self.max_validators_count = max_validators_count
        self.exited_keys_count = exited_keys_count
        self.total_keys_count = total_keys_count
        self.deposited_keys_count = deposited_keys_count
