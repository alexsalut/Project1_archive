import datetime
import time
import os


import pandas as pd
from dbfread import DBF
from trading_calendar import TradingCalendar as tc


class AccountMonitor:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y-%m-%d')
        self.save_dir = r'\\192.168.1.116\target_position\monitor'
        self.panlan1_account_dir = r'\\192.168.1.116\trade\broker\cats\account'

    def update_panlan1_account(self):
        panlan1_info_last_trading_day = self.get_panlan1_account_info(date=-1)

        while True:
            panlan1_info_today = self.get_panlan1_account_info()
            stock_pl = panlan1_info_today['股票权益'] - panlan1_info_last_trading_day['股票权益']
            option_pl = panlan1_info_today['期权权益'] - panlan1_info_last_trading_day['期权权益']
            pct_change = ((panlan1_info_today['总权益'] - panlan1_info_last_trading_day['总权益'])
                          / panlan1_info_last_trading_day['总权益'])
            deposit_risk = float(panlan1_info_today['期权保证金风险度'].replace('%', ''))/100
            last_equity = panlan1_info_last_trading_day['总权益']
            today_equity = panlan1_info_today['总权益']
            panlan1_info_output = (f"{time.strftime('%Y-%m-%d %X')}，"
                                   f"股票盈亏：{stock_pl:.2f}，"
                                   f"期权盈亏：{option_pl:.2f}，"
                                   f"涨跌幅：{pct_change:.2%}，"
                                   f"保证金风险度：{deposit_risk:.2%}，"
                                   f"昨日权益：{last_equity:.2f}，"
                                   f"今日权益：{today_equity:.2f}")
            print(panlan1_info_output)
            self.retry_write_panlan1_info(panlan1_info_output)
            time.sleep(3)

    def retry_write_panlan1_info(self, panlan1_info_output):
        with open(rf'{self.save_dir}/实时盈亏.txt', 'a') as f:
            try:
                f.truncate(0)
                f.write(panlan1_info_output+'\n')
            except Exception as e:
                print(e)
                time.sleep(5)
                self.retry_write_panlan1_info(panlan1_info_output)

    def get_panlan1_account_info(self, date=None):
        if date is None:
            panlan1_account_s = self.get_today_panlan_account_info()
        else:
            panlan1_account_s = self.get_last_trading_day_panlan1_info()

        panlan1_account_s['总权益'] = panlan1_account_s['期权权益'] + panlan1_account_s['股票权益']
        panlan1_account_s.name = date
        return panlan1_account_s

    def get_today_panlan_account_info(self):
        option_path = rf'{self.panlan1_account_dir}/OptionFund.dbf'
        stock_path = rf'{self.panlan1_account_dir}/StockFund.dbf'
        try:
            panlan1_option_df = pd.DataFrame(iter(DBF(option_path)))
            panlan1_stock_df = pd.DataFrame(iter(DBF(stock_path)))
            panlan1_account_s = pd.Series({
                '期权权益': float(panlan1_option_df['TOTEQUITY'].iloc[0]),
                '股票权益': float(panlan1_stock_df['ASSET'].iloc[0]),
                '期权保证金风险度': panlan1_option_df['MARGINRP'].iloc[0],
            })
            return panlan1_account_s
        except Exception as e:
            print(e)
            print('[Panlan1 account monitor] Unable to get today info, retry in 2 seconds')
            time.sleep(2)
            self.get_today_panlan_account_info()

    def get_last_trading_day_panlan1_info(self):
        today = time.strftime('%Y-%m-%d')
        last_trading_day = tc().get_n_trading_day(today,-1).strftime('%Y-%m-%d')
        panlan1_option_path = rf'{self.panlan1_account_dir}/OptionFund_{last_trading_day}.csv'
        panlan1_stock_path = rf'{self.panlan1_account_dir}/StockFund_{last_trading_day}.csv'
        try:
            panlan1_option_df = pd.read_csv(panlan1_option_path, index_col=False)
            panlan1_stock_df = pd.read_csv(panlan1_stock_path, index_col=False)
            panlan1_account_s = pd.Series({
                '期权权益': panlan1_option_df['客户总权益'].iloc[0],
                '股票权益': panlan1_stock_df['账户资产'].iloc[0],
                '期权保证金风险度': panlan1_option_df['保证金风险度'].iloc[0],
            })
            return panlan1_account_s
        except Exception as e:
            print(e)
            print('[Panlan1 account monitor] Unable to get last trading day info, retry in 2 seconds')
            time.sleep(2)
            self.get_last_trading_day_panlan1_info()

if __name__ == '__main__':
    AccountMonitor().get_last_trading_day_panlan1_info()
