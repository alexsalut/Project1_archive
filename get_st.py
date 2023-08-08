import pandas as pd

from EmQuantAPI import c


def gen_st_list(start_date, end_date):
    print("Downloading ST list")
    print("----------------------------")
    c.start()

    trade_dates = c.tradedates(
        start_date,
        end_date,
        "period=1,order=1,market=CNSESH",
    ).Dates
    all_st_list = []
    for date in trade_dates:
        st_list = c.sector("001023", date).Codes
        tmp_st_s = pd.Series(st_list, index=[date]*len(st_list))
        all_st_list.append(tmp_st_s)
    c.stop()

    all_st_s = pd.concat(all_st_list)
    return all_st_s


st_s = gen_st_list("2022-08-31", "2023-08-07")
print()
