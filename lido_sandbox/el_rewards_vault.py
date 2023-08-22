from lido_sandbox.contract import Contract


class ElRewardsVault(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)

    def withdraw_rewards(self, *args):
        pass
