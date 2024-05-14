# -*- coding: utf-8 -*-
# @Time    : 2023/3/7 15:01
# @Author  : Youwei Wu
# @File    : performance.py
# @Software: PyCharm

import pandas as pd
import matplotlib.pyplot as plt


class Performance:

    def evaluate(self, ret_s, x_label=None, title=None, freq='daily', save_path=None, ax=None):
        nav_s = (ret_s + 1).cumprod()
        nav_s /= nav_s.iat[0]
        if ax is None:
            fig, ax1 = plt.subplots(figsize=(12, 8))
        else:
            ax1 = ax
        # nav_s.plot(grid=True, figsize=(12, 8))
        ax1.plot(nav_s)
        n = int(len(nav_s) / 6)
        ax1.text(
            x=nav_s.index[-n],
            y=(nav_s.max() - nav_s.min())/3+nav_s.min(),
            s=get_eval_txt(ret_s, freq),
        )

        ax1.text(
            x=nav_s.index[4],
            y=(nav_s.max() - nav_s.min())*0.4+nav_s.min(),
            s=str(self.display_yearly_perf(ret_s, freq)),
        )
        dd = nav_s / nav_s.cummax()
        ax1.plot(dd)
        ax1.grid(True)

        # dd_pct = 0.05
        # ax1.plot([nav_s.index[0], nav_s.index[-1]], [1-dd_pct, 1-dd_pct], c='r', linestyle='--')
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.xticks(rotation=45)
        ax1.set_xlabel(x_label)
        ax1.set_title(title)
        plt.tight_layout()
        if ax is None:
            plt.savefig(save_path)
            plt.show()

    def display_yearly_perf(self, ret_s, freq):
        ret_s.index = pd.to_datetime(ret_s.index)
        perf_df = ret_s.groupby(ret_s.index.year).apply(
            self.eval_perf, freq).unstack()
        perf_df.index.name = 'year'
        display_df = perf_df.round(2).astype({'TradeDays': int})
        if freq == 'weekly':
            del display_df['D_WinRate']
            del display_df['TradeDays']

        print('\nYearly Performance\n'
              '------------------\n')
        print(display_df)
        return display_df

    @staticmethod
    def eval_perf(ret_s, freq):
        multiple = 52 if freq == 'weekly' else 250
        nav_s = (ret_s + 1).cumprod()
        dd = nav_s / nav_s.cummax() - 1
        n_days = len(ret_s)

        weekly_ret_s = nav_s.resample('W').last().pct_change().dropna()
        weekly_win_rate = len(weekly_ret_s[weekly_ret_s > 0]) / (len(weekly_ret_s[weekly_ret_s != 0]) + 1e-6)

        perf_dict = {
            'AnRev(%)': (nav_s.iat[-1] - 1) * 100 * multiple / len(nav_s),
            'AnStd(%)': (ret_s.std() * pow(multiple, 0.5)) * 100,
            'Mdd(%)': dd.min() * 100,
            'TradeDays': n_days,
            'D_WinRate': (len(ret_s[ret_s > 0]) / n_days),
            'W_WinRate': weekly_win_rate,


        }
        perf_dict['Sharpe'] = perf_dict['AnRev(%)'] / perf_dict['AnStd(%)']
        return pd.Series(perf_dict)


def get_eval_txt(ret_s, freq, if_text=True):
    eval_s = eval_perf(ret_s, freq).round(2)
    print(eval_s)

    nav_s = (ret_s + 1).cumprod()
    dd = nav_s / nav_s.cummax() - 1

    # mdd
    mdd_end_date = dd.idxmin().strftime('%Y%m%d')
    tmp_dd = dd.loc[:mdd_end_date]
    mdd_start_date = tmp_dd[tmp_dd == 0].index[-1].strftime('%Y%m%d')
    eval_s.loc['MddStartDate'] = mdd_start_date
    eval_s.loc['MddEndDate'] = mdd_end_date

    # ldd
    new_high_points = dd[dd == 0]
    dd_days = new_high_points.index[1:] - new_high_points.index[:-1]
    ldd_days = dd_days.max()
    ldd_index = list(dd_days).index(ldd_days)
    eval_s.loc['LddStartDate'] = new_high_points.index[ldd_index].strftime('%Y%m%d')
    eval_s.loc['LddEndDate'] = new_high_points.index[ldd_index + 1].strftime('%Y%m%d')

    eval_txt = str(eval_s).split('\nName')[0]
    if if_text:
        return eval_txt
    else:
        return eval_s


def eval_perf(ret_data, freq='daily', cumprod=True):
    if isinstance(ret_data, pd.Series):
        ret_df = ret_data.to_frame()
    else:
        ret_df = ret_data.copy()

    assert freq in ['daily', 'weekly']
    param = 52 if freq == 'weekly' else 250

    # sharpe
    if cumprod:
        nav_df = (ret_df + 1).cumprod()
    else:
        nav_df = ret_df.cumsum() + 1

    an_rev = nav_df.iloc[-1] ** (param / len(ret_df)) - 1
    an_std = ret_df.std() * pow(param, 0.5)
    sharpe = an_rev / an_std

    mdd = (nav_df / nav_df.cummax() - 1).min()
    sortino = cal_sortino(ret_df, param)
    mar = an_rev / abs(mdd)
    skew = ret_df.skew()

    daily_win_rate = ret_df.apply(lambda x: len(x[x > 0]) / (len(x[x != 0]) + 1e-8))
    weekly_win_rate = get_win_rate(nav_df, period="W")
    monthly_ret = get_win_rate(nav_df, period="M")

    keys = [
        'AnRev(%)', 'AnStd(%)', 'Mdd(%)',
        'Sharpe', 'Sortino', 'MAR', 'Skewness',
        'DailyWinRate', 'WeeklyWinRate', 'MonthlyWinRate',
    ]
    indicators = [
        an_rev, an_std, mdd,
        sharpe, sortino, mar, skew,
        daily_win_rate, weekly_win_rate, monthly_ret,
    ]
    eval_df = pd.concat(indicators, keys=keys, axis=1).T
    eval_df.iloc[:3] *= 100

    if freq == 'weekly':
        eval_df = eval_df.drop('DailyWinRate')

    if isinstance(ret_data, pd.Series):
        return eval_df[eval_df.columns[0]]
    else:
        return eval_df


def get_win_rate(nav_df, period):
    ret_df = nav_df.resample(period).last().pct_change().dropna()
    win_rate = ret_df.apply(lambda x: len(x[x > 0]) / (len(x[x != 0])))
    return win_rate


def cal_sortino(ret_df, param):
    nav_df = (ret_df + 1).cumprod()
    an_rev = nav_df.iloc[-1] ** (param / len(ret_df)) - 1
    # downside risk
    dn_ret_df = ret_df[ret_df < 0].fillna(0)
    dn_risk = (dn_ret_df ** 2).mean() ** 0.5  # 下行风险，收益平方均值的标准差
    an_dn_risk = dn_risk * pow(param, 0.5)

    sortino = an_rev / an_dn_risk
    return sortino
