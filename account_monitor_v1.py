import time

import pandas as pd
from dbfread import DBF
from trading_calendar import TradingCalendar as tc


class AccountMonitor:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y-%m-%d')
        self.save_dir = r'\\192.168.1.116\target_position\monitor'
        self.panlan1_account_dir = r'\\192.168.1.116\trade\broker\cats\account'
        self.talang2_account_dir = r'\\192.168.1.116\trade\broker\emc\account'

    def gen_all_account_overview(self):
        panlan1_last_info = self.get_account_info('盼澜1号', date=-1)
        tinglian2_last_info = self.get_account_info('听涟2号', date=-1)
        while True:
            panlan1_output = self.gen_account_overview('盼澜1号', panlan1_last_info)
            tinglian2_output = self.gen_account_overview('听涟2号', tinglian2_last_info)
            all_output = (f"{time.strftime('%Y-%m-%d %X')}\n") + panlan1_output + "\n" + tinglian2_output + "\n"
            print(all_output)
            self.retry_write_info(all_output)
            time.sleep(3)

    def gen_account_overview(self, account, account_last_info):
        today_info_s = self.get_account_info(account)
        stock_pl = today_info_s['股票权益'] - account_last_info['股票权益']
        option_pl = today_info_s['期权权益'] - account_last_info['期权权益']
        pct_change = ((today_info_s['总权益'] - account_last_info['总权益'])
                      / account_last_info['总权益'])

        deposit_risk = float(today_info_s['期权保证金风险度'].replace('%', '')) / 100 if account == '盼澜1号' else None
        deposit_risk_string = f"保证金风险度：{deposit_risk:.2%}，" if deposit_risk is not None else ''

        account_info_output = (f"{account}，"
                               f"股票盈亏：{stock_pl:.2f}，"
                               f"期权盈亏：{option_pl:.2f}，"
                               f"涨跌幅：{pct_change:.3%}，"
                               f"{deposit_risk_string}"
                               f"昨日权益：{account_last_info['总权益']:.2f}，"
                               f"今日权益：{today_info_s['总权益']:.2f}")
        return account_info_output

    def retry_write_info(self, output):
        path = rf'{self.save_dir}/实时盈亏.txt'
        with open(path, 'r+') as f:
            try:
                f.truncate(0)
                f.write(output + '\n')
                f.flush()
            except Exception as e:
                print(e)
                time.sleep(5)
                self.retry_write_info(output)

    def get_account_info(self, account, date=None):
        if account == '盼澜1号':
            if date == None:
                option_df = pd.DataFrame(iter(DBF(rf'{self.panlan1_account_dir}/OptionFund.dbf')))
                stock_df = pd.DataFrame(iter(DBF(rf'{self.panlan1_account_dir}/StockFund.dbf')))
                col_list = ['TOTEQUITY', 'ASSET', 'MARGINRP']
            else:
                last_trading_day = tc().get_n_trading_day(time.strftime('%Y-%m-%d'), -1).strftime('%Y-%m-%d')
                option_df = pd.read_csv(rf'{self.panlan1_account_dir}/OptionFund_{last_trading_day}.csv', index_col=False)
                stock_df = pd.read_csv(rf'{self.panlan1_account_dir}/StockFund_{last_trading_day}.csv', index_col=False)
                col_list = ['客户总权益', '账户资产', '保证金风险度']
        elif account == '听涟2号':
            date = time.strftime('%Y%m%d') if date is None else tc().get_n_trading_day(time.strftime('%Y-%m-%d'), -1).strftime('%Y%m%d')
            option_df = pd.read_csv(rf'{self.talang2_account_dir}/310317000090_OPTION_FUND.{date}.csv', encoding='gbk', index_col=False)
            stock_df = pd.read_csv(rf'{self.talang2_account_dir}/310310300343_RZRQ_FUND.{date}.csv', encoding='gbk', index_col=False)
            col_list = ['资产总值', '资产总值', '']

        else:
            print('The input account name is not valid')

        account_s = pd.Series({
            '期权权益': float(option_df[col_list[0]].iloc[0]),
            '股票权益': float(stock_df[col_list[1]].iloc[0]),
            '期权保证金风险度': option_df[col_list[2]].iloc[0] if col_list[2]!='' else None ,
        })
        account_s['总权益'] = account_s['期权权益'] + account_s['股票权益']
        account_s.name = account
        return account_s

if __name__ == '__main__':
    AccountMonitor().gen_all_account_overview()








