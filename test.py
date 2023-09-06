# import xlwings as xw
#
#
# def remove_formulas(input_file, output_file):
#     # Open the Excel file
#     wb = xw.Book(input_file)
#
#     # Loop through each worksheet
#     for sheet in wb.sheets:
#         # Loop through each cell in the sheet
#         for cell in sheet.cells:
#             # Check if the cell has a formula
#             if cell.has_formula:
#                 # Set the cell's value to the calculated value
#                 cell.value = cell.value
#
#     # Save the workbook with removed formulas
#     wb.save(output_file)
#     wb.close()
#
#
# # Input and output file paths
# input_file = r'C:/Users/Yz02/Desktop/monitor_20230906.xlsx'
# output_file = r'C:/Users/Yz02/Desktop/monitor_20230906_copy.xlsx'
#
# # Call the function to remove formulas and save the result
# remove_formulas(input_file, output_file)
import pandas as pd
import chinese_calendar
from EmQuantAPI import c
from account import read_account_info
import xlwings as xw
import pandas as pd
import openpyxl
import datetime
from chinese_calendar import is_workday

def get_next_trading_day(today=None):
    date = today if today is not None else datetime.datetime.now().strftime('%Y%m%d')
    tomorrow = datetime.datetime.strptime(date, '%Y%m%d') + datetime.timedelta(days=1)
    while not (is_workday(tomorrow) and tomorrow.isoweekday() < 6):
        tomorrow = tomorrow + datetime.timedelta(days=1)
    next_trading_day = tomorrow.strftime('%Y%m%d')
    print(f'next trading day is {next_trading_day}')
    return next_trading_day


if __name__ == "__main__":
    m = get_next_trading_day('20231003')






