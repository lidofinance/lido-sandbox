class StakingRewardsDistribution:
    def __init__(
        self,
        recipients: list[str],
        module_ids: list[int],
        modules_fees: list[int],
        total_fee: int,
        precision_points: int,
    ):
        self.recipients = recipients
        self.module_ids = module_ids
        self.modules_fees = modules_fees
        self.total_fee = total_fee
        self.precision_points = precision_points
