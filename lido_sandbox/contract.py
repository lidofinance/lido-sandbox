from typing import Self


class Contract:
    address: str
    balance: int

    _contracts_registry: dict[str, Self] = {}

    def __new__(cls, address: str, *args, **kwargs):
        if not address in cls._contracts_registry:
            instance = super().__new__(cls)
            cls._contracts_registry[address] = instance

        return cls._contracts_registry[address]

    def __init__(self, address: str, balance: int = 0) -> None:
        self.address = address
        self.balance = balance
