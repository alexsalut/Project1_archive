import time
import pandas as pd
import xlwings as xw
import rqdatac as rq

from account import read_account_info
from utils import send_email, SendEmailInfo


class Account:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = r'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察.xlsx'
        self.remote_account_path = r'\\192.168.1.116\target_position\monitor\cnn策略观察.xlsx'

        # self.account_path = r'C:\Users\Yz02\Desktop\strategy_update_copy\cnn策略观察.xlsx'
        # self.remote_account_path = r'C:\Users\Yz02\Desktop\strategy_update_remote\cnn策略观察.xlsx'
        self.monitor_path = rf'C:\Users\Yz02\Desktop\strategy_update\monitor_{self.date}.xlsx'
        self.panlan_dir = r'\\192.168.1.116\trade\broker\cats\account'

    def update_account(self):
        self.update_account_monitor(sheet_name='单策略超额')
        self.update_account_monitor(sheet_name='多策略超额')
        self.update_account_talang(sheet_name='踏浪2号')
        self.update_account_talang(sheet_name='踏浪3号')
        self.update_account_panlan1()
        self.update_account_remote()

        content = rf"""
        文件路径: 
        {self.account_path}
        {self.remote_account_path}
        更新内容：
        单策略超额
        多策略超额
        踏浪2号
        踏浪3号
        盼澜1号
        """

        send_email(subject='[CNN 策略观察] 更新完成', content=None, receiver=SendEmailInfo.department['research'])

    def update_account_remote(self):
        try:
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.account_path)
            wb.save(self.remote_account_path)
            wb.close()
            app.quit()
            print(f'{self.remote_account_path} remote updating finished')
        except Exception as e:
            print(e)
            print(f'{self.account_path} remote updating failed, retry in 10 seconds')
            time.sleep(10)
            self.update_account_remote()

    def update_account_panlan1(self, today=None):
        try:
            today = time.strftime('%Y-%m-%d') if today is None else today
            option_df = pd.read_csv(rf'{self.panlan_dir}/OptionFund_{today}.csv', index_col=False)
            stock_df = pd.read_csv(rf'{self.panlan_dir}/StockFund_{today}.csv', index_col=False)
            transaction_df = pd.read_csv(rf'{self.panlan_dir}/TransactionsStatisticsDaily_{today}.csv', index_col=False)
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.account_path)
            sheet = wb.sheets['盼澜1号']
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
            sheet.range(f'A{last_row}').value = today  # date
            sheet.range(f'B{last_row}').formula = f'=H{last_row}+N{last_row}'  # 总资产
            sheet.range(f'C{last_row}').formula = f'=I{last_row}+O{last_row}'
            sheet.range(f'D{last_row}').formula = f'=C{last_row}/(B{last_row-1}+P{last_row}+Q{last_row})'  # 当日收益率
            sheet.range(f'E{last_row}').formula = f'=(E{last_row-1}+1)*(1+D{last_row})-1'  # 累计收益率
            sheet.range(f'G{last_row}').formula = f'=E{last_row}-MAX($E$2:E{last_row})'  # 累计回撤
            sheet.range(f'H{last_row}').value = stock_df['账户资产'].iloc[0]
            sheet.range(f'I{last_row}').formula = f'=H{last_row}-H{last_row-1}-P{last_row}'
            sheet.range(f'J{last_row}').value = stock_df['证券市值'].iloc[0]
            sheet.range(f'K{last_row}').formula = f'=J{last_row}/H{last_row}'
            sheet.range(f'L{last_row}').value = transaction_df['成交额'].sum()
            sheet.range(f'M{last_row}').formula = f'=L{last_row}/H{last_row-1}'
            sheet.range(f'N{last_row}').value = option_df['客户总权益'].iloc[0]
            sheet.range(f'O{last_row}').formula = f'=N{last_row}-N{last_row-1}-Q{last_row}'

            wb.save(self.account_path)
            wb.close()
            app.quit()
            print(f'{self.account_path} 盼澜1号 updating finished')
        except Exception as e:
            print(e)
            print(f'{self.account_path} 盼澜1号 updating failed. retry in 2 seconds')
            time.sleep(2)
            self.update_account_panlan1(today=today)

    def update_account_talang(self, sheet_name):
        index_ret = self.get_index_ret(sheet_name=sheet_name)
        account = 'tanglang2' if sheet_name == '踏浪2号' else 'tanglang3'
        account_info_s = read_account_info(date=self.date, account=account)

        try:
            self.input_talang_account_cell_value(
                sheet_name=sheet_name,
                account_info_s=account_info_s,
                index_ret=index_ret
            )
        except Exception as e:
            print(e)
            print(f'{self.account_path} with sheet name {sheet_name} updating failed, retry in 10 seconds')
            time.sleep(10)
            self.update_account_talang(sheet_name=sheet_name)

    def input_talang_account_cell_value(self, sheet_name, account_info_s, index_ret):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.account_path)
        time.sleep(10)
        sheet = wb.sheets[sheet_name]
        last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
        sheet.range(f'A{last_row}').value = self.date  # date
        sheet.range(f'B{last_row}').value = account_info_s['总资产']  # 总资产
        sheet.range(f'C{last_row}').formula = f'=B{last_row}-B{last_row - 1}-O{last_row - 1}'  # 当日盈亏
        sheet.range(f'D{last_row}').formula = f'=C{last_row}/(B{last_row - 1}+O{last_row - 1})'  # 当日盈亏率
        sheet.range(f'E{last_row}').formula = index_ret  # 指数收益率
        sheet.range(f'F{last_row}').formula = f'=D{last_row}-E{last_row}'  # 当日超额
        sheet.range(f'G{last_row}').formula = f'=G{last_row - 1}*(1+D{last_row})'  # 多头净值
        sheet.range(f'H{last_row}').formula = f'=H{last_row - 1}*(1+E{last_row})'  # 指数净值
        sheet.range(f'I{last_row}').formula = f'=G{last_row}/H{last_row}-1'  # 累计超额
        sheet.range(f'J{last_row}').formula = f'=I{last_row}-MAX(I2:I{last_row})'  # 超额回撤
        sheet.range(f'K{last_row}').value = account_info_s['股票总市值']  # 总市值
        sheet.range(f'L{last_row}').formula = f'=K{last_row}/B{last_row}'  # 总仓位
        sheet.range(f'M{last_row}').value = account_info_s['成交额']  # 成交额
        sheet.range(f'N{last_row}').formula = f'=M{last_row}/B{last_row - 1}'  # 双边换手率
        wb.save(self.account_path)
        wb.close()
        app.quit()
        print(f'{self.account_path} with sheet name {sheet_name} updating finished')

    def get_index_ret(self, sheet_name):
        index_code = '000905.SH' if sheet_name == '踏浪2号' else '000852.SH'
        rq.init()
        order_book_ids = rq.id_convert(index_code)
        index_ret = rq.get_live_minute_price_change_rate(order_book_ids).iloc[-1, 0]
        print(f'{index_code} return is {index_ret:.2%}')
        return index_ret

    def update_account_monitor(self, sheet_name):
        monitor_data = self.get_monitor_data()
        try:
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(self.account_path)
            sheet = wb.sheets[sheet_name]
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row+1
            sheet.range(f'A{last_row}').value = self.date  # date
            if sheet_name == '单策略超额':
                sheet.range(f'B{last_row}').value = monitor_data['sub_strategy_ret']    # 子策略涨幅
            elif sheet_name == '多策略超额':
                sheet.range(f'B{last_row}').value = monitor_data['strategy_ret']  # 策略涨幅
            else:
                raise

            sheet.range(f'C{last_row}').value = monitor_data['kc50_ret']  # 科创50涨幅
            sheet.range(f'D{last_row}').value = (sheet.range(f'B{last_row}').value
                                                 - sheet.range(f'C{last_row}').value)  # 指增超额
            sheet.range(f'E{last_row}').formula = f'=SUM(D2:D{last_row})'  # 累计指增超额算术
            sheet.range(f'F{last_row}').formula = f'=F{last_row-1}*(1+B{last_row})'  # 多头净值
            sheet.range(f'G{last_row}').formula = f'=G{last_row-1}*(1+C{last_row})'  # 指数净值
            sheet.range(f'H{last_row}').formula = f'=F{last_row}/G{last_row}'  # 累计超额净值
            sheet.range(f'I{last_row}').formula = f'=H{last_row}-1'  # 累计超额-几何
            sheet.range(f'J{last_row}').formula = f'=H{last_row}/MAX(H2:H{last_row})-1'  # 超额回撤
            wb.save(self.account_path)
            wb.close()
            app.quit()
            print(f'{self.account_path} with sheet name {sheet_name} updated successfully')
        except Exception as e:
            print(e)
            print(f'{self.account_path} with sheet name {sheet_name} updating failed, retry in 10 seconds')
            time.sleep(10)
            self.update_account_monitor(sheet_name=sheet_name)

    def get_monitor_data(self):

        monitor_df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=0)
        monitor_data = pd.Series(index=['kc50_ret', 'strategy_ret', 'sub_strategy_ret', 'excess_ret', 'sub_excess_ret'],
                                 data=[
                                     monitor_df.iloc[0, 1],
                                     monitor_df.iloc[0, 7],
                                     monitor_df.iloc[2, 7],
                                     monitor_df.iloc[0, 8],
                                     monitor_df.iloc[2, 8],
                                       ],
                                 dtype=float)

        if (monitor_data == 'Refreshing').any():
            print('Account monitor data is refreshing, wait for 10 seconds to retry for access')
            self.get_monitor_data()
        else:
            print('Get account monitor data successfully')
            return monitor_data

if __name__ == '__main__':
    Account().update_account()
