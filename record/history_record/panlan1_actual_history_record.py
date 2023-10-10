import os
import glob

import pandas as pd
import xlwings as xw
import rqdatac as rq

from util.utils import retry_save_excel

class PanlanAccountRecord():
    def __init__(self):
        self.panlan1_option_history_dir = r'C:\Users\Yz02\Desktop\Data\Save\盼澜1号\OptionFund'
        self.panlan1_stock_history_dir = r'\\192.168.1.116\trade\broker\emc\account'
        self.record_path = r'C:\Users\Yz02\Desktop\strategy_update\副本cnn策略观察.xlsx'
        self.nav_history_path = r'C:\Users\Yz02\Desktop\Data\Save\盼澜1号\panlanNetVal.csv'

    def record_panlan_account(self):
        stock_df = self.get_stock_history_data()
        option_s = self.get_option_history_data()
        nav_s = self.get_nav_history_data()
        transaction_s = self.get_stock_transaction_volume()
        panlan_df = (pd.concat([stock_df, option_s, transaction_s, nav_s], axis=1))
        panlan_df.index = pd.to_datetime(panlan_df.index)
        rq.init()
        trading_days = rq.get_trading_dates(start_date='20230728', end_date='20230911', market='cn')

        panlan_df = panlan_df.loc[trading_days].rename(columns={'cumu_netvalue':'累计净值'})

        panlan_df.loc[['20230801','20230907'] ,'股票出入金'] = [30000, -2534865.25]
        panlan_df.loc[['20230801', '20230823', '20230906'],'期权出入金'] = [-30000, -100000, 100000]
        panlan_df[['期权出入金','股票出入金']] = panlan_df[['期权出入金','股票出入金']].fillna(0)
        panlan_df.loc['20230808',['股票资产总值', '股票总市值','股票总仓位']] = panlan_df.loc['20230807',['股票资产总值', '股票总市值','股票总仓位']]
        panlan_df.loc['20230808',['股票成交额']] = 0

        panlan_df['总资产'] = panlan_df['股票资产总值'] + panlan_df['期权总权益']
        panlan_df['股票盈亏'] = panlan_df['股票资产总值'] - panlan_df['股票资产总值'].shift(1)-panlan_df['股票出入金']
        panlan_df['期权盈亏'] = panlan_df['期权总权益'] - panlan_df['期权总权益'].shift(1)-panlan_df['期权出入金']
        panlan_df['多头收益率'] = panlan_df['股票盈亏']/panlan_df['股票资产总值'].shift(1)
        panlan_df['双边换手率'] = panlan_df['股票成交额']/panlan_df['股票资产总值'].shift(1)
        panlan_df['当日收益率'] = (panlan_df['股票盈亏'] + panlan_df['期权盈亏'])/panlan_df['总资产'].shift(1)
        panlan_df['累计收益率'] = (panlan_df['当日收益率']+1).cumprod()-1
        panlan_df['累计回撤'] = panlan_df['累计收益率'] - panlan_df['累计收益率'].cummax()

        panlan_df.loc[panlan_df['股票总仓位']==0, '双边换手率'] = 0


        col_list = [
            '总资产',
            '股票资产总值',
            '股票总市值',
            '股票总仓位',
            '股票成交额',
            '股票盈亏',
            '多头收益率',
            '期权总权益',
            '期权盈亏',
            '当日收益率',
            '累计收益率',
            '累计净值',
            '累计回撤',
            '双边换手率',
            '股票出入金',
            '期权出入金',
        ]

        panlan_df = panlan_df[col_list]

        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.record_path)
        sheet = wb.sheets['盼澜1号']
        sheet.clear_contents()
        sheet['A1'].options(index=True).value = panlan_df
        retry_save_excel(wb, self.record_path)

        # for i in panlan_df.index:
        #     sheet[f'A{i + 2}'].value = panlan_df.loc[i,'index']
        #     sheet[f'B{i + 2}'].value = panlan_df.loc[i,'总资产']
        #     sheet[f'C{i + 2}'].formula = f'=(D{i + 2}+E{i + 2})/(B{i + 1}+N{i + 1}+O{i + 1})'
        #     sheet[f'D{i + 2}'].value = panlan_df.loc[i,'股票盈亏']
        #     sheet[f'E{i + 2}'].value = panlan_df.loc[i, '期权盈亏']
        #     sheet[f'F{i + 2}'].value = panlan_df.loc[i,'多头收益率']
        #     sheet[f'G{i + 2}'].value = panlan_df.loc[i, 'cumu_netvalue']
        #     sheet[f'H{i + 2}'].formula = f'=(1+H{i + 1})*(1+C{i + 2})-1'
        #     sheet[f'I{i + 2}'].formula = f'=H{i + 2}-MAX(H$2:H{i + 2})'
        #     sheet[f'J{i + 2}'].value = panlan_df.loc[i, '股票总市值']
        #     sheet[f'K{i + 2}'].value = panlan_df.loc[i, '股票总仓位']
        #     sheet[f'L{i + 2}'].value = panlan_df.loc[i, '股票成交额']
        #     sheet[f'M{i + 2}'].formula = f'=L{i+2}/(P{i+1}+N{i+1})'
        #     sheet[f'P{i + 2}'].value = panlan_df.loc[i,'股票资产总值']
        # retry_save_excel(wb, self.record_path)


    def get_nav_history_data(self):
        history_nav_df = pd.read_csv(self.nav_history_path, index_col=False)
        history_nav_df['date'] = history_nav_df.loc[:,'date'].str.replace('-','')
        return history_nav_df.set_index('date')['cumu_netvalue']

    def get_stock_history_data(self):
        stock_path_list = glob.glob(rf'{self.panlan1_stock_history_dir}/310300016516_FUND.*.csv')
        s = []
        for path in stock_path_list:
            date = os.path.basename(path).split('.')[1]
            daily_stock_df = pd.read_csv(path, index_col=False, encoding='gbk')
            daily_stock_df['date'] = date
            s.append(daily_stock_df)
        stock_df = pd.concat(s).set_index('date').rename(columns={'资产总值':'股票资产总值','总市值':'股票总市值'})
        stock_df['股票总仓位'] = stock_df['股票总市值']/stock_df['股票资产总值']
        return stock_df[['股票资产总值','股票总市值','股票总仓位']]

    def get_option_history_data(self):
        option_path_list = glob.glob(rf'{self.panlan1_option_history_dir}/OptionFund_*.csv')
        s = []
        for path in option_path_list:
            date = os.path.basename(path).split('.')[0].split('_')[1].replace('-','')
            daily_option_df = pd.read_csv(path, index_col=False).reset_index(drop=True)
            daily_option_df['date'] = date
            s.append(daily_option_df)
        option_df = pd.concat(s).set_index('date').rename(columns={'客户总权益':'期权总权益'})
        return option_df['期权总权益']

    def get_stock_transaction_volume(self):
        stock_path_list = glob.glob(rf'{self.panlan1_stock_history_dir}/310300016516_MATCH.*.csv')
        s = pd.Series(name='股票成交额')
        for path in stock_path_list:
            date = os.path.basename(path).split('.')[1]
            daily_stock_df = pd.read_csv(path, index_col=False, encoding='gbk')
            daily_stock_df['成交金额'] = daily_stock_df['成交数量'].mul(daily_stock_df['成交价格'])
            s.loc[date] = daily_stock_df['成交金额'].sum()
        return s





if __name__ == '__main__':
    PanlanAccountRecord().record_panlan_account()
