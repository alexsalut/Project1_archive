import pandas as pd
from dbfread import DBF

path = r"C:/Users/Yz02/Desktop/Data/Save/trade.dbf"
table = DBF(path, encoding='gbk')
df = pd.DataFrame(iter(table))
print(df)
