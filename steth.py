from collections import defaultdict

class stETH:
    _shares: dict[str, int]
    _allowances: dict[str, dict[str, int]]
    _total_shares: int = 0

    INFINITE_ALLOWANCE: int = 2**256 - 1
    INITIAL_TOKEN_HOLDER: str = "0xdead"

    def __init__(self) -> None:
        self._shares = defaultdict(int)
        self._allowances = defaultdict(lambda: defaultdict(int))

    def total_supply(self) -> int:
        return self._get_total_pooled_ether()

    def get_total_pooled_ether(self) -> int:
        return self._get_total_pooled_ether()

    def balance_of(self, account: str) -> int:
        return self.get_pooled_eth_by_shares(self.shares_of(account))

    def transfer(self, sender: str, recipient: str, amount: int) -> bool:
        self._transfer(sender, recipient, amount)
        return True

    def allowance(self, owner: str, spender: str) -> int:
        return self._allowances[owner][spender]

    def approve(self, sender: str, spender: str, amount: int) -> bool:
        self._approve(sender, spender, amount)
        return True

    def transfer_from(
        self, msg_sender: str, sender: str, recipient: str, amount: int
    ) -> bool:
        self._spend_allowance(sender, msg_sender, amount)
        self._transfer(sender, recipient, amount)
        return True

    def get_total_shares(self) -> int:
        return self._get_total_shares()

    def shares_of(self, account: str) -> int:
        return self._shares_of(account)

    def get_shares_by_pooled_eth(self, eth_amount: int) -> int:
        return eth_amount * self._get_total_shares() // self._get_total_pooled_ether()

    def get_pooled_eth_by_shares(self, shares_amount: int) -> int:
        return (
            shares_amount * self._get_total_pooled_ether() // self._get_total_shares()
        )

    def transfer_shares(
        self, msg_sender: str, recipient: str, shares_amount: int
    ) -> int:
        self._transfer_shares(msg_sender, recipient, shares_amount)
        tokens_amount = self.get_pooled_eth_by_shares(shares_amount)
        return tokens_amount

    def transfer_shares_from(
        self, msg_sender: str, sender: str, recipient: str, shares_amount: int
    ) -> int:
        tokens_amount = self.get_pooled_eth_by_shares(shares_amount)
        self._spend_allowance(sender, msg_sender, tokens_amount)
        self._transfer_shares(sender, recipient, shares_amount)
        return tokens_amount

    def _get_total_pooled_ether(self) -> int:
        pass

    def _transfer(self, sender: str, recipient: str, amount: int) -> None:
        shares_to_transfer = self.get_shares_by_pooled_eth(amount)
        self._transfer_shares(sender, recipient, shares_to_transfer)

    def _approve(self, owner: str, spender: str, amount: int) -> None:
        self._allowances[owner][spender] = amount

    def _spend_allowance(self, owner: str, spender: str, amount: int) -> None:
        current_allowance = self._allowances[owner][spender]
        if current_allowance != self.INFINITE_ALLOWANCE:
            assert current_allowance >= amount
            self._approve(owner, spender, current_allowance - amount)

    def _get_total_shares(self) -> int:
        return self._total_shares

    def _shares_of(self, account: str) -> int:
        return self._shares[account]

    def _transfer_shares(self, sender: str, recipient: str, shares_amount: int) -> None:
        current_sender_shares = self._shares_of(sender)
        assert shares_amount <= current_sender_shares

        self._shares[sender] = current_sender_shares - shares_amount
        self._shares[recipient] += shares_amount

    def _mint_shares(self, recipient: str, shares_amount: int) -> None:
        self._total_shares = self._get_total_shares() + shares_amount
        self._shares[recipient] = self._shares[recipient] + shares_amount

    def _burn_shares(self, account: str, shares_amount: int) -> int:
        account_shares = self._shares[account]
        assert shares_amount <= account_shares

        new_total_shares = self._get_total_shares() - shares_amount
        self._total_shares = new_total_shares
        self._shares[account] = account_shares - shares_amount

        return new_total_shares

    def _mint_initial_shares(self, shares_amount: int) -> None:
        self._mint_shares(self.INITIAL_TOKEN_HOLDER, shares_amount)
