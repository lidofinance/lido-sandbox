from lido_sandbox.helpers.wei_to_eth import wei_to_eth
from lido_sandbox.locator import Locator
import pandas as pd


def print_global_lido_statistic(locator: Locator):
    _, lido = locator.lido

    deposited_validators, cl_validators, cl_balance = lido.get_beacon_stat()

    df = pd.DataFrame(
        {
            "param": [
                "total supply",
                "total shares",
                "buffered",
                "cl balance",
                "cl vals",
                "deposited vals",
            ],
            "value": [
                wei_to_eth(lido.total_supply()),
                wei_to_eth(lido.get_total_shares()),
                wei_to_eth(lido.get_buffered_ether()),
                wei_to_eth(cl_balance),
                cl_validators,
                deposited_validators,
            ],
        }
    )

    return df.style.format(precision=5)
