# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import datetime
import pandas as pd
import smtplib
import tushare as ts

from EmQuantAPI import c

from utils import c_get_trade_dates, transfer_to_jy_ticker
from fq_kline import FqKLine
from email.mime.text import MIMEText

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


def turnover_rate_update_and_confirm(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_turnover_rate_history(today, save_dir=CHOICE_DIR)
    save_path = rf'{CHOICE_DIR}/daily_turnover_rate/{today[:4]}/{today[:6]}/{today}.csv'
    subject, content = turnover_rate_email_content(save_path=save_path)
    send_email(subject, content)


def turnover_rate_email_content(save_path):
    stock_count = None
    anomaly_stock_list = None
    na_stock_list = None
    if os.path.exists(save_path):
        turnover_rate_df = pd.read_csv(save_path, index_col=0)
        subject, stock_count, anomaly_stock_list, na_stock_list = turnover_rate_check(turnover_rate_df)

    else:
        save_path = None
        subject = '[Turnover Rate] File does not exist'

    content = f""""
    Today's turnover rate info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock_list}
    Stocks with turnover rate > 100% or < 0%:
    {anomaly_stock_list}
    """
    return subject, content


def turnover_rate_check(turnover_rate_df):
    stock_count = None
    anomaly_stock_list = None
    na_stock_list = None
    if turnover_rate_df.dropna(how='all').empty:
        subject = '[Turnover Rate] File is empty'
    else:
        stock_count = len(turnover_rate_df.index)
        na_stock_list = turnover_rate_df[turnover_rate_df.isna().any(axis=1)].index.tolist()
        s = turnover_rate_df[(turnover_rate_df > 100) | (turnover_rate_df < 0)].any(axis=1)
        anomaly_stock_list = s[s].index.tolist()
        if len(anomaly_stock_list)>0:
            subject = '[Turnover Rate] File downloaded successfully with anomalous data'
        else:
            subject = '[Turnover Rate] File downloaded successfully'

    return subject, stock_count, anomaly_stock_list, na_stock_list


def c_download_turnover_rate_history(today=None, save_dir=CHOICE_DIR):
    today = time.strftime('%Y%m%d') if today is None else today
    print(f"Downloading historical turnover rate until {today}")
    print("-------------------------------------------------")

    c.start()
    trade_dates = c.tradedates(
        "2022-06-30",
        today,
        "period=1,order=1,market=CNSESH",
    ).Dates
    c.stop()

    date_list = pd.to_datetime(trade_dates).strftime("%Y%m%d").tolist()

    for date in date_list:
        cache_dir = rf'{save_dir}/daily_turnover_rate/{date[:4]}/{date[:6]}'
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, f'{date}.csv')
        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            c_download_daily_turnover_rate(index_ticker='001071', date=date, save_path=save_path)


def c_download_daily_turnover_rate(index_ticker, date, save_path):
    print("Downloading turnover rate")
    print("-------------------------")

    # A share market
    c.start()
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
    a_daily_turnover.to_csv(save_path)




def adjusted_kline_update_and_confirm():
    update_adjusted_kline()
    subject, content = adjusted_kline_email_content(save_path=KLINE_PATH)
    send_email(subject, content)


def adjusted_kline_email_content(save_path):
    today = time.strftime('%Y%m%d')
    if os.path.exists(save_path):
        adjusted_kline = pd.read_pickle(save_path)
        subject, stock_count, na_stock = adjusted_kline_check(adjusted_kline, today)
    else:
        subject = '[adjusted_kline] file is non-existent'
        stock_count = None
        na_stock = None
        save_path = None
    content = f"""
        Today's raw daily bar info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock}
    """
    return subject, content


def adjusted_kline_check(adjusted_kline, today):
    if adjusted_kline.dropna(how='all').empty:
        subject = '[adjusted_kline] file is empty'
        stock_count = 0
        na_stock = []
    else:
        today_kline = adjusted_kline[adjusted_kline.index.get_level_values(0) == today]
        stock_count = len(today_kline)
        na_stock = today_kline[today_kline.isna().any(axis=1)].index.tolist()
        if len(stock_count) < 5000:
            subject = '[adjusted_kline] Data downloaded with alert.'
        else:
            subject = '[adjusted_kline] Data downloaded successfully.'
    return subject, stock_count, na_stock


def update_adjusted_kline():
    FqKLine(
        tushare_dir=TUSHARE_DIR,
        save_path=KLINE_PATH,
    ).gen_qfq_kline()


