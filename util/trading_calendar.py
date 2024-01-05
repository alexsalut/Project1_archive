import time

import pandas as pd


class TradingCalendar:
    trading_calendar = pd.read_pickle(r'C:\Users\Yz02\Desktop\Project_1\util\trading_calendar2024.pkl').index.tolist()

    def get_n_trading_day(self, date=None, n=1):
        try:
            formatted_date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
            index = self.trading_calendar.index(formatted_date)
            return pd.to_datetime(self.trading_calendar[index + n])
        except Exception as e:
            print(e)

    def check_is_trading_day(self, date=None):
        try:
            formatted_date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
            return formatted_date in self.trading_calendar
        except Exception as e:
            print(e)

    def calculate_trading_weeks(self, start, end):
        trading_calendar = [pd.to_datetime(date) for date in self.trading_calendar]
        selected_trading_calendar = [date for date in trading_calendar if start <= date <= end]
        weeks = [date.strftime('%Y%W') for date in selected_trading_calendar]

        return len(set(weeks))


if __name__ == '__main__':
    TradingCalendar().get_n_trading_day()