from burner import Burner
from accounting_oracle import AccountingOracle
from el_rewards_vault import ElRewardsVault
from oracle_report_sanity_checker import OracleReportSanityChecker
from staking_router import StakingRouter
from withdrawal_queue import WithdrawalQueue
from withdrawal_vault import WithdrawalVault
from post_token_rebase_receiver import PostTokenRebaseReceiver


class LidoLocator:
    def __init__(self, lido):
        self.accounting_oracle = "accounting_oracle", AccountingOracle()
        self.el_rewards_vault = "el_rewards_vault", ElRewardsVault()
        self.oracle_report_sanity_checker = (
            "oracle_report_sanity_checker",
            OracleReportSanityChecker(),
        )
        self.staking_router = "staking_router", StakingRouter(lido)
        self.burner = "burner", Burner()
        self.withdrawal_queue = "withdrawal_queue", WithdrawalQueue()
        self.withdrawal_vault = "withdrawal_vault", WithdrawalVault()
        self.post_token_rebase_receiver = (
            "post_token_rebase_receiver",
            PostTokenRebaseReceiver(),
        )