def raw_daily_bar_update_and_confirm(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    ts_download_raw_daily_bar_history(
        save_dir=TUSHARE_DIR,
        start_date='20220630',
        end_date=today
    )
    save_path = rf'{TUSHARE_DIR}/{today[:4]}/{today[:6]}/raw_daily_{today}.csv'
    subject, content = raw_daily_bar_email_content(save_path)
    send_email(subject, content)


def raw_daily_bar_email_content(save_path):
    if os.path.exists(save_path):
        raw_daily_bar = pd.read_csv(save_path)
        print(f'{save_path} exists.')
        subject, stock_count, na_stock = raw_daily_bar_check(raw_daily_bar)
    else:
        subject = f'[raw_daily_bar] file does not exist.'
        stock_count = 0
        na_stock = []
        save_path = None
    content = f"""
        Today's raw daily bar info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock}
    """
    return subject, content


def raw_daily_bar_check(raw_daily_bar):
    if raw_daily_bar.dropna(how='all').empty:
        subject = '[Raw Daily Bar] No data available yet.'
        save_path = None
    elif len(raw_daily_bar.index) < 5000:
        subject = '[Raw Daily Bar] Data downloaded with alert.'
    else:
        subject = '[Raw Daily Bar] Data downloaded successfully.'

    stock_count = len(raw_daily_bar.index)
    na_stock = raw_daily_bar[raw_daily_bar.isna().any(axis=1)].index.tolist()
    return subject, stock_count, na_stock


def ts_download_raw_daily_bar_history(save_dir, start_date, end_date):
    trade_dates = c_get_trade_dates(start_date, end_date)
    ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

    for date in trade_dates:
        cache_dir = rf'{save_dir}/{date[:4]}/{date[:6]}'
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, f'raw_daily_{date}.csv')

        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            ts_download_raw_daily_bar(save_path, date)


def ts_download_raw_daily_bar(save_path, date):
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
    raw_daily_bar = pro.daily(trade_date=date).set_index('ts_code')
    raw_daily_bar = raw_daily_bar.loc[raw_daily_bar.index.str[-2:] != 'BJ']
    raw_daily_bar.to_csv(save_path)
    print(save_path, 'has downloaded.')


def kc50_weight_update_and_confirm(today=None):
    save_dir = KC50_WEIGHT_DIR
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_kc50_weight(save_dir, today)
    save_path = os.path.join(save_dir, f'{today}.pkl')
    subject, content = kc50_weight_email_content(today, save_path=save_path)
    send_email(subject=subject, content=content)


def kc50_weight_email_content(today, save_path):
    data_name = 'kc50_weight'
    alert = []
    if os.path.exists(save_path):
        df = pd.read_pickle(save_path)
        print(f'{data_name} file exists')
        subject, alert = kc50_weight_check(df)
    else:
        subject = rf'[{data_name}] has not downloaded yet'
    content = f"""
    {data_name} update on {today}.
    Data alert check if any: {alert}
    """
    return subject, content


def kc50_weight_check(df):
    alert = []
    data_name = 'kc50_weight'
    if df.empty:
        subject = rf"[{data_name}]  No data on the downloaded file"
    else:
        if abs(df.WEIGHT.sum()-1) > 0.00001:
            alert.append('Sum of weight is not 1')
        if df.shape[0] != 50:
            alert.append('Number of stocks is not 50')
        if not all(value > 0 for value in df.WEIGHT):
            alert.append('Weight has negative value')
        if len(alert) == 0:
            subject = rf"[{data_name}] has successfully downloaded"
        else:
            subject = rf"[{data_name}] has successfully downloaded with alert"
    return subject, alert


def c_download_kc50_weight(save_dir, date):
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{date}.pkl')

    c_download_index_weight(
        index_ticker='000688.SH',
        date=date,
        save_path=save_path
    )


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

    df.to_pickle(save_path)
    print(f'{save_path}', 'has downloaded.')


def st_list_update_and_confirm(today=None):
    save_path = ST_PATH
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_st_list(today)
    subject, content = st_list_email_content(today, save_path=save_path, stock_default_count=0)
    send_email(subject=subject, content=content)


def st_list_email_content(today, save_path, stock_default_count=0):
    data_name = 'st_list'
    if os.path.exists(save_path):
        df = pd.read_csv(save_path, index_col=0)
        print(f'{data_name} file exists')
        stock_count = len(df[df.index == int(today)])
        if df.empty:
            subject = f"No data on the downloaded {data_name} file"
        elif stock_count > stock_default_count:
            subject = rf"[{data_name}]   today file is updated"
        else:
            subject = rf"[{data_name}]   today file is updated with alert"
        content = rf""""
        {today} {data_name} has been accessed and the info is as follows:
        Download path:
        {save_path}
        Number of stocks included today: {stock_count}

        """
    else:
        subject = f"{data_name} file does not exist"
        content = f""""
        {today} {data_name} has not been accessed successfully
        """
    return subject, content


def c_download_st_list(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_index_list(
        index_ticker='001023',
        date=today,
        save_path=ST_PATH,
    )


def c_download_index_list(index_ticker, date, save_path):
    print(rf"Downloading {index_ticker} list until", date)
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

    all_st_s = all_st_s.str[-2:].str.lower() + all_st_s.str[:6]
    all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
    all_st_s.to_csv(save_path)
    print(rf"{index_ticker} list updated and new .csv file generated ")


def send_email(subject, content):
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
    turnover_rate_update_and_confirm()


