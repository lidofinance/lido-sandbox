from time import time

class WithdrawalRequest:
    def __init__(
        self,
        cumulative_steth: int = 0,
        cumulative_shares: int = 0,
        owner: str = 'nobody',
        timestamp: int = int(time()),
        claimed: bool = True,
        report_timestamp: int = 0,
    ) -> None:
        self.cumulative_steth = cumulative_steth
        self.cumulative_shares = cumulative_shares
        self.owner = owner
        self.timestamp = timestamp
        self.claimed = claimed
        self.report_timestamp = report_timestamp

class WithdrawalRequestStatus:
    def __init__(
        self,
        amount_of_steth: int,
        amount_of_shares: int,
        owner: str,
        timestamp: int,
        is_finalized: bool,
        is_claimed: bool,
    ) -> None:
        self.amount_of_steth = amount_of_steth
        self.amount_of_shares = amount_of_shares
        self.owner = owner
        self.timestamp = timestamp
        self.is_finalized = is_finalized
        self.is_claimed = is_claimed
