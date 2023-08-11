from EmQuantAPI import c

import pandas as pd


def c_get_trade_dates(start, end):
    c.start()
    c_data = c.tradedates(start, end, "period=1").Data
    trade_dates = pd.to_datetime(c_data).strftime('%Y%m%d')
    c.stop()
    return list(trade_dates)


def transfer_to_jy_ticker(universe, inverse=False):
    """
    input: [601919.SH, 000333.SZ]
    output: [sh601919, sz000333]
    """
    if inverse:
        return [x[-6:]+'.'+x[:2].upper() for x in universe]
    else:
        return [x.split('.')[-1].lower()+x.split('.')[0] for x in universe]


