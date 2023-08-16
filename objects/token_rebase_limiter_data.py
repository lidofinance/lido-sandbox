class TokenRebaseLimiterData:
    def __init__(
        self,
        current_total_pooled_ether: int,
        pre_total_pooled_ether: int,
        pre_total_shares: int,
        positive_rebase_limit: int,
        max_total_pooled_ether: int,
    ):
        self.current_total_pooled_ether = current_total_pooled_ether
        self.pre_total_pooled_ether = pre_total_pooled_ether
        self.pre_total_shares = pre_total_shares
        self.positive_rebase_limit = positive_rebase_limit
        self.max_total_pooled_ether = max_total_pooled_ether
