#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 8:44
# @Author  : Suying
# @Site    : 
# @File    : rongquan_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import rqdatac as rq
import seaborn as sns

def check_instant_rongquan(product='nongchao2'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')
    yuequan_df['记录日期'] = pd.to_datetime(yuequan_df['记录日期'].astype(str).str[:8])
    yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
    yuequan_df['证券代码'] = yuequan_df['证券代码'].astype(str).str.zfill(6)

    rongquan_df = pd.read_pickle(rf'data\tmp\{product}_rongquan_volume.pkl')
    rongquan_dict = dict()
    for date in rongquan_df.index.get_level_values(0):
        daily_rongquan = rongquan_df.loc[date]
        daily_rongquan.index = daily_rongquan.index.astype(int).astype(str).str.zfill(6)
        daily_yuequan = yuequan_df[(yuequan_df['记录日期'] == date)&(yuequan_df['生效日期'] <= date)]


        col = '合约数量' if product == 'nongchao2' else '约定合约数量'
        daily_yuequan = daily_yuequan.groupby('证券代码')[col].sum()
        new_df = pd.concat([daily_rongquan, daily_yuequan], axis=1).fillna(0)
        new_df['是否实时'] = (new_df['融券数量'] > new_df[col]).astype(int)
        num_instant_rongquan = new_df['是否实时'].sum()
        num_yuequan = len(daily_rongquan) - num_instant_rongquan
        rongquan_dict[date] = [num_yuequan, num_instant_rongquan]

    type_df = pd.DataFrame(rongquan_dict).T.rename(columns={0: '预约融券', 1: '实时融券'})
    plot_instant_rongquan(type_df, suffix)

def plot_instant_rongquan(type_df, suffix):
    plt.stackplot(type_df.index, type_df.T, labels=type_df.columns)
    plt.title(f'{suffix}每日实时融券和预约融券只数')
    plt.xlabel('日期')
    plt.ylabel('只数')
    plt.grid()
    plt.text(type_df.index[int(len(type_df)*0.5)],
             type_df.max().max()*0.5,
             f'每日融券最大只数: {type_df.sum(axis=1).max()}\n'
             f'每日融券最小只数: {type_df.sum(axis=1).min()}\n'
                f'每日融券平均只数: {type_df.sum(axis=1).mean():.2f}\n'
                f'每日融券只数中位数: {type_df.sum(axis=1).median():.0f}\n'
             f'每日预约融券只数平均占比: {(type_df["预约融券"]/type_df.sum(axis=1)).mean():.2%}\n'
             )
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.legend()
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}每日约券和即时融券只数.png')
    plt.show()



def plot_daily_contract_interest_rate():
    nongchao1 = daily_contract_interest_rate('nongchao1').sort_index()
    nongchao2 = daily_contract_interest_rate('nongchao2').sort_index()

    fig, ax = plt.subplots()
    plt.plot(nongchao1.index, nongchao1, label='弄潮1号')
    plt.plot(nongchao2.index, nongchao2, label='弄潮2号')
    plt.title('每日预约融券合约利率')
    plt.xlabel('日期')
    plt.ylabel('利率')
    plt.text(nongchao1.index[int(len(nongchao1)*0.5)],
                nongchao1.max(),
                f'弄潮1号平均利率: {nongchao1.mean():.4%}\n'
                f'弄潮2号平均利率: {nongchao2.mean():.2%}\n')
    plt.grid()
    plt.legend()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\每日约券合约利率.png')
    plt.show()

