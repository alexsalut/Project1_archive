import time

import pandas as pd
class cnn_updater:
    def __init__(self,file_dir, today=None):
        self.file_dir = file_dir
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.cnn_path = rf'{self.file_dir}/cnn策略观察.xlsx'

    def talang_update(self):
        self.talang_2_df = pd.read_excel(self.cnn_portfolio_path, index_col=0, sheet_name='踏浪2号',parse_dates=True)
        self.talang_3_df = pd.read_excel(self.cnn_portfolio_path, index_col=0, sheet_name='踏浪3号',parse_dates=True)

    def cnn_portfolio_update(self):
        cnn_portfolio_df = pd.read_excel(self.cnn_portfolio_path, index_col=0, sheet_name='多策略超额',parse_dates=True)
        cnn_single_portfolio_df = pd.read_excel(self.cnn_portfolio_path, index_col=0, sheet_name='单策略超额',parse_dates=True)