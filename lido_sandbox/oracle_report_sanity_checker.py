from lido_sandbox.libs import PositiveTokenRebaseLimiter
from lido_sandbox.objects import LimitsListPacked
from lido_sandbox.contract import Contract


class OracleReportSanityChecker(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)

    _limits = LimitsListPacked(
        churn_validators_per_day_limit=20000,
        one_off_cl_balance_decrease_bp_limit=500,
        annual_balance_increase_bp_limit=1000,
        simulated_share_rate_deviation_bp_limit=50,
        max_validator_exit_requests_per_report=600,
        max_accounting_extra_data_list_items_count=2,
        max_node_operators_per_extra_data_item_count=100,
        request_timestamp_margin=7680,
        max_positive_token_rebase=750000,
    )

    def check_simulated_share_rate(self, *args):
        pass

    def check_accounting_oracle_report(self, *args):
        pass

    def get_max_positive_token_rebase(self):
        return self._limits.max_positive_token_rebase

    def smoothen_token_rebase(
        self,
        pre_total_pooled_ether: int,
        pre_total_shares: int,
        pre_cl_balance: int,
        post_cl_balance: int,
        withdrawal_vault_balance: int,
        el_rewards_vault_balance: int,
        shares_requested_to_burn: int,
        ether_to_lock_for_withdrawals: int,
        new_shares_to_burn_for_withdrawals: int,
    ) -> tuple[int, int, int, int]:
        token_rebase_limiter = PositiveTokenRebaseLimiter.init_limiter_state(
            self.get_max_positive_token_rebase(),
            pre_total_pooled_ether,
            pre_total_shares,
        )

        if post_cl_balance < pre_cl_balance:
            PositiveTokenRebaseLimiter.decrease_ether(
                token_rebase_limiter, pre_cl_balance - post_cl_balance
            )
        else:
            PositiveTokenRebaseLimiter.increase_ether(
                token_rebase_limiter, post_cl_balance - pre_cl_balance
            )

        withdrawals = PositiveTokenRebaseLimiter.increase_ether(
            token_rebase_limiter, withdrawal_vault_balance
        )
        el_rewards = PositiveTokenRebaseLimiter.increase_ether(
            token_rebase_limiter, el_rewards_vault_balance
        )

        simulated_shares_to_burn = min(
            PositiveTokenRebaseLimiter.get_shares_to_burn_limit(token_rebase_limiter),
            shares_requested_to_burn,
        )

        PositiveTokenRebaseLimiter.decrease_ether(
            token_rebase_limiter, ether_to_lock_for_withdrawals
        )

        shares_to_burn = min(
            PositiveTokenRebaseLimiter.get_shares_to_burn_limit(token_rebase_limiter),
            new_shares_to_burn_for_withdrawals + shares_requested_to_burn,
        )

        return withdrawals, el_rewards, simulated_shares_to_burn, shares_to_burn

    def check_withdrawal_queue_oracle_report(self, *args):
        pass
