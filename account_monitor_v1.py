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
        self.account_list = ['听涟2号', '盼澜1号']

    def daily_gen_account_overview(self, account_inflow_list):
        while True:
            if tc().check_is_trading_day(time.strftime('%Y%m%d')):
                current_minute = int(time.strftime('%H%M'))
                account_last_info_dict = self.get_all_account_info(account_list=self.account_list, date=-1)
                if current_minute > 900 and current_minute < 1502:
                    self.gen_account_overview(account_last_info_dict, account_inflow_list)
                else:
                    time.sleep(60)

    def gen_account_overview(self, account_last_info_dict, account_inflow_list):
        account_info_output = [(f"{time.strftime('%Y-%m-%d %X')}")]
        account_today_info_dict = self.get_all_account_info(account_last_info_dict.keys())
        for account in account_last_info_dict.keys():
            account_index = 0 if account == '盼澜1号' else 2
            account_today_info_dict[account].loc['股票盈亏'] = (
                    account_today_info_dict[account]['股票权益'] - account_inflow_list[account_index] -
                    account_last_info_dict[account]['股票权益'])
            account_today_info_dict[account].loc['期权盈亏'] = account_today_info_dict[account][
                                                                   '期权权益'] - account_inflow_list[
                                                                   account_index + 1] - \
                                                               account_last_info_dict[account]['期权权益']
            account_today_info_dict[account].loc['涨跌幅'] = (account_today_info_dict[account]['总权益'] -
                                                              account_last_info_dict[account]['总权益'] -
                                                              account_inflow_list[account_index] -
                                                              account_inflow_list[account_index + 1])/account_last_info_dict[account]['总权益']

            if account == '盼澜1号':
                account_today_info_dict[account].loc['保证金风险度'] = float(
                    account_today_info_dict[account]['期权保证金风险度'].replace('%', '')) / 100
                deposit_risk_string = f"保证金风险度：{account_today_info_dict[account]['保证金风险度']:.2%}，"
            else:
                deposit_risk_string = ''

            account_info_output.append((f"{account}，"
                                f"股票盈亏：{account_today_info_dict[account]['股票盈亏']:.2f}，"
                                f"期权盈亏：{account_today_info_dict[account]['期权盈亏']:.2f}，"
                                f"涨跌幅：{account_today_info_dict[account]['涨跌幅']:.3%}，"
                                f"{deposit_risk_string}"
                                f"昨日权益：{account_last_info_dict[account]['总权益']:.2f}，"
                                f"今日权益：{account_today_info_dict[account]['总权益']:.2f}"))

        print('\n'.join(account_info_output))
        self.retry_write_info('\n'.join(account_info_output))
        time.sleep(3)


    def get_all_account_info(self, account_list, date=None):
        account_info_dict = {}
        for account in account_list:
            account_info_dict[account] = self.get_account_info(account, date=date)
        return account_info_dict


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
            if date is None:
                option_df = pd.DataFrame(iter(DBF(rf'{self.panlan1_account_dir}/OptionFund.dbf')))
                stock_df = pd.DataFrame(iter(DBF(rf'{self.panlan1_account_dir}/StockFund.dbf')))
                col_list = ['TOTEQUITY', 'ASSET', 'MARGINRP']
            else:
                last_trading_day = tc().get_n_trading_day(time.strftime('%Y-%m-%d'), -1).strftime('%Y-%m-%d')
                option_df = pd.read_csv(rf'{self.panlan1_account_dir}/OptionFund_{last_trading_day}.csv',
                                        index_col=False)
                stock_df = pd.read_csv(rf'{self.panlan1_account_dir}/StockFund_{last_trading_day}.csv', index_col=False)
                col_list = ['客户总权益', '账户资产', '保证金风险度']
        elif account == '听涟2号':
            date = time.strftime('%Y%m%d') if date is None else tc().get_n_trading_day(time.strftime('%Y-%m-%d'),
                                                                                       -1).strftime('%Y%m%d')
            option_df = pd.read_csv(rf'{self.talang2_account_dir}/310317000090_OPTION_FUND.{date}.csv', encoding='gbk',
                                    index_col=False)
            stock_df = pd.read_csv(rf'{self.talang2_account_dir}/310310300343_RZRQ_FUND.{date}.csv', encoding='gbk',
                                   index_col=False)
            col_list = ['资产总值', '资产总值', '']

        else:
            print('The input account name is not valid')

        account_s = pd.Series({
            '期权权益': float(option_df[col_list[0]].iloc[0]),
            '股票权益': float(stock_df[col_list[1]].iloc[0]),
            '期权保证金风险度': option_df[col_list[2]].iloc[0] if col_list[2] != '' else None,
        })
        account_s['总权益'] = account_s['期权权益'] + account_s['股票权益']
        account_s.name = account
        return account_s


if __name__ == '__main__':
    account_inflow_list = [150000, -55000, #  盼澜1号出入金
                           0, 0] # 听涟2号出入金
    AccountMonitor().daily_gen_account_overview(account_inflow_list)
