import rqdatac
import pandas as pd
import glob
import os

if __name__ == '__main__':
    dir = r'\\192.168.1.116\trade\broker\emc\account'
    option_fund_path_list = glob.glob(dir + '/310317000090_OPTION_FUND.*.csv')
    rzrq_fund_path_list = glob.glob(dir + '/310310300343_RZRQ_FUND.*.csv')
    option_fund = []
    for path in option_fund_path_list:
        date = pd.to_datetime(os.path.basename(path).split('.')[1])
        df = pd.read_csv(path, encoding='gbk')
        df.index = [date] * df.shape[0]
        option_fund.append(df)
    option_fund_df = pd.concat(option_fund, axis=0)
    option_fund_df = option_fund_df.rename(columns={x: 'option_' + x for x in option_fund_df.columns})

    rzrq_fund = []
    for path in rzrq_fund_path_list:
        date = pd.to_datetime(os.path.basename(path).split('.')[1])
        df = pd.read_csv(path, encoding='gbk')
        df.index = [date] * df.shape[0]
        rzrq_fund.append(df)
    rzrq_fund_df = pd.concat(rzrq_fund, axis=0)
    rzrq_fund_df = rzrq_fund_df.rename(columns={x: 'rzrq_' + x for x in rzrq_fund_df.columns})

    fund_df = pd.concat([option_fund_df, rzrq_fund_df], axis=1)
    new_fund_df = fund_df.query('index > 20230903')
    new_fund_df = new_fund_df.fillna(0)
    new_fund_df['总权益'] = new_fund_df['option_资产总值'] + new_fund_df['rzrq_资产总值'] - new_fund_df['rzrq_总负债'] - new_fund_df['option_总负债']
    new_fund_df['option_权益'] = new_fund_df['option_资产总值'] - new_fund_df['option_总负债']
    new_fund_df['rzrq_权益'] = new_fund_df['rzrq_资产总值'] - new_fund_df['rzrq_总负债']
    save_df = new_fund_df[['option_资产总值','option_总市值', 'option_总负债', 'option_权益','rzrq_资产总值','rzrq_总市值', 'rzrq_总负债', 'rzrq_权益', '总权益']]
    save_df.to_excel(r'C:\Users\Yz02\Desktop\panlan1.xlsx')
    print()
















