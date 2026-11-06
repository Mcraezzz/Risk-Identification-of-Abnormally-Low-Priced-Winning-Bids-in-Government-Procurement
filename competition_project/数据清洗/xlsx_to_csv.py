# -*- coding: utf-8 -*-
# 格式转换脚本：将Excel文件转换为CSV格式
# 生成日期: 2026-05-10

from openpyxl import load_workbook
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

excel_path = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.xlsx'
csv_path = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'

print('读取 Excel...')
wb = load_workbook(excel_path, read_only=True, data_only=True)
ws = wb['合并表']

# Read headers
headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
print(f'字段数: {len(headers)}')

# Write CSV
print('写入 CSV...')
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    
    row_count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        writer.writerow(row)
        row_count += 1
        if row_count % 1000 == 0:
            print(f'  已处理 {row_count} 行...')

print(f'完成。共写入 {row_count} 行数据。')
print(f'输出文件: {csv_path}')
