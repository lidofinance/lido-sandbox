from lido_sandbox.contract import Contract


class WithdrawalVault(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)

    def withdraw_withdrawals(self, *args):
        pass
