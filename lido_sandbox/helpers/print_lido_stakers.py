from lido_sandbox.helpers.print_table import print_table
from lido_sandbox.helpers.wei_to_eth import wei_to_eth
from lido_sandbox.locator import Locator

def print_lido_stakers(locator: Locator):
    _, lido = locator.lido

    print_table(
        [[key, wei_to_eth(value), wei_to_eth(lido.get_pooled_eth_by_shares(value))] for key, value in lido._shares.items()],
        ['address', 'shares', 'steth']
    )