def daily_contract_interest_rate(product='nongchao1'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')
    yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
    if product == 'nongchao1':
        contract_s = yuequan_df.groupby('生效日期')['费用比率'].mean()

    else:
        contract_s = yuequan_df.groupby('生效日期')['融券占用利率'].mean()

    return contract_s.rename(suffix)




def contract_interest_rate(product='nongchao2'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')

    if product == 'nongchao1':
        contract_s = yuequan_df.groupby('合约编号')['费用比率'].max()

    else:
        contract_s = yuequan_df.groupby('头寸合约编号')['融券占用利率'].max()

    plot_contract_interest_rate(contract_s, suffix)

def plot_contract_interest_rate(early_days, suffix):
    sns.histplot(early_days, bins=10, kde=True)
    plt.title(f'{suffix}每笔预约融券合约利率分布')
    plt.xlabel('合约利率')
    plt.ylabel('频数')
    plt.text(early_days.max()*0.7,
             500,
             f'合约数量: {early_days.count()}\n'
             f'平均融券利率: {early_days.mean():.4f}\n'
             f'融券利率中位数: {early_days.median()}\n'
                f'最大融券利率: {early_days.max()}\n'
                f'最小融券利率: {early_days.min()}\n'
                )
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}约券合约利率.png')
    plt.show()

def contract_transaction_analysis(product='nongchao2'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')
    if product == 'nongchao1':
        contract_s = yuequan_df.groupby('合约编号')['约定合约金额'].max()
    else:
        contract_s = yuequan_df.groupby('头寸合约编号')['合约金额'].max()
    plot_contract_transaction(contract_s, suffix)

def plot_contract_transaction(early_days, suffix):
    sns.histplot(early_days, bins=50, kde=True)
    plt.title(f'{suffix}每笔预约融券合约金额分布')
    plt.xlabel('合约金额')
    plt.ylabel('频数')
    plt.text(early_days.max()*0.3,
             500,
             f'合约数量: {early_days.count()}\n'
             f'平均合约金额: {early_days.mean():.2f}\n'
             f'合约金额中位数: {early_days.median()}\n'
                f'最大合约金额: {early_days.max()}\n'
                f'最小合约金额: {early_days.min()}\n'
                )
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}约券合约金额分布.png')
    plt.show()

def hold_period_analysis(product='nongchao2'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')

    if product == 'nongchao1':
        yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
        yuequan_df['到期日期'] = pd.to_datetime(yuequan_df['到期日期'].astype(str))
        yuequan_df['记录日期'] = pd.to_datetime(yuequan_df['记录日期'].astype(str))
        yuequan_df['持有天数'] = (yuequan_df['记录日期'] - yuequan_df['生效日期']).dt.days + 1
        contract_df = yuequan_df.groupby('合约编号')[['生效日期','持有天数']].agg({'生效日期': 'first', '持有天数': 'max'})

    else:
        yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
        yuequan_df['到期日期'] = pd.to_datetime(yuequan_df['合约到期日'].astype(str))
        yuequan_df['记录日期'] = yuequan_df['记录日期'].astype(str).str[:8]
        yuequan_df['记录日期'] = pd.to_datetime(yuequan_df['记录日期'])

        yuequan_df['持有天数'] = (yuequan_df['记录日期'] - yuequan_df['生效日期']).dt.days + 1
        contract_df = yuequan_df.groupby('头寸合约编号')[['生效日期','持有天数']].agg({'生效日期': 'first', '持有天数': 'max'})

    plot_hold_days(contract_df['持有天数'], suffix)

def plot_hold_days(early_days, suffix):
    sns.histplot(early_days, bins=25, kde=True)
    plt.title(f'{suffix}约券合约持有天数分布')
    plt.xlabel('持有天数')
    plt.ylabel('频数')
    plt.text(early_days.max()*0.5,
             500,
             f'合约数量: {early_days.count()}\n'
             f'平均持有天数: {early_days.mean():.2f}\n'
                f'最大持有天数: {early_days.max()}\n'
                f'最小持有天数: {early_days.min()}\n'
                f'持有天数中位数: {early_days.median()}')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}约券合约持有天数分布.png')
    plt.show()

def repay_early_analysis(product='nongchao2'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    yuequan_df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')

    if product == 'nongchao1':
        yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
        yuequan_df['到期日期'] = pd.to_datetime(yuequan_df['到期日期'].astype(str))
        yuequan_df['记录日期'] = pd.to_datetime(yuequan_df['记录日期'].astype(str))
        yuequan_df['剩余天数'] = (yuequan_df['到期日期'] - yuequan_df['记录日期']).dt.days
        contract_df = yuequan_df.groupby('合约编号')[['生效日期','剩余天数']].agg({'生效日期': 'first', '剩余天数': 'min'})
        contract_df['提前天数'] = contract_df['剩余天数']

    else:
        yuequan_df['生效日期'] = pd.to_datetime(yuequan_df['生效日期'].astype(str))
        yuequan_df['到期日期'] = pd.to_datetime(yuequan_df['合约到期日'].astype(str))
        yuequan_df['记录日期'] = yuequan_df['记录日期'].astype(str).str[:8]
        yuequan_df['记录日期'] = pd.to_datetime(yuequan_df['记录日期'])
        yuequan_df['剩余天数'] = (yuequan_df['到期日期'] - yuequan_df['记录日期']).dt.days
        contract_df = yuequan_df.groupby('头寸合约编号')[['生效日期', '剩余天数']].agg(
            {'生效日期': 'first', '剩余天数': 'min'})
        contract_df['提前天数'] = contract_df['剩余天数']
    plot_repay_early_days(contract_df['提前天数'], suffix)

def plot_repay_early_days(early_days, suffix):
    # plot the distribution of early repayment days
    plt.hist(early_days, bins=10)
    plt.title(f'{suffix}提前还券天数分布')
    plt.xlabel('提前还券天数')
    plt.ylabel('频数')
    plt.text(early_days.max()*0.5,
             1000,
             f'平均提前还券天数: {early_days.mean():.2f}\n'
                f'最大提前还券天数: {early_days.max()}\n'
                f'最小提前还券天数: {early_days.min()}\n'
                f'提前还券天数中位数: {early_days.median()}')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}提前还款天数分布.png')
    plt.show()

def get_contract_days(product='nongchao1'):
    suffix = '弄潮1号' if product == 'nongchao1' else '弄潮2号'
    df = pd.read_pickle(rf'data\{product}_yuequan_df.pkl')
    df['生效日期'] = pd.to_datetime(df['生效日期'].astype(str))

    bianhao_col = '合约编号' if '合约编号' in df.columns else '头寸合约编号'
    effective_days_col = '约定合约期限' if '约定合约期限' in df.columns else '期限天数'


    contract_days = df.groupby(bianhao_col)[[effective_days_col,'生效日期']].first()
    contract_days['约定合约期限'] = contract_days[effective_days_col].astype(int)
    plot_contract_days(contract_days['约定合约期限'], suffix)




    # contract_stats = contract_days.groupby('生效日期')[effective_days_col].apply(lambda x: x.describe()).unstack()
    #
    #
    # plot_cols = {
    #              'mean': '平均合约期限(天)',
    #              'min': '最小合约期限(天)',
    #              'max': '最大合约期限(天)',}
    # contract_stats = contract_stats.rename(columns=plot_cols)
    # contract_stats = reindex_df(contract_stats).fillna(0)
    # contract_stats.index = [date.strftime('%Y-%m-%d') for date in contract_stats.index]
    #
    # fig, ax = plt.subplots()
    # for key, value in plot_cols.items():
    #     plt.plot(contract_stats.index, contract_stats[value], label=value)
    # plt.title(f'{suffix}每日约定合约期限统计')
    # plt.xlabel('日期')
    # plt.ylabel('合约期限(天)')
    # plt.grid()
    # plt.rcParams['font.sans-serif'] = ['SimHei']
    # plt.rcParams['axes.unicode_minus'] = False
    # plt.legend()
    # ax.set_xticks(range(0, len(contract_stats), 5))
    # plt.xticks(rotation=45)
    # plt.tight_layout()
    # plt.savefig(rf'fig\{suffix}每日约定合约期限统计.png')
    # plt.show()

def plot_contract_days(early_days, suffix):
    sns.histplot(early_days, bins=50, kde=True)
    plt.title(f'{suffix}约定合约期限分布')
    plt.xlabel('合约期限')
    plt.ylabel('频数')
    plt.text(early_days.max()*0.3,
             500,
             f'合约数量: {early_days.count()}\n'
             f'平均合约期限: {early_days.mean():.2f}\n'
             f'合约期限中位数: {early_days.median()}\n'
                f'最大合约期限: {early_days.max()}\n'
                f'最小合约期限: {early_days.min()}\n'
                )
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\{suffix}约券合约期限分布.png')
    plt.show()

def get_both_daily_rongquan_volume():
    rq.init()
    nongchao1_order = pd.read_pickle(r'data\nongchao1_order_df.pkl')
    nongchao2_order = pd.read_pickle(r'data\nongchao2_order_df.pkl')
    nongchao1_rq = get_product_daily_rongquan_volume(nongchao1_order, product='nongchao1')
    nongchao2_rq = get_product_daily_rongquan_volume(nongchao2_order, product='nongchao2')

    trading_days = rq.get_trading_dates(nongchao1_rq.index[0], nongchao1_rq.index[-1])
    nongchao1_rq = nongchao1_rq.reindex(trading_days).fillna(0)
    nongchao1_rq.index = pd.to_datetime(nongchao1_rq.index)
    nongchao1_rq['weekday'] = nongchao1_rq.index.weekday

    trading_days = rq.get_trading_dates(nongchao2_rq.index[0], nongchao2_rq.index[-1])
    nongchao2_rq = nongchao2_rq.reindex(trading_days).fillna(0)
    nongchao2_rq.index = pd.to_datetime(nongchao2_rq.index)
    nongchao2_rq['weekday'] = nongchao2_rq.index.weekday

    plot_daily_rq_transaction(nongchao1_rq['融券金额'], nongchao2_rq['融券金额'])
    plot_daily_num_stock(nongchao1_rq['融券对数'], nongchao2_rq['融券对数'])

def plot_daily_rq_transaction(nongchao1_s, nongchao2_s):
    df = pd.concat([nongchao1_s.rename('弄潮1号'), nongchao2_s.rename('弄潮2号')], axis=1)
    df = df.astype(float)
    daily_mean = df.mean().rename('每日平均融券金额').round(2)
    df = df.dropna()
    df.index = [date.strftime('%Y-%m-%d') for date in df.index]


    fig, ax = plt.subplots()
    # plt.stackplot(df.index, df.T, labels=df.columns)
    plt.plot(df.index, df['弄潮1号'], label='弄潮1号')
    plt.plot(df.index, df['弄潮2号'], label='弄潮2号')
    plt.text(df.index[int(len(df)*0.15)],
                df.max().max()*0.8,
                f'{daily_mean}')
    plt.title('弄潮1号和弄潮2号每日融券金额')
    plt.xlabel('日期')
    plt.ylabel('融券金额')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.legend()
    ax.set_xticks(range(0, len(df), 5))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(rf'fig\弄潮1号和弄潮2号每日融券金额.png')
    plt.show()


def plot_daily_num_stock(nongchao1_s, nongchao2_s):
    plt.plot(nongchao1_s.index, nongchao1_s, label='弄潮1号')
    plt.plot(nongchao2_s.index, nongchao2_s, label='弄潮2号')
    plt.title('弄潮1号和弄潮2号每日融券对数')
    plt.xlabel('日期')
    plt.ylabel('融券对数')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.legend()
    plt.savefig(rf'fig\弄潮1号和弄潮2号每日融券对数.png')
    plt.show()

def get_product_daily_rongquan_volume(df, product='nongchao1'):
    rongquan = df[df['摘要代码'].str.contains('融券卖出')]
    rongquan['发生日期'] = pd.to_datetime(rongquan['发生日期'].astype(str))
    rongquan_num = rongquan.groupby('发生日期')['证券代码'].unique().apply(len).rename('融券对数')
    rongquan_transaction = rongquan.groupby('发生日期')['发生金额'].sum().rename(product).rename('融券金额')

    rongquan_volume = rongquan.groupby(['发生日期', '证券代码'])['发生数量'].sum().rename('融券数量')
    rongquan_volume.to_pickle(rf'data\tmp\{product}_rongquan_volume.pkl')
    rongquan_daily_df = pd.concat([rongquan_num, rongquan_transaction], axis=1)
    return rongquan_daily_df

def get_both_interest_expense(freq='1D'):
    rq.init()
    nongchao1_order = pd.read_pickle(r'data\nongchao1_order_df.pkl')
    nongchao2_order = pd.read_pickle(r'data\nongchao2_order_df.pkl')
    nongchao1_interest = get_product_interest_expense(nongchao1_order, product='弄潮1号')
    nongchao2_interest = get_product_interest_expense(nongchao2_order, product='弄潮2号')
    interest_df = pd.concat([nongchao1_interest, nongchao2_interest], axis=1).dropna()
    trading_days = rq.get_trading_dates(interest_df.index[0], interest_df.index[-1])
    interest_df = interest_df.reindex(trading_days).fillna(0)
    interest_df.index = pd.to_datetime(interest_df.index)
    if freq == '1D':
        suffix = '日'
        data = interest_df
    elif freq == '1M':
        suffix = '月'
        data = interest_df.resample('1M').sum()
    elif freq == '1W':
        suffix = '周'
        data = interest_df.resample('1W').sum()
    else:
        raise ValueError('freq must be 1D, 1M or 1W')

    mean_interest = data.mean().rename(f'每{suffix}平均融券费用').round(2)
    data = data.fillna(0)
    data.index = [date.strftime('%Y-%m-%d') for date in data.index]

    # plt.stackplot(data.index, data.T, labels=data.columns)

    fig, ax = plt.subplots()
    plt.plot(data.index, data['弄潮1号'], label='弄潮1号')
    plt.plot(data.index, data['弄潮2号'], label='弄潮2号')
    plt.title(f'弄潮1号和弄潮2号每{suffix}融券费用')
    plt.text(data.index[int(len(data)*0.2)],
             data.max().max()*0.7,
                f'{mean_interest}')
    plt.xlabel(suffix)
    plt.ylabel('融券费用')
    plt.grid()
    plt.legend()
    ax.set_xticks(range(0, len(data), 1))
    plt.xticks(rotation=45)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(rf'fig\弄潮每{suffix}融券费用.png')
    plt.show()



    return interest_df

def get_product_interest_expense(df, product='弄潮1号'):
    interest_df = df[df['摘要代码'].str.contains('融券费用')]
    interest_df['利息费用'] = interest_df['发生金额'].abs()
    interest_df = interest_df.set_index('发生日期')
    interest_df.index = pd.to_datetime(interest_df.index.astype(str))
    interest_df = interest_df.resample('1D').sum()
    return interest_df['利息费用'].rename(product)

def reindex_df(df):
    rq.init()
    trading_days = rq.get_trading_dates(df.index[0], df.index[-1])
    df = df.reindex(trading_days)
    df.index = pd.to_datetime(df.index)
    return df


if __name__ == '__main__':
    # get_both_interest_expense(freq='1M')
    # get_both_daily_rongquan_volume()
    # get_contract_days()
    # repay_early_analysis()
    # hold_period_analysis()
    # contract_transaction_analysis()
    # contract_interest_rate()
    # check_instant_rongquan()
    plot_daily_contract_interest_rate()