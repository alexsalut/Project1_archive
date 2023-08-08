import datetime

import pandas as pd

from EmQuantAPI import c


def st_list_update():
    print("Downloading ST list")
    print("----------------------------")
    start_date = "2020-08-01"
    end_date = datetime.date.today().strftime("%Y-%m-%d")

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
    all_st_s = pd.concat(all_st_list)

    all_st_s = all_st_s.str[-2:].str.lower() + all_st_s.str[:6]
    all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
    all_st_s.to_csv("st_list.csv")
    print("Data updated and new .csv file generated at:", datetime.datetime.now())
    c.stop()









