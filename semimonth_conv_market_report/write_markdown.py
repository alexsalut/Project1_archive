# -*- coding: utf-8 -*-
# @Time    : 2022/10/21 14:00
# @Author  : Youwei Wu
# @File    : write_markdown.py
# @Software: PyCharm

import os

from conv_perf import gen_all_graph


class ConvMarketReview:

    def __init__(self, mark_date):
        self.cache_dir = rf'投研例会\{mark_date}/周素颖/转债市场综述'
        os.makedirs(self.cache_dir, exist_ok=True)

    def gen_report(
            self,
            start_date,
            end_date,
    ):
        gen_all_graph(start=start_date, end=end_date, save_dir=self.cache_dir)

        indent = "&emsp;&emsp;"
        with open(f"{self.cache_dir}/MarketReview_{start_date}_{end_date}.md", 'w') as f:
            f.write(
                f"# 市场综述报告：{start_date} - {end_date}\n"

                "## 1 市场整体表现\n"
                f"![](近两周可转债和股票指数({start_date}-{end_date})区间收益.png)\n"
                f"![](近两周可转债和股票指数({start_date}-{end_date})走势.png)\n"
                f"![](2024年可转债和股票指数走势.png)\n"

                "## 2 东财可转债行业指数\n"
                f"![](近两周东财可转债行业指数({start_date}-{end_date})区间收益.png)\n"
                f"![](2024年东财可转债行业指数走势.png)\n"
            )
