# -*- coding: utf-8 -*-
# 数据探索脚本：查看服务类型CSV文件的字段和样本数据
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500_服务类型.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    print('字段数:', len(headers))
    for i, field in enumerate(headers, 1):
        print(f'{i}. {field}')
    print()
    print('前3行数据示例:')
    for _ in range(3):
        row = next(reader)
        for k, v in zip(headers, row):
            val = v[:60] if v else ''
            print(f'  {k}: {val}')
        print('---')
