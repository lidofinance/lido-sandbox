class OracleReportedData:
    def __init__(
        self,
        report_timestamp: int,
        time_elapsed: int,
        cl_validators: int,
        post_cl_balance: int,
        withdrawal_vault_balance: int,
        el_rewards_vault_balance: int,
        shares_requested_to_burn: int,
        withdrawal_finalization_batches: list[int],
        simulated_share_rate: int,
    ):
        self.report_timestamp = report_timestamp
        self.time_elapsed = time_elapsed
        self.cl_validators = cl_validators
        self.post_cl_balance = post_cl_balance
        self.withdrawal_vault_balance = withdrawal_vault_balance
        self.el_rewards_vault_balance = el_rewards_vault_balance
        self.shares_requested_to_burn = shares_requested_to_burn
        self.withdrawal_finalization_batches = withdrawal_finalization_batches
        self.simulated_share_rate = simulated_share_rate
