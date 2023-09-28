#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/28 9:46
# @Author  : Suying
# @Site    : 
# @File    : option_clearing_file_data.py
import pandas as pd
import re


class OptionClearingFileData:
    def __init__(self, file_path):
        self.file_path = file_path
        self.series_list = ['交易结算单', '资金状况']
        self.df_list = ['出入金明细单', '成交明细单', '平仓明细单', '行权流水单', '现货交收单', '指派明细单',
                        '转处置明细单',
                        '持仓明细单']

    def gen_option_clearing_file_data(self):
        data = self.read_file()
        categorized_data_dict = self.categorize_data(data, self.series_list + self.df_list)
        option_clearing_dict = self.gen_series_data(categorized_data_dict)
        option_clearing_dict.update(self.gen_df_data(categorized_data_dict))
        return option_clearing_dict

    def read_file(self):
        with open(self.file_path, 'r', encoding='gbk') as f:
            data = f.readlines()
        return data

    def categorize_data(self, data, element_list):
        location_s = pd.Series(index=element_list)
        for line in data:
            for element in element_list:
                if line.startswith(element):
                    location_s[element] = data.index(line)
        location_s = location_s.sort_values(ascending=True).astype(int)
        line_dict = {}
        for i, element in enumerate(location_s.index):
            if i == len(location_s) - 1:
                line_dict[element] = data[location_s[element] + 1:]
            else:
                line_dict[element] = data[location_s[element] + 1:location_s[location_s.index[i + 1]]]
        return line_dict

    def gen_series_data(self, categorized_data_dict):
        option_clearing_dict = {series: pd.Series() for series in self.series_list}
        for element in self.series_list:
            content = categorized_data_dict[element]
            selected_content = [x for x in content if ':' in x]
            for line in selected_content:
                filtered_line = [x.replace('\n', '') for x in re.split(' |:', line) if x != '']
                if (len(filtered_line) > 0) & (len(filtered_line) % 2 == 0):
                    for i in range(0, len(filtered_line) - 1, 2):
                        option_clearing_dict[element][filtered_line[i]] = filtered_line[i + 1]
        return option_clearing_dict

    def gen_df_data(self, categorized_data_dict):
        option_clearing_dict = {}
        for element in self.df_list:
            content = categorized_data_dict[element]
            selected_content = [x for x in content if '|' in x and '---' not in x]
            option_clearing_dict[element] = pd.DataFrame(columns=selected_content[0].split('|')[1:-1])
            for i, line in enumerate(selected_content[1:]):
                option_clearing_dict[element].loc[i] = line.split('|')[1:-1]
        return option_clearing_dict


if __name__ == '__main__':
    file_path = r'C:\Users\Yz02\Desktop\Data\Save\期权结算单\310300016431衍舟听涟2号20230925(期权).TXT'
    option_clearing_file_data = OptionClearingFileData(file_path).gen_option_clearing_file_data()
