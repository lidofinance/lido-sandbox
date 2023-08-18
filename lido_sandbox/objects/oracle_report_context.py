class OracleReportContext:
    def __init__(
        self,
        pre_cl_validators: int = 0,
        pre_cl_balance: int = 0,
        pre_total_pooled_ether: int = 0,
        pre_total_shares: int = 0,
        ether_to_lock_on_withdrawal_queue: int = 0,
        shares_to_burn_from_withdrawal_queue: int = 0,
        simulated_shares_to_burn: int = 0,
        shares_to_burn: int = 0,
        shares_minted_as_fees: int = 0,
    ):
        self.pre_cl_validators = pre_cl_validators
        self.pre_cl_balance = pre_cl_balance
        self.pre_total_pooled_ether = pre_total_pooled_ether
        self.pre_total_shares = pre_total_shares
        self.ether_to_lock_on_withdrawal_queue = ether_to_lock_on_withdrawal_queue
        self.shares_to_burn_from_withdrawal_queue = shares_to_burn_from_withdrawal_queue
        self.simulated_shares_to_burn = simulated_shares_to_burn
        self.shares_to_burn = shares_to_burn
        self.shares_minted_as_fees = shares_minted_as_fees
