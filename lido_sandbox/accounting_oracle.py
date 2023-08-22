from lido_sandbox.contract import Contract


class AccountingOracle(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address)
