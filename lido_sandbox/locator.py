from lido_sandbox.contract import Contract


class Locator(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)

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

        self.accounting_oracle = AccountingOracle(address="accounting_oracle")
        self.burner = Burner(address="burner")
        self.el_rewards_vault = ElRewardsVault(address="el_rewards_vault")
        self.lido = Lido(locator=self, address="lido")
        self.oracle_report_sanity_checker = OracleReportSanityChecker(
            address="oracle_report_sanity_checker"
        )
        self.post_token_rebase_receiver = PostTokenRebaseReceiver(
            address="post_token_rebase_receiver"
        )
        self.staking_router = StakingRouter(locator=self, address="staking_router")
        self.treasury = Treasury(address="treasury")
        self.withdrawal_queue = WithdrawalQueue(address="withdrawal_queue")
        self.withdrawal_vault = WithdrawalVault(address="withdrawal_vault")
