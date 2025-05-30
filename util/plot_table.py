#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/1 16:08
# @Author  : Suying
# @Site    : 
# @File    : plot_table.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_table(data, path=None, col_width=3.0, row_height=0.625, font_size=14,
               header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
               bbox=[0, 0, 1, 1], header_columns=0,
               ax=None, **kwargs):
    data = data.reset_index(drop=False)
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')
    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)
    for k, cell in mpl_table._cells.items():
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0] % len(row_colors)])
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    fig = ax.get_figure()
    if path is not None:
        fig.savefig(path)
    plt.show()
