from lido_sandbox.objects import TokenRebaseLimiterData


class PositiveTokenRebaseLimiter:
    LIMITER_PRECISION_BASE: int = 10**9
    UNLIMITED_REBASE: int = 2**64 - 1
    MAX_UINT256 = 2**256 - 1

    @staticmethod
    def init_limiter_state(
        rebase_limit: int, pre_total_pooled_ether: int, pre_total_shares: int
    ) -> TokenRebaseLimiterData:
        assert rebase_limit != 0
        assert rebase_limit <= PositiveTokenRebaseLimiter.UNLIMITED_REBASE

        # special case
        if pre_total_pooled_ether == 0:
            rebase_limit = PositiveTokenRebaseLimiter.UNLIMITED_REBASE

        current_total_pooled_ether = pre_total_pooled_ether
        max_total_pooled_ether = (
            PositiveTokenRebaseLimiter.MAX_UINT256
            if rebase_limit == PositiveTokenRebaseLimiter.UNLIMITED_REBASE
            else pre_total_pooled_ether
            + (rebase_limit * pre_total_pooled_ether)
            // PositiveTokenRebaseLimiter.LIMITER_PRECISION_BASE
        )

        return TokenRebaseLimiterData(
            current_total_pooled_ether,
            pre_total_pooled_ether,
            pre_total_shares,
            rebase_limit,
            max_total_pooled_ether,
        )

    @staticmethod
    def is_limit_reached(limiter_state: TokenRebaseLimiterData) -> bool:
        return (
            limiter_state.current_total_pooled_ether
            >= limiter_state.max_total_pooled_ether
        )

    @staticmethod
    def decrease_ether(
        limiter_state: TokenRebaseLimiterData, ether_amount: int
    ) -> None:
        if (
            limiter_state.positive_rebase_limit
            == PositiveTokenRebaseLimiter.UNLIMITED_REBASE
        ):
            return

        if ether_amount > limiter_state.current_total_pooled_ether:
            raise ValueError("NegativeTotalPooledEther")

        limiter_state.current_total_pooled_ether -= ether_amount

    @staticmethod
    def increase_ether(limiter_state: TokenRebaseLimiterData, ether_amount: int) -> int:
        if (
            limiter_state.positive_rebase_limit
            == PositiveTokenRebaseLimiter.UNLIMITED_REBASE
        ):
            return ether_amount

        prev_pooled_ether = limiter_state.current_total_pooled_ether
        limiter_state.current_total_pooled_ether += ether_amount

        limiter_state.current_total_pooled_ether = min(
            limiter_state.current_total_pooled_ether,
            limiter_state.max_total_pooled_ether,
        )

        assert limiter_state.current_total_pooled_ether >= prev_pooled_ether

        return limiter_state.current_total_pooled_ether - prev_pooled_ether

    @staticmethod
    def get_shares_to_burn_limit(limiter_state: TokenRebaseLimiterData) -> int:
        if (
            limiter_state.positive_rebase_limit
            == PositiveTokenRebaseLimiter.UNLIMITED_REBASE
        ):
            return limiter_state.pre_total_shares

        if PositiveTokenRebaseLimiter.is_limit_reached(limiter_state):
            return 0

        rebase_limit_plus_1 = (
            limiter_state.positive_rebase_limit
            + PositiveTokenRebaseLimiter.LIMITER_PRECISION_BASE
        )
        pooled_ether_rate = (
            limiter_state.current_total_pooled_ether
            * PositiveTokenRebaseLimiter.LIMITER_PRECISION_BASE
        ) // limiter_state.pre_total_pooled_ether

        max_shares_to_burn = (
            limiter_state.pre_total_shares * (rebase_limit_plus_1 - pooled_ether_rate)
        ) // rebase_limit_plus_1

        return max_shares_to_burn
