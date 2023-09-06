import pandas as pd



if __name__ == '__main__':

    file_path = r'C:\Users\Yz02\Desktop\盼澜交割单.xlsx'
    df = pd.read_excel(file_path, sheet_name=0, index_col=0)
    df1 = df.query('index==20230905 | index==20230807')
    df1['佣金费率'] = 100 * df1['佣金'] / abs(df1['成交金额']).astype(float)
    df1['印花税率'] = 100 * df1['印花税'] / abs(df1['成交金额'])
    df1['过户费率'] = 100 * df1['过户费'] / abs(df1['成交金额'])
    df1['交易规费率'] = 100 * df1['交易规费'] / abs(df1['成交金额'])
    df_select = df1.query('成交金额>40000')
    df_select = df_select.round(4)
    df1 = df1.round(4)
    df_select.to_excel(r'C:\Users\Yz02\Desktop\Data\Save\盼澜交割单.xlsx')
    print()


