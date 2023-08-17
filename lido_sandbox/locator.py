class Locator:
    def __init__(self):
        from lido_sandbox.accounting_oracle import AccountingOracle
        from lido_sandbox.burner import Burner
        from lido_sandbox.el_rewards_vault import ElRewardsVault
        from lido_sandbox.lido import Lido
        from lido_sandbox.oracle_report_sanity_checker import OracleReportSanityChecker
        from lido_sandbox.post_token_rebase_receiver import PostTokenRebaseReceiver
        from lido_sandbox.staking_router import StakingRouter
        from lido_sandbox.treasury import Treasury
        from lido_sandbox.withdrawal_queue import WithdrawalQueue
        from lido_sandbox.withdrawal_vault import WithdrawalVault

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
