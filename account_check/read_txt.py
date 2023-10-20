#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 9:06
# @Author  : Suying
# @Site    : 
# @File    : read_txt.py
class TXTFileReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def gen_formatted_txt_file(self, encoding='gbk'):
        data = self.read_file(encoding)
        self.categorize_data(data)

    @staticmethod
    def categorize_data(data):
        n_loc = [index for index, line in enumerate(data) if line == '\n']
        n_loc = [n for n in n_loc if n + 1 not in n_loc]
        if n_loc[-1] < len(data) - 1:
            n_loc.append(len(data) - 1)
        grouped_data_dict = {
            i: data[n_loc[i] + 1:n_loc[i + 1]] for i in range(len(n_loc) - 1)
        }
        return grouped_data_dict

    def read_file(self, encoding):
        with open(self.file_path, 'r', encoding=encoding) as f:
            data = f.readlines()
        return data


if __name__ == '__main__':
    f_path = [
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\310300016431衍舟听涟2号20231016(期权).TXT',
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\310310300343衍舟听涟2号20231016(两融).TXT',
        r'C:\Users\Yz02\Desktop\Data\Save\账户对账单\190000612973普通对账单_20231016.txt'
    ]
    TXTFileReader(f_path[2]).gen_formatted_txt_file(encoding='utf-8')
