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
    def __init__(self,
                 date=None,
                 stock_list=None,
                 option_list=None,
                 ):
        rq.init()
        self.date = time.strftime('%Y%m%d') if date is None else date
        self.last_trading_day = tc().get_n_trading_day(self.date, -1).strftime('%Y%m%d')
        self.stock_list = ['踏浪1号', '盼澜1号', '踏浪3号'] if stock_list is None else stock_list
        self.option_list = ['盼澜1号', '听涟2号'] if option_list is None else option_list
        self.option_tickers = ['10006234', '10006225', '588000.XSHG']  # d（沽-购 + ETF）/ETF
        self.product_fee_dict = {'盼澜1号': {'卖': 0.0616 / 100, '买': 0.0115 / 100},
                                 '踏浪1号': {'卖': 0.063 / 100, '买': 0.013 / 100},
                                 '听涟1号': {'卖': 0.07 / 100, '买': 0.02 / 100},
                                 '踏浪3号': {'卖': 0.06 / 100, '买': 0.01 / 100},
                                 '听涟2号': {'卖': 0.0135 / 100, '买': 0.0635 / 100},
                                 }

    def gen_email(self):
        rq.init()
        table_1, table_2, s_trade_pl_df, _ = self.gen_table()
        styled_1, styled_2, styled_3 = (self.format_table(table_1),
                                        self.format_table(table_2),
                                        self.format_table(s_trade_pl_df, if_percent=False))
        product = '|'.join(set(self.stock_list + self.option_list))
        content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>{product} 收益率分析</b></td>
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
        <p>各产品交易终端股票交易盈亏分析(考虑交易成本)</p>
        <center>{styled_3}</center>
        """

        subject = f'[产品收益率分析] {self.date}'
        Mail().send(subject=subject,
                    body_content=content,
                    receivers=R.department['research'])

    def format_table(self, df, if_percent=True):
        df = df.dropna(how='all')

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
        styled_string = styled_df.to_html(classes='table', escape=False)
        styled_string = styled_string.replace('<table',
                                              '<table style="border-collapse: collapse; border: 1px solid black;"')
        styled_string = styled_string.replace('<tr', '<tr style="border-bottom: 1px solid black;"')
        styled_string = styled_string.replace('<th', '<th style="border-right: 1px solid black;"')
        styled_string = styled_string.replace('<td', '<td style="border-right: 1px solid black;"')
        styled_string = styled_string.replace('nan%', '-')
        styled_string = styled_string.replace('nan', '-')
        return styled_string

    def gen_table(self):
        df, s_trade_df = self.gen_df()
        table_1 = df.loc[['股票收益率1', '股票收益率2', '股票收益误差', '期权收益率1', '期权收益率2', '期权收益误差']]
        table_2_row = [x for x in df.index if x not in table_1.index]
        table_2 = df.loc[table_2_row, :]
        return table_1, table_2, s_trade_df, df

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
        stock_name_dict = self.get_stock_name(s_trade_pl_df.index)
        s_trade_pl_df['name'] = s_trade_pl_df.index.map(stock_name_dict)
        s_trade_pl_df = s_trade_pl_df.set_index('name', drop=True)
        s_trade_pl_df.index.name = None
        return df, s_trade_pl_df

    @staticmethod
    def get_stock_name(ticker_list):
        rq.init()
        stock_lst = [ticker for ticker in ticker_list if not ticker.startswith('1')]
        new_ticker_list = rq.id_convert(stock_lst)

        stock_info = rq.instruments(new_ticker_list)
        stock_name_dict = {stock.order_book_id[:6]: stock.symbol for stock in stock_info}
        return stock_name_dict

    def get_kc50_ret(self, date):
        rq.init()
        rq_data = rq.get_price_change_rate('000688.XSHG', start_date=date, end_date=date)
        if rq_data is None:
            print('No data for', '000688.XSHG', date, '  sleep 120s')
            time.sleep(120)
            return self.get_kc50_ret(date)
        else:
            return rq_data.iloc[0, 0]

    def get_ret_decomposition(self, product):
        product_dict = {}
        asset_col = '总资产' if product == '踏浪3号' else '股票资产总值'
        stock_asset = get_product_record(product, asset_col, self.last_trading_day)
        trade_df, net_trade_pl, gross_trade_pl, trade_fee = self.get_trade_pl(product, 'Credit',
                                                                              self.product_fee_dict[product])
        gross_trade_rate = gross_trade_pl / stock_asset
        trade_fee_rate = trade_fee / stock_asset
        net_trade_rate = net_trade_pl / stock_asset
        hold_rate = self.get_hold_pl(product, 'Credit') / stock_asset

        pl_col = '当日盈亏' if product == '踏浪3号' else '股票盈亏'
        product_dict['股票收益率1'] = get_product_record(product, pl_col, self.date) / stock_asset
        product_dict['股票交易收益率(毛)'] = gross_trade_rate
        product_dict['股票交易费率'] = trade_fee_rate
        product_dict['股票持有收益率'] = hold_rate
        product_dict['股票收益率2'] = net_trade_rate + hold_rate
        product_dict['股票收益误差'] = product_dict['股票收益率1'] - product_dict['股票收益率2']

        product_dict['monitor组合涨幅'] = get_monitor_data(product, self.date)

        product_dict['股票权重配置误差'] = product_dict['股票持有收益率'] - product_dict['monitor组合涨幅']

        if product in self.option_list:
            op_trade_pl = self.get_trade_pl(product, 'Option')[1]
            product_dict['期权收益率1'] = get_product_record(product, '期权盈亏', self.date) / stock_asset
            product_dict['期权交易收益率'] = op_trade_pl / stock_asset
            product_dict['期权持有收益率'] = self.get_hold_pl(product, 'Option') / stock_asset
            product_dict['期权收益率2'] = product_dict['期权交易收益率'] + product_dict['期权持有收益率']
            product_dict['期权收益误差'] = product_dict['期权收益率1'] - product_dict['期权收益率2']
            product_dict['指数收益率'] = self.get_kc50_ret(self.date)
            product_dict['期权基差'], etf_ret = self.get_base_diff()
            product_dict['ETF跟踪误差'] = etf_ret - product_dict['指数收益率']
            product_dict['期权权重配置误差'] = (product_dict['期权持有收益率']
                                                + product_dict['指数收益率']
                                                + product_dict['ETF跟踪误差']
                                                - product_dict['期权基差'])

        stock_trade_pl = trade_df['净盈亏'].sort_values(ascending=False)
        return product_dict, stock_trade_pl.rename(product)

    def get_trade_pl(self, product, account_type, fee_dict=None):
        sep = '*' * 32
        print(fr'{sep}Generating {product} {account_type} Trading P&L {sep}')
        trade_df = get_transaction_df(product, account_type, self.date, fee_dict)
        trade_df.index = trade_df.index.astype(str)
        ticker_list = trade_df.index.astype(str).tolist()
        if ticker_list:
            new_trade_df = pd.concat(
                [trade_df,
                 get_t_raw_daily_bar(ticker_list=ticker_list, ticker_type=account_type, col='close', date=self.date)],
                axis=1)
            new_trade_df['毛盈亏'] = new_trade_df['成交数量'] * new_trade_df['close'] + new_trade_df['成交金额']
            new_trade_df['净盈亏'] = new_trade_df['成交数量'] * new_trade_df['close'] + new_trade_df['发生金额']
            net_pl = new_trade_df['净盈亏'].sum()
            gross_pl = new_trade_df['毛盈亏'].sum()
            fees = new_trade_df['交易费'].sum()
            return new_trade_df, net_pl, gross_pl, fees

        else:
            return trade_df, 0, 0, 0

    def get_hold_pl(self, product, product_type):
        sep = '*' * 32
        print(fr'{sep}Generating {product} {product_type} Holding P&L {sep}')
        position_s = get_position_s(account=product, account_type=product_type, date=self.last_trading_day)
        position_s.index = position_s.index.astype(str)
        ticker_list = position_s.index.astype(str).tolist()
        close = get_t_raw_daily_bar(ticker_list=ticker_list,
                                    ticker_type=product_type,
                                    col=['close', 'prev_close'],
                                    date=self.date)
        hold_pl = (close['close'] - close['prev_close']).mul(position_s).sum()
        print(f'{product} {product_type} Holding P&L(%) is {hold_pl}')
        return hold_pl

    def get_base_diff(self):
        option_tickers = self.option_tickers
        df = get_t_raw_daily_bar(
            ticker_list=option_tickers,
            ticker_type='Option',
            col=['close', 'prev_close'],
            date=self.date
        )
        s = df['close'] - df['prev_close']
        base_diff = (s[option_tickers[0]] - s[option_tickers[1]] + s[option_tickers[2]]) / df.loc[
            option_tickers[2], 'prev_close']
        return base_diff, s[option_tickers[2]] / df.loc[option_tickers[2], 'prev_close']


def get_t_raw_daily_bar(ticker_list, ticker_type, col=None, date=None):
    """
    Get daily bar data for stock or option
    :param ticker_list:
    :param ticker_type:
    :param col: str or list
    :param date:
    :return:
    """
    col = 'close' if col is None else col
    if ticker_type == 'Option':
        rq.init()
        raw_daily = rq.get_price(ticker_list, start_date=date, end_date=date)
        if raw_daily is None:
            print('No data for', ticker_list, date, '  sleep 120s')
            time.sleep(120)
            return get_t_raw_daily_bar(ticker_list, ticker_type, col, date)
        else:
            raw_daily = raw_daily.droplevel(1)
            raw_daily['pct_chg'] = (raw_daily['close'] / raw_daily['prev_close'] - 1) * 100
            return raw_daily[col] * 10000

    else:
        date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
        t_raw_daily_bar_dir = FileLocation.raw_daily_dir
        file_path = rf'{t_raw_daily_bar_dir}\{date[:4]}\{date[:6]}\raw_daily_{date}.csv'
        raw_daily_df = pd.read_csv(file_path, index_col=0)
        raw_daily_df.index = raw_daily_df.index.str.split('.', expand=True).get_level_values(0)
        raw_daily_df = raw_daily_df.rename(columns={'pre_close': 'prev_close'})
        non_stock_tickers = [ticker for ticker in ticker_list if
                             ticker not in raw_daily_df.index and not ticker.startswith('1')]
        stock_tickers = [ticker for ticker in ticker_list if
                         ticker not in non_stock_tickers and not ticker.startswith('1')]
        stock_df = raw_daily_df.loc[stock_tickers, col]

        if len(non_stock_tickers) == 0:
            return stock_df
        else:
            tickers = [ticker for ticker in non_stock_tickers if not ticker.startswith('1')]
            ticker_string = ','.join(tickers)
            rq.init()
            ticker_string = rq.id_convert(ticker_string)
            price = rq.get_price(ticker_string, start_date=date, end_date=date, fields=col)[col].droplevel(1)
            price.index = price.index.str.split('.', expand=True).get_level_values(0)
            price_s = pd.concat([stock_df, price], axis=0)
            return price_s
