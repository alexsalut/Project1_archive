#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/5 9:09
# @Author  : Suying
# @Site    : 
# @File    : product_ret_decomposition.py

import time
import pandas as pd
import rqdatac as rq
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar as tc
from product_ret_analysis.account_reader import get_position_s, get_transaction_df, get_product_record, get_monitor_data
from util.file_location import FileLocation


class ProductRetDecomposition:
    def __init__(self, date=None):
        self.date = time.strftime('%Y%m%d') if date is None else date
        self.last_trading_day = tc().get_n_trading_day(self.date, -1).strftime('%Y%m%d')
        self.stock_list = ['踏浪1号', '盼澜1号', '听涟2号']
        self.option_list = ['听涟2号', '盼澜1号']
        self.stock_fee = {
            '盼澜1号': {'买入': 0.01154 / 100, '卖出': 0.06154 / 100},
            '听涟2号': {'担保品买入': 0.01354 / 100, '担保品卖出': 0.06354 / 100, '融资买入': 0.01354 / 100}
        }
        self.option_tickers = ['10005541', '10005532', '588000.XSHG']  # d（沽-购 + ETF）/ETF

    def gen_email(self):
        table_1, table_2, s_trade_pl_df = self.gen_table()
        styled_1, styled_2, styled_3 = (self.format_table(table_1),
                                        self.format_table(table_2),
                                        self.format_table(s_trade_pl_df,if_percent=False))
        content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号|盼澜1号|听涟2号 收益率分析</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    """
        content += f"""
        <p>各产品交易终端收益率分析</p>
        <center>{styled_1}</center>
        <p>注：</p>
        <p>收益率1和2均是通过交易终端导出单计算得到</p>
        <p>收益率1=净资产的增长率（导出单Fund文件）</p>
        <p>收益率2=交易收益率（导出单Trade文件）+ 持有收益率（导出单Position文件）</p>
        """

        content += f"""
        <center>{styled_2}</center>
        <p>注：</p>
        <p>股票权重配置误差=股票持有收益率-monitor组合涨幅</p>
        <p>期权权重配置误差=期权持有收益率+指数收益率+ETF跟踪误差-期权基差</p>
        """

        content += f"""
        <p>各产品交易终端股票交易盈亏分析</p>
        <center>{styled_3}</center>
        """

        subject = f'[产品收益率分析] {self.date}'
        Mail().send(subject=subject,
                    body_content=content,
                    receivers=R.department['research'])

    def format_table(self, df, if_percent=True):

        def highlight_diff(s):
            if abs(s) > 2000:
                return f'background-color: lightblue'
            else:
                return ''

        if if_percent:
            styled_df = df.style.format({product: '{:.2%}' for product in self.stock_list})
        else:
            styled_df = df.style.applymap(highlight_diff)
            styled_df = styled_df.format({product: '{:.2f}' for product in self.stock_list})
        styled_df = styled_df.to_html(classes='table', escape=False)
        styled_df = styled_df.replace('<table',
                                      '<table style="border-collapse: collapse; border: 1px solid black;"')
        styled_df = styled_df.replace('<tr', '<tr style="border-bottom: 1px solid black;"')
        styled_df = styled_df.replace('<th', '<th style="border-right: 1px solid black;"')
        styled_df = styled_df.replace('<td', '<td style="border-right: 1px solid black;"')
        styled_df = styled_df.replace('nan%', '-')
        styled_df = styled_df.replace('nan', '-')
        return styled_df

    def gen_table(self):
        df, s_trade_df = self.gen_df()
        table_1 = df.loc[['股票收益率1', '股票收益率2', '股票收益误差', '期权收益率1', '期权收益率2', '期权收益误差'],
                  :]
        table_2_row = [x for x in df.index if x not in table_1.index]
        table_2 = df.loc[table_2_row, :]
        return table_1, table_2, s_trade_df

    def gen_df(self):
        data = []
        stock_trade = []
        for product in self.stock_list:
            product_dict, s_trade_pl_s = self.get_ret_decomposition(product)
            s = pd.Series(product_dict, name=product)
            data.append(s)
            stock_trade.append(s_trade_pl_s)
        df = pd.concat(data, axis=1)
        s_trade_pl_df = pd.concat(stock_trade, axis=1)

        return df, s_trade_pl_df

    def get_ret_decomposition(self, product):
        product_dict = {}
        stock_asset = get_product_record(product, '股票资产总值', self.last_trading_day)
        s_trade_pl, s_trade_pl_s = self.get_trade_pl(product, 'Credit')
        product_dict['股票收益率1'] = get_product_record(product, '股票盈亏', self.date) / stock_asset
        product_dict['股票交易收益率'] = s_trade_pl / stock_asset
        product_dict['股票持有收益率'] = self.get_hold_pl(product, 'Credit') / stock_asset
        product_dict['股票收益率2'] = product_dict['股票交易收益率'] + product_dict['股票持有收益率']
        product_dict['股票收益误差'] = product_dict['股票收益率1'] - product_dict['股票收益率2']
        product_dict['monitor组合涨幅'] = get_monitor_data(product, self.date)
        product_dict['股票权重配置误差'] = product_dict['股票持有收益率'] - product_dict['monitor组合涨幅']

        if product in self.option_list:
            op_trade_pl, _ = self.get_trade_pl(product, 'Option')
            product_dict['期权收益率1'] = get_product_record(product, '期权盈亏', self.date) / stock_asset
            product_dict['期权交易收益率'] = op_trade_pl / stock_asset
            product_dict['期权持有收益率'] = self.get_hold_pl(product, 'Option') / stock_asset
            product_dict['期权收益率2'] = product_dict['期权交易收益率'] + product_dict['期权持有收益率']
            product_dict['期权收益误差'] = product_dict['期权收益率1'] - product_dict['期权收益率2']
            product_dict['指数收益率'] = get_monitor_data('000688.SH', self.date)
            product_dict['期权基差'], etf_ret = self.get_base_diff()
            product_dict['ETF跟踪误差'] = etf_ret - product_dict['指数收益率']
            product_dict['期权权重配置误差'] = product_dict['期权持有收益率'] + product_dict['指数收益率'] + \
                                               product_dict['ETF跟踪误差'] - product_dict['期权基差']

        return product_dict, s_trade_pl_s

    def get_trade_fee(self, product, type):
        sep = '*' * 32
        print(fr'{sep}Generating {product} {type} Trading fee {sep}')
        trade_df, _ = get_transaction_df(product, type, self.date)

    def get_trade_pl(self, product, type):
        sep = '*' * 32
        print(fr'{sep}Generating {product} {type} Trading P&L {sep}')
        _, trade_df = get_transaction_df(product, type, self.date)
        trade_df.index = trade_df.index.astype(str)
        ticker_list = trade_df.index.astype(str).tolist()
        if ticker_list:
            new_trade_df = pd.concat(
                [trade_df, get_t_raw_daily_bar(ticker_list=ticker_list, type=type, date=self.date)], axis=1)
            trade_pl_s = new_trade_df.apply(
                lambda x: x['成交数量'] * x['close'] - x['成交金额'] if x['成交金额'] > 0
                else -x['成交数量'] * x['close'] - x['成交金额'], axis=1).rename(product)
            trade_pl = trade_pl_s.sum()
        else:
            trade_pl = 0
            trade_pl_s = pd.Series(name=product)
        print(f'{product} {type} Trading P&L is {trade_pl}')
        return trade_pl, trade_pl_s

    def get_hold_pl(self, product, type):
        sep = '*' * 32
        print(fr'{sep}Generating {product} {type} Holding P&L {sep}')
        position_s = get_position_s(account=product, type=type, date=self.last_trading_day)
        ticker_list = position_s.index.astype(str).tolist()

        last_close = get_t_raw_daily_bar(ticker_list=ticker_list, type=type, date=self.last_trading_day)
        today_close = get_t_raw_daily_bar(ticker_list=ticker_list, type=type, date=self.date)
        position_s = get_position_s(account=product, type=type, date=self.last_trading_day)
        position_s.index = position_s.index.astype(str)
        hold_pl = ((today_close - last_close).mul(position_s)).sum()
        print(f'{product} {type} Holding P&L is {hold_pl}')
        return hold_pl

    def get_base_diff(self):
        l = self.option_tickers
        df = get_t_raw_daily_bar(
            ticker_list=l,
            type='Option',
            col=['close', 'prev_close'],
            date=self.date
        )
        s = df['close'] - df['prev_close']
        base_diff = (s[l[0]] - s[l[1]] + s[l[2]]) / df.loc[l[2], 'prev_close']
        return base_diff, s[l[2]] / df.loc[l[2], 'prev_close']


def get_t_raw_daily_bar(ticker_list, type, col='close', date=None):
    if type == 'Option':
        rq.init()
        raw_daily = rq.get_price(ticker_list, start_date=date, end_date=date)
        if raw_daily is None:
            print('No data for', ticker_list, date, '  sleep 120s')
            time.sleep(120)
            return get_t_raw_daily_bar(ticker_list, type, col, date)
        else:
            raw_daily = raw_daily.droplevel(1)
            return raw_daily[col] * 10000


    else:
        date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
        t_raw_daily_bar_dir = FileLocation.raw_daily_dir
        file_path = rf'{t_raw_daily_bar_dir}\{date[:4]}\{date[:6]}\raw_daily_{date}.csv'
        raw_daily_df = pd.read_csv(file_path, index_col=0)
        raw_daily_df.index = raw_daily_df.index.str.split('.', expand=True).get_level_values(0)
        return raw_daily_df.loc[ticker_list, col]


if __name__ == '__main__':
    ProductRetDecomposition('20231211').gen_email()