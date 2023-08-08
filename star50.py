import pandas as pd
from EmQuantAPI import c


def get_star50(date):
    print("Downloading Star 50")
    print("----------------------------")
    c.start()
    data = c.ctr("INDEXCOMPOSITION", "SECUCODE,WEIGHT", "IndexCode=000688.SH,EndDate=2022-08-31").Data
    df = pd.DataFrame(data)
    star_50 = df.transpose()
    star_50.columns = ['code', 'weight']
    return star_50


star50 = get_star50("2022-08-31")
print()
