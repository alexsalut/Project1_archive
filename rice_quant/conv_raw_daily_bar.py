import time
import os
import glob
import pandas as pd
import rqdatac as rq

rq.init()

def download_raw_daily_bar(date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    dir = r'C:\Users\Yz02\Desktop\Data\conv_raw_daily_bar\convertible_raw_daily_bar\2024'
    os.makedirs(dir, exist_ok=True)

    df = get_conv_raw_daily_bar(date)
    file = os.path.join(dir, f'raw_daily_bar_{date}.csv')
    df.to_csv(file)
    print(f'{date} raw daily bar saved')

    ticker_list = df.index.tolist()
    df['pct_chg'] = rq.get_price_change_rate(ticker_list, start_date=date, end_date=date).iloc[0]
    new_file = file.replace('raw', 'adjusted')
    df.to_csv(new_file)
    print(f'{new_file} adjusted daily bar saved')

def get_conv_raw_daily_bar(date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    conv_s = get_conv_list(date)
    conv_list = conv_s.index.tolist()
    conv_raw_daily_bar = rq.get_price(conv_list, start_date=date, end_date=date,
                                      fields=['open', 'volume', 'prev_close',  'low', 'high', 'total_turnover', 'close', ])

    conv_raw_daily_bar = conv_raw_daily_bar.rename(columns={'total_turnover': 'volume'})
    conv_raw_daily_bar = conv_raw_daily_bar.droplevel(1, axis=0)

    conv_raw_daily_pair = pd.concat([conv_s, conv_raw_daily_bar], axis=1).dropna()
    conv_raw_daily_pair.index.name = 'ticker'
    return conv_raw_daily_pair

def get_conv_list(date=None):
    date =  time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    conv_s = rq.all_instruments(type='Convertible', date=date)[['order_book_id', 'stock_code']].set_index('order_book_id').iloc[:,0]
    return conv_s



if __name__ == '__main__':
    download_raw_daily_bar('20240229')