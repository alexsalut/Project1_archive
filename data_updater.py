# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import datetime
import pytz

import tushare as ts
import pandas as pd
import smtplib
from EmQuantAPI import c

from utils import c_get_trade_dates, transfer_to_jy_ticker
from fq_kline import FqKLine
from email.mime.text import MIMEText
# from script.preprocess.fq_kline import FqKLine
# from script.product.utils import ProductPath, c_get_trade_dates, transfer_to_jy_ticker

TUSHARE_DIR = "C:/Users/Yz02/Desktop/Data/Tushare"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
SAVE_PATH = "C:/Users/Yz02/Desktop/Data/Save/qfq_price.pkl"


def update_confirm_adjusted_kline():
    update_adjusted_kline()
    update_email_confirmation(
        'update_confirm_adjusted_kline',
        'update_confirm_adjusted_kline'
    )


def update_adjusted_kline():
    FqKLine(
        tushare_dir=TUSHARE_DIR,
        save_path=SAVE_PATH,
    ).gen_qfq_kline()


def update_confirm_raw_daily_bar(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    ts_download_raw_daily_bar(today)
    update_email_confirmation(
        'update_confirm_raw_daily_bar',
        'update_confirm_raw_daily_bar'
    )


def ts_download_raw_daily_bar(today):
    ts_download_history(
        start_date='20220630',
        end_date=today,
        save_dir=TUSHARE_DIR,
    )


def ts_download_history(start_date, end_date, save_dir):
    trade_dates = c_get_trade_dates(start_date, end_date)
    ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

    for date in trade_dates:
        cache_dir = rf'{save_dir}/{date[:4]}/{date[:6]}'
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, f'raw_daily_{date}.csv')

        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            ts_download_daily(date, save_path)


def ts_download_daily(date, save_path):
    """
    Returns
    -------
    daily_bar: pd.DataFrame

        名称	类型	描述
        ts_code	str	股票代码
        trade_date	str	交易日期
        open	float	开盘价
        high    float	最高价
        low     float	最低价
        close	float	收盘价
        pre_close	float	昨收价(前复权)
        change	float	涨跌额
        pct_chg	float	涨跌幅
        vol	    float	成交量 （手）
        amount	float	成交额 （千元）
    """
    pro = ts.pro_api()
    daily_bar = pro.daily(trade_date=date).set_index('ts_code')
    if daily_bar.empty:
        print('No data:', date)
    else:
        daily_bar = daily_bar.loc[daily_bar.index.str[-2:] != 'BJ']
        daily_bar.to_csv(save_path)
        print(save_path, 'has downloaded.')


def update_confirm_kc50_weight(today=None):
    c_download_kc50_weight(today)
    update_email_confirmation('update_confirm_kc50_weight',
                              "update_confirm_kc50_weight")


