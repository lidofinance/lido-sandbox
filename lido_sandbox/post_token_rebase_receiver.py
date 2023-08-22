from lido_sandbox.contract import Contract


class PostTokenRebaseReceiver(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)

    def handle_post_token_rebase(
        self,
        report_timestamp: int,
        time_elapsed: int,
        pre_total_shares: int,
        pre_total_ether: int,
        post_total_shares: int,
        post_total_ether: int,
        shares_minted_as_fees: int,
    ):
        pass
