class Locator:
    def __init__(self):
        from accounting_oracle import AccountingOracle
        from burner import Burner
        from el_rewards_vault import ElRewardsVault
        from lido import Lido
        from oracle_report_sanity_checker import OracleReportSanityChecker
        from post_token_rebase_receiver import PostTokenRebaseReceiver
        from staking_router import StakingRouter
        from treasury import Treasury
        from withdrawal_queue import WithdrawalQueue
        from withdrawal_vault import WithdrawalVault

        self.accounting_oracle = "accounting_oracle", AccountingOracle()
        self.burner = "burner", Burner()
        self.el_rewards_vault = "el_rewards_vault", ElRewardsVault()
        self.lido = 'lido', Lido(self)
        self.oracle_report_sanity_checker = (
            "oracle_report_sanity_checker",
            OracleReportSanityChecker(),
        )
        self.post_token_rebase_receiver = (
            "post_token_rebase_receiver",
            PostTokenRebaseReceiver(),
        )
        self.staking_router = "staking_router", StakingRouter(self)
        self.treasury = 'treasury', Treasury()
        self.withdrawal_queue = "withdrawal_queue", WithdrawalQueue()
        self.withdrawal_vault = "withdrawal_vault", WithdrawalVault()
