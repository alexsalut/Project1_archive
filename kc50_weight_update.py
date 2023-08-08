import datetime

from EmQuantAPI import c


def kc50_weight_update():
    current_date = datetime.date.today()

    c.start()
    kc50_weight = c.ctr("INDEXCOMPOSITION",
                        "SECUCODE,WEIGHT",
                        f"IndexCode=000688.SH,EndDate={current_date},ispandas=1"
                        )
    kc50_weight.columns = ['SECUCODE', 'WEIGHT']
    c.stop()
    kc50_weight.to_pickle(f'kc50_{current_date.strftime("%Y%m%d")}.pkl')
    print("Data updated and new .pkl file generated at:", datetime.datetime.now())










