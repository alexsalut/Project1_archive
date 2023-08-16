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
    s = a_daily_turnover[(a_daily_turnover > 100) | (a_daily_turnover < 0)].any(axis=1)
    anomaly_stock = s[s].index.tolist()
    na_stock = a_daily_turnover[a_daily_turnover.isna().any(axis=1)].index.tolist()

    email_turnover_confirmation(subject, save_path, stock_count, na_stock, anomaly_stock)




def email_turnover_confirmation(subject, save_path, stock_count, na_stock, anomaly_stock):
    content = f""""
    Today's turnover rate has been accessed on Choice and the info is as follows:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock}
    Stocks with turnover rate > 100% or < 0%:
    {anomaly_stock}
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
