#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/28 9:46
# @Author  : Suying
# @Site    : 
# @File    : txt_data.py
import pandas as pd
import re


class TxtData:
    def __init__(self, file_path):
        self.file_path = file_path
        self.series_sep_list = [':', '：']
        self.df_sep_list = ['|', '│']

    def gen_settle_data(self, encoding='gbk'):
        data = self.read_file(encoding)
        clearing_dict = self.gen_series_data(self.categorize_data(data))
        df_dict = self.gen_df_data(self.categorize_data(data))
        clearing_dict.update(df_dict)
        return clearing_dict

    def read_file(self, encoding):
        with open(self.file_path, 'r', encoding=encoding) as f:
            data = f.readlines()
        return data

    def categorize_data(self, data):
        grouped_line_dict = {}
        series_line_list = [line for line in data if any([sep in line for sep in self.series_sep_list])]
        grouped_line_dict['series'] = series_line_list

        df_line_list = [line for line in data if line not in series_line_list]
        n_locs = [index for index, line in enumerate(df_line_list) if line == '\n']
        n_locs.append(len(df_line_list)-1) if n_locs[-1] < len(df_line_list)-1 else None
        n_locs = [n for n in n_locs if n+1 not in n_locs]
        grouped_line_dict.update({
            df_line_list[n_locs[i]+1].split()[0]: df_line_list[n_locs[i]+1:n_locs[i+1]] for i in range(len(n_locs)-1)
        })
        return grouped_line_dict

    @staticmethod
    def gen_series_data(categorized_data_dict):
        clearing_dict = {'series': pd.Series()}
        content = categorized_data_dict['series']
        sep = ':' if any([':' in line for line in content]) else '：'

        def get_pairs(line, pattern, pair_sep):
            pair = []
            item_list = re.split(pattern, line)
            valid_list = [x for x in item_list if x != '']
            for i, x in enumerate(valid_list):
                if x[-1] == pair_sep and i < len(valid_list) - 1:
                    pair.append([x[:-1], valid_list[i + 1]])
                elif pair_sep in x:
                    pair.append(x.split(pair_sep))

            return pair

        for j, line in enumerate(content):
            pairs = get_pairs(line, r'[ ,\n]', pair_sep=sep)
            if len(pairs) > 0:
                for h in pairs:
                    if h[0] in clearing_dict['series'].index:
                        clearing_dict['series'][h[0]+str(j)] = h[1]
                    else:
                        clearing_dict['series'][h[0]] = h[1]

        return clearing_dict

    @staticmethod
    def gen_df_data(categorized_data_dict):
        categorized_data_dict.pop('series')
        clearing_dict = {}
        for element in categorized_data_dict.keys():
            content = categorized_data_dict[element]
            if any(['|' in line for line in content]):
                sep = '|'
            elif any(['│' in line for line in content]):
                sep = '│'
            else:
                sep = '  '

            selected_content = [x for x in content if sep in x and '---' not in x] if sep in ['|', '│'] else content[1:]
            cols = [col for col in selected_content[0].split(sep) if col != '']
            cols = [col.replace(' ', '') for col in cols]
            clearing_dict[element] = pd.DataFrame(columns=cols) if len(selected_content) > 0 else pd.DataFrame()
            if len(selected_content) > 1:
                for i, line in enumerate(selected_content[1:]):
                    sep_line = [x for x in line.split(sep) if x != '']
                    if len(sep_line) == len(cols):
                        clearing_dict[element].loc[i] = sep_line
        return clearing_dict


if __name__ == '__main__':
    f_path = [
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\310300016431衍舟听涟2号20231016(期权).TXT',
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\310310300343衍舟听涟2号20231016(两融).TXT',
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\190000612973普通对账单_20231016.txt'
    ]
    option_clearing_file_data = TxtData(f_path[2]).gen_clearing_file_data(encoding='utf-8')
