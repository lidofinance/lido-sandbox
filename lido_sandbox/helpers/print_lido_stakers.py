from lido_sandbox.helpers.wei_to_eth import wei_to_eth
from lido_sandbox.locator import Locator
import pandas as pd


def print_lido_stakers(locator: Locator):
    _, lido = locator.lido

    df = pd.DataFrame(
        {
            "address": [key for key, _ in lido._shares.items()],
            "shares": [wei_to_eth(value) for _, value in lido._shares.items()],
            "steth": [
                wei_to_eth(lido.get_pooled_eth_by_shares(value))
                for _, value in lido._shares.items()
            ],
        }
    )

    return df.style.format(precision=5).format_index()