def c_download_kc50_weight(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    save_dir = rf'{CHOICE_DIR}/kc50_weight'
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{today}.pkl')

    if os.path.exists(save_path):
        print(save_path, 'has existed.')
    else:
        c_download_index_weight(index_ticker='000688.SH',
                                date=today,
                                save_path=save_path)


def c_download_index_weight(index_ticker, date, save_path):
    print("Downloading Index Composition Weight")
    print("-----------------------------------")
    jy_ticker = transfer_to_jy_ticker([index_ticker])[0]

    c.start()
    df = c.ctr(
        "INDEXCOMPOSITION",
        "SECUCODE,WEIGHT",
        f"IndexCode={index_ticker},EndDate={date},ispandas=1",
    )
    c.stop()

    if df.empty:
        print('No data:', date)
    else:
        df.to_pickle(save_path)
        print(f'{save_path}', 'has downloaded.')


def update_confirm_st_list(today=None):
    c_download_st_list(today)
    update_email_confirmation('update_confirm_st_list',
                              'update_confirm_st_list')


def c_download_st_list(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    save_dir = rf'{CHOICE_DIR}/st_list'
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'st_list.csv')

    if os.path.exists(save_path):
        print(save_path, 'has existed.')
    else:
        c_download_index_list(
            index_ticker='001023',
            date=today,
            save_path=save_path,
        )


def c_download_index_list(index_ticker, date, save_path):
    print("Downloading st list until", date)
    print("----------------------------------")
    start_date = "2020-08-31"
    c.start()
    trade_dates = c.tradedates(
        start_date,
        date,
        "period=1,order=1,market=CNSESH",
    ).Dates

    all_st_list = []
    for date in trade_dates:
        st_list = c.sector(index_ticker, date).Codes
        tmp_st_s = pd.Series(st_list, index=[date] * len(st_list))
        all_st_list.append(tmp_st_s)
    all_st_s = pd.concat(all_st_list)
    c.stop()

    if all_st_s.empty:
        print('No data:', date)
    else:
        all_st_s = all_st_s.str[-2:].str.lower() + all_st_s.str[:6]
        all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
        all_st_s.to_csv(save_path)
        print("ST list updated and new .csv file generated ")


def update_confirm_daily_turnover(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    save_dir = rf'{CHOICE_DIR}/daily_turnover_rate/{today[:4]}/{today[:6]}'
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{today}.csv')

    a_daily_turnover = c_download_daily_turnover_rate(
        index_ticker='001071',
        date=today,
        save_path=save_path
    )
    if a_daily_turnover.dropna(how='all').empty:
        subject = '[Turnover Rate]No data available yet'
        save_path = None
    else:
        subject = '[Turnover Rate]Data downloaded successfully '

    stock_count = len(a_daily_turnover.index)
    na_stock = a_daily_turnover[a_daily_turnover.isna().any(axis=1)].index.tolist()
    na_stock_count = len(na_stock)

    email_turnover_confirmation(subject, save_path, stock_count, na_stock_count, na_stock)


def email_turnover_confirmation(subject, save_path, stock_count, na_stock_count, na_stock):
    content = f""""
    Today's turnover rate has been accessed on Choice and the info is as follows:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Number of stocks with missing values: {na_stock_count} 
    Details(Code) of stocks with missing values:
    {na_stock}
    """
    update_email_confirmation(subject=subject, content=content)


def c_download_all_daily_turnover_rate(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    print(f"Downloading historical turnover rate until {today}")
    print("-------------------------------------------------")
    today = time.strftime('%Y%m%d') if today is None else today

    start_date = "2022-06-30"
    c.start()
    trade_dates = c.tradedates(
        start_date,
        today,
        "period=1,order=1,market=CNSESH",
    ).Dates
    c.stop()

    date_list = pd.to_datetime(trade_dates).strftime("%Y%m%d").tolist()

    for date in date_list:
        save_dir = rf'{CHOICE_DIR}/daily_turnover_rate/{date[:4]}/{date[:6]}'
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f'{date}.csv')
        c_download_daily_turnover_rate(index_ticker='001071', date=date, save_path=save_path)


def c_download_daily_turnover_rate(index_ticker, date, save_path):
    if os.path.exists(save_path):
        a_daily_turnover = pd.read_csv(save_path, index_col=0)
        print(f'{save_path}', 'has existed.')
        return a_daily_turnover

    else:
        print("Downloading turnover rate")
        print("-------------------------")

        c.start()

        # A share market
        stock_list = c.sector(index_ticker, date).Codes
        filter_list = [x for x in stock_list if x[-2:] in ['SH', 'SZ']]
        a_daily_turnover = c.css(
            filter_list,
            "TURN,FREETURNOVER",
            f"TradeDate={date}, isPandas=1",
        )
        c.stop()
        a_daily_turnover.index = transfer_to_jy_ticker(a_daily_turnover.index)
        a_daily_turnover.drop(columns=['DATES'], inplace=True)
        # stock_count = len(a_daily_turnover.index)
        # na_stock = a_daily_turnover.isna().T.any()[a_daily_turnover.isna().T.any() == True].index.tolist()
        # na_stock_count = a_daily_turnover.isna().T.any().sum()

        if a_daily_turnover.dropna(how='all').empty:
            print('No data available yet:', date)
        else:
            a_daily_turnover.to_csv(save_path)
            print(f'{save_path}', 'has downloaded.')
        return a_daily_turnover


def update_email_confirmation(subject, content):
    # 配置第三方 SMTP 服务
    host = "smtp.163.com"
    mail_user = "13671217387@163.com"
    mail_pwd = 'YDIDWQVKNSKJHGYT'

    # 配置发送方、接收方信息
    sender = '13671217387@163.com'
    receivers = ['zhou.sy@yz-fund.com.cn', 'wu.yw@yz-fund.com.cn']

    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = sender  # 发送者
    message['To'] = ','.join(receivers)  # 接收者
    message['Subject'] = subject
    try:
        smtpObj = smtplib.SMTP()  # 建立和SMTP邮件服务器的连接
        smtpObj.connect(host, 25)  # 25 为 SMTP 端口号
        smtpObj.set_debuglevel(1)
        smtpObj.login(mail_user, mail_pwd)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print(subject, '邮件发送成功')
        smtpObj.quit()

    except smtplib.SMTPException as e:
        print(e)


if __name__ == '__main__':
    update_confirm_daily_turnover('20230803')










