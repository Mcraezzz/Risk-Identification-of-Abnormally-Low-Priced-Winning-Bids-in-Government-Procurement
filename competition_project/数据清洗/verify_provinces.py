# -*- coding: utf-8 -*-
# 数据验证脚本：验证清洗后项目省份的分布情况
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    provinces = {}
    for row in reader:
        p = row.get('项目省份', '')
        if p:
            provinces[p] = provinces.get(p, 0) + 1

print('项目省份分布:')
for p, c in sorted(provinces.items(), key=lambda x: -x[1]):
    print(f'  {p}: {c}')
