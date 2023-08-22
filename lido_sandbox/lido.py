from lido_sandbox.steth import StETH
from lido_sandbox.staking_router import StakingRouter
from lido_sandbox.locator import Locator
from lido_sandbox.objects import (
    OracleReportContext,
    OracleReportedData,
    StakingRewardsDistribution,
)
from lido_sandbox.post_token_rebase_receiver import PostTokenRebaseReceiver


class Lido(StETH):
    balance: int = 0

    _buffered_ether: int = 0
    _total_shares: int = 0
    _cl_balance: int = 0
    _cl_validators: int = 0
    _deposited_validators: int = 0
    _total_el_rewards_collected: int = 0
    _last_report_timestamp: int = 0
    _locator: Locator

    DEPOSIT_SIZE: int = 32 * 10**18

    def __init__(self, locator: Locator, address: str):
        super().__init__(address)
        self._locator = locator

    def get_buffered_ether(self) -> int:
        return self._get_buffered_ether()

    def initialize(self):
        self._bootstrap_initial_holder()
        self._initialize_v2()

    def _initialize_v2(self):
        withdrawal_queue = self._locator.withdrawal_queue
        burner = self._locator.burner

        self._approve(withdrawal_queue.address, burner.address, self.INFINITE_ALLOWANCE)

    def submit(self, sender: str, value: int):
        return self._submit(sender, value)

    def receive_el_rewards(self, msg_value: int):
        self._total_el_rewards_collected = self._total_el_rewards_collected + msg_value

    def receive_withdrawals(self):
        pass

    def handle_oracle_report(
        self,
        report_timestamp: int,
        time_elapsed: int,
        cl_validators: int,
        cl_balance: int,
        withdrawal_vault_balance: int,
        el_rewards_vault_balance: int,
        shares_requested_to_burn: int,
        withdrawal_finalization_batches: list[int],
        simulated_share_rate: int,
    ) -> tuple[int, int, int, int]:
        return self._handle_oracle_report(
            OracleReportedData(
                report_timestamp,
                time_elapsed,
                cl_validators,
                cl_balance,
                withdrawal_vault_balance,
                el_rewards_vault_balance,
                shares_requested_to_burn,
                withdrawal_finalization_batches,
                simulated_share_rate,
            )
        )

    def get_total_el_rewards_collected(self) -> int:
        return self._total_el_rewards_collected

    def get_beacon_stat(self) -> tuple[int, int, int]:
        return self._deposited_validators, self._cl_validators, self._cl_balance

    def can_deposit(self) -> bool:
        withdrawal_queue = self._locator.withdrawal_queue
        return not withdrawal_queue.is_bunker_mode_active()

    def get_depositable_ether(self) -> int:
        withdrawal_queue = self._locator.withdrawal_queue
        buffered_ether = self._get_buffered_ether()
        withdrawal_reserve = withdrawal_queue.unfinalized_steth()
        return (
            buffered_ether - withdrawal_reserve
            if buffered_ether > withdrawal_reserve
            else 0
        )

    def deposit(self, max_deposits_count: int, staking_module_id: int) -> None:
        assert self.can_deposit(), "CAN_NOT_DEPOSIT"

        staking_router = self._locator.staking_router
        deposits_count = min(
            max_deposits_count,
            staking_router.get_staking_module_max_deposits_count(
                staking_module_id, self.get_depositable_ether()
            ),
        )

        deposits_value = 0
        if deposits_count > 0:
            deposits_value = deposits_count * self.DEPOSIT_SIZE
            self._buffered_ether = self._get_buffered_ether() - deposits_value

            new_deposited_validators = self._deposited_validators + deposits_count
            self._deposited_validators = new_deposited_validators

        staking_router.deposit(deposits_value, deposits_count, staking_module_id)

    def get_fee_distribution(self) -> tuple[int, int, int]:
        staking_router = self._locator.staking_router
        total_basis_points: int = staking_router.total_basis_points()
        total_fee: int = staking_router.get_total_fee_e4_precision()
        (
            treasury_fee_basis_points_abs,
            operators_fee_basis_points_abs,
        ) = staking_router.get_staking_fee_aggregate_distribution_e4_precision()

        insurance_fee_basis_points: int = 0  # explicitly set to zero
        treasury_fee_basis_points: int = (
            treasury_fee_basis_points_abs * total_basis_points
        ) // total_fee
        operators_fee_basis_points: int = (
            operators_fee_basis_points_abs * total_basis_points
        ) // total_fee

        return (
            treasury_fee_basis_points,
            insurance_fee_basis_points,
            operators_fee_basis_points,
        )

    def _process_cl_state_update(
        self,
        report_timestamp: int,
        pre_cl_validators: int,
        post_cl_validators: int,
        post_cl_balance: int,
    ) -> int:
        self._last_report_timestamp = report_timestamp

        deposited_validators: int = self._deposited_validators
        assert post_cl_validators <= deposited_validators, "REPORTED_MORE_DEPOSITED"
        assert post_cl_validators >= pre_cl_validators, "REPORTED_LESS_VALIDATORS"

        if post_cl_validators > pre_cl_validators:
            self._cl_validators = post_cl_validators

        appeared_validators: int = post_cl_validators - pre_cl_validators
        pre_cl_balance = self._cl_balance

        pre_cl_balance = pre_cl_balance + appeared_validators * self.DEPOSIT_SIZE
        self._cl_balance = post_cl_balance

        return pre_cl_balance

    def _collect_rewards_and_process_withdrawals(
        self,
        withdrawals_to_withdraw: int,
        el_rewards_to_withdraw: int,
        withdrawal_finalization_batches: list[int],
        simulated_share_rate: int,
        ether_to_lock_on_withdrawal_queue: int,
    ) -> None:
        el_rewards_vault = self._locator.el_rewards_vault
        withdrawal_vault = self._locator.withdrawal_vault

        if el_rewards_to_withdraw > 0:
            el_rewards_vault.withdraw_rewards(el_rewards_to_withdraw)

        if withdrawals_to_withdraw > 0:
            withdrawal_vault.withdraw_withdrawals(withdrawals_to_withdraw)

        if ether_to_lock_on_withdrawal_queue > 0:
            withdrawal_queue = self._locator.withdrawal_queue
            withdrawal_queue.finalize(
                withdrawal_finalization_batches[-1],
                simulated_share_rate,
                value=ether_to_lock_on_withdrawal_queue,
            )

        post_buffered_ether = (
            self._get_buffered_ether()
            + el_rewards_to_withdraw
            + withdrawals_to_withdraw
            - ether_to_lock_on_withdrawal_queue
        )

        self._set_buffered_ether(post_buffered_ether)

    def _calculate_withdrawals(
        self, reported_data: OracleReportedData
    ) -> tuple[int, int]:
        withdrawal_queue = self._locator.withdrawal_queue
        oracle_report_sanity_checker = self._locator.oracle_report_sanity_checker

        if not withdrawal_queue.is_paused():
            oracle_report_sanity_checker.check_withdrawal_queue_oracle_report(
                reported_data.withdrawal_finalization_batches[-1],
                reported_data.report_timestamp,
            )

            ether_to_lock, shares_to_burn = withdrawal_queue.prefinalize(
                reported_data.withdrawal_finalization_batches,
                reported_data.simulated_share_rate,
            )
            return ether_to_lock, shares_to_burn

    def _process_rewards(
        self,
        report_context: OracleReportContext,
        post_cl_balance: int,
        withdrawn_withdrawals: int,
        withdrawn_el_rewards: int,
    ):
        post_cl_total_balance = post_cl_balance + withdrawn_withdrawals

        if post_cl_total_balance > report_context.pre_cl_balance:
            consensus_layer_rewards = (
                post_cl_total_balance - report_context.pre_cl_balance
            )

            shares_minted_as_fees = self._distribute_fee(
                report_context.pre_total_pooled_ether,
                report_context.pre_total_shares,
                consensus_layer_rewards + withdrawn_el_rewards,
            )
            return shares_minted_as_fees

    def _submit(self, sender: str, value: int) -> int:
        assert value > 0

        shares_amount = self.get_shares_by_pooled_eth(value)
        self._mint_shares(sender, shares_amount)
        self._set_buffered_ether(self.get_buffered_ether() + value)

        return shares_amount

    def _get_staking_rewards_distribution(
        self,
    ) -> tuple[StakingRewardsDistribution, StakingRouter]:
        router = self._locator.staking_router

        (
            recipients,
            module_ids,
            modules_fees,
            total_fee,
            precision_points,
        ) = router.get_staking_rewards_distribution()

        assert len(recipients) == len(modules_fees), "WRONG_RECIPIENTS_INPUT"
        assert len(module_ids) == len(modules_fees), "WRONG_MODULE_IDS_INPUT"

        return (
            StakingRewardsDistribution(
                recipients, module_ids, modules_fees, total_fee, precision_points
            ),
            router,
        )

    def _distribute_fee(
        self, pre_total_pooled_ether: int, pre_total_shares: int, total_rewards: int
    ) -> int:
        rewards_distribution, router = self._get_staking_rewards_distribution()
        shares_minted_as_fees = 0

        if rewards_distribution.total_fee > 0:
            total_pooled_ether_with_rewards = pre_total_pooled_ether + total_rewards

            shares_minted_as_fees = (
                total_rewards
                * rewards_distribution.total_fee
                * pre_total_shares
                // (
                    total_pooled_ether_with_rewards
                    * rewards_distribution.precision_points
                    - total_rewards * rewards_distribution.total_fee
                )
            )

            lido = self._locator.lido
            self._mint_shares(lido.address, shares_minted_as_fees)

            module_rewards, total_module_rewards = self._transfer_module_rewards(
                rewards_distribution.recipients,
                rewards_distribution.modules_fees,
                rewards_distribution.total_fee,
                shares_minted_as_fees,
            )

            self._transfer_treasury_rewards(
                shares_minted_as_fees - total_module_rewards
            )

            router.report_rewards_minted(
                rewards_distribution.module_ids, module_rewards
            )

        return shares_minted_as_fees

    def _transfer_module_rewards(
        self,
        recipients: list[str],
        modules_fees: list[int],
        total_fee: int,
        total_rewards: int,
    ) -> tuple[list[int], int]:
        total_module_rewards = 0
        module_rewards = [0] * len(recipients)
        lido = self._locator.lido

        for i in range(len(recipients)):
            if modules_fees[i] > 0:
                i_module_rewards = total_rewards * modules_fees[i] // total_fee
                module_rewards[i] = i_module_rewards
                self._transfer_shares(lido.address, recipients[i], i_module_rewards)
                total_module_rewards += i_module_rewards

        return module_rewards, total_module_rewards

    def _transfer_treasury_rewards(self, treasury_reward: int) -> None:
        lido = self._locator.lido
        treasury = self._locator.treasury
        self._transfer_shares(lido.address, treasury.address, treasury_reward)

    def _get_buffered_ether(self) -> int:
        return self._buffered_ether

    def _set_buffered_ether(self, value: int) -> None:
        self._buffered_ether = value

    def _get_transient_balance(self) -> int:
        assert self._deposited_validators >= self._cl_validators
        return (self._deposited_validators - self._cl_validators) * self.DEPOSIT_SIZE

    def _get_total_pooled_ether(self) -> int:
        return (
            self._get_buffered_ether()
            + self._cl_balance
            + self._get_transient_balance()
        )

    def _handle_oracle_report(
        self, reported_data: OracleReportedData
    ) -> tuple[int, int, int, int]:
        withdrawal_queue = self._locator.withdrawal_queue
        burner = self._locator.burner
        oracle_report_sanity_checker = self._locator.oracle_report_sanity_checker
        post_token_rebase_receiver = self._locator.post_token_rebase_receiver

        report_context = OracleReportContext()

        # Step 1.
        # Take a snapshot of the current (pre-) state
        report_context.pre_total_pooled_ether = self._get_total_pooled_ether()
        report_context.pre_total_shares = self._get_total_shares()
        report_context.pre_cl_validators = self._cl_validators
        report_context.pre_cl_balance = self._process_cl_state_update(
            reported_data.report_timestamp,
            report_context.pre_cl_validators,
            reported_data.cl_validators,
            reported_data.post_cl_balance,
        )

        # Step 2.
        # Pass the report data to sanity checker (reverts if malformed)
        self._check_accounting_oracle_report(reported_data, report_context)

        # Step 3.
        # Pre-calculate the ether to lock for withdrawal queue and shares to be burnt
        # due to withdrawal requests to finalize
        if len(reported_data.withdrawal_finalization_batches) != 0:
            (
                report_context.ether_to_lock_on_withdrawal_queue,
                report_context.shares_to_burn_from_withdrawal_queue,
            ) = self._calculate_withdrawals(reported_data)

            if report_context.shares_to_burn_from_withdrawal_queue > 0:
                burner.request_burn_shares(
                    withdrawal_queue.address,
                    report_context.shares_to_burn_from_withdrawal_queue,
                )

        # Step 4.
        # Pass the accounting values to sanity checker to smoothen positive token rebase
        withdrawals = 0
        el_rewards = 0
        (
            withdrawals,
            el_rewards,
            report_context.simulated_shares_to_burn,
            report_context.shares_to_burn,
        ) = oracle_report_sanity_checker.smoothen_token_rebase(
            report_context.pre_total_pooled_ether,
            report_context.pre_total_shares,
            report_context.pre_cl_balance,
            reported_data.post_cl_balance,
            reported_data.withdrawal_vault_balance,
            reported_data.el_rewards_vault_balance,
            reported_data.shares_requested_to_burn,
            report_context.ether_to_lock_on_withdrawal_queue,
            report_context.shares_to_burn_from_withdrawal_queue,
        )

        # Step 5.
        # Invoke finalization of the withdrawal requests (send ether to withdrawal queue, assign shares to be burnt)
        self._collect_rewards_and_process_withdrawals(
            withdrawals,
            el_rewards,
            reported_data.withdrawal_finalization_batches,
            reported_data.simulated_share_rate,
            report_context.ether_to_lock_on_withdrawal_queue,
        )

        # Step 6.
        # Burn the previously requested shares
        if report_context.shares_to_burn > 0:
            burner.commit_shares_to_burn(report_context.shares_to_burn)
            self._burn_shares(burner.address, report_context.shares_to_burn)

        # Step 7.
        # Distribute protocol fee (treasury & node operators)
        report_context.shares_minted_as_fees = self._process_rewards(
            report_context, reported_data.post_cl_balance, withdrawals, el_rewards
        )

        # Step 8.
        # Complete token rebase by informing observers (emit an event and call the external receivers if any)
        (post_rotal_shares, post_total_pooled_ether) = self._complete_token_rebase(
            reported_data, report_context, post_token_rebase_receiver
        )

        # Step 9. Sanity check for the provided simulated share rate
        if len(reported_data.withdrawal_finalization_batches):
            oracle_report_sanity_checker.check_simulated_share_rate(
                post_total_pooled_ether,
                post_rotal_shares,
                report_context.ether_to_lock_on_withdrawal_queue,
                report_context.shares_to_burn - report_context.simulated_shares_to_burn,
                reported_data.simulated_share_rate,
            )

        return [post_total_pooled_ether, post_rotal_shares, withdrawals, el_rewards]

    def _check_accounting_oracle_report(
        self,
        reported_data: OracleReportedData,
        report_context: OracleReportContext,
    ) -> None:
        oracle_report_sanity_checker = self._locator.oracle_report_sanity_checker

        oracle_report_sanity_checker.check_accounting_oracle_report(
            reported_data.time_elapsed,
            report_context.pre_cl_balance,
            reported_data.post_cl_balance,
            reported_data.withdrawal_vault_balance,
            reported_data.el_rewards_vault_balance,
            reported_data.shares_requested_to_burn,
            report_context.pre_cl_validators,
            reported_data.cl_validators,
        )

    def _complete_token_rebase(
        self,
        reported_data: OracleReportedData,
        report_context: OracleReportContext,
        post_token_rebase_receiver: PostTokenRebaseReceiver,
    ) -> tuple[int, int]:
        post_total_shares = self._get_total_shares()
        post_total_pooled_ether = self._get_total_pooled_ether()

        if post_token_rebase_receiver is not None:
            post_token_rebase_receiver.handle_post_token_rebase(
                reported_data.report_timestamp,
                reported_data.time_elapsed,
                report_context.pre_total_shares,
                report_context.pre_total_pooled_ether,
                post_total_shares,
                post_total_pooled_ether,
                report_context.shares_minted_as_fees,
            )

        return post_total_shares, post_total_pooled_ether

    def _bootstrap_initial_holder(self) -> None:
        balance = self.balance
        assert balance != 0

        if self._get_total_shares() == 0:
            self._set_buffered_ether(balance)
            self._mint_initial_shares(balance)
