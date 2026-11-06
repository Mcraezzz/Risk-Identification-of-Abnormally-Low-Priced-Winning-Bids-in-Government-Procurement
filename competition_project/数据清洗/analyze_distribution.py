# -*- coding: utf-8 -*-
# 数据分析脚本：统计中标/预算比例在各区间段的分布
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500.csv','r',encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

ratios = []
for row in rows:
    try:
        ratios.append(float(row['中标/预算比例']))
    except:
        pass

bins = {
    '<0.6': 0,
    '0.6-0.7': 0,
    '0.7-0.8': 0,
    '0.8-0.85': 0,
    '0.85-0.9': 0,
    '0.9-0.95': 0,
    '0.95-1.0': 0,
    '=1.0': 0,
}

for r in ratios:
    if r < 0.6:
        bins['<0.6'] += 1
    elif r < 0.7:
        bins['0.6-0.7'] += 1
    elif r < 0.8:
        bins['0.7-0.8'] += 1
    elif r < 0.85:
        bins['0.8-0.85'] += 1
    elif r < 0.9:
        bins['0.85-0.9'] += 1
    elif r < 0.95:
        bins['0.9-0.95'] += 1
    elif r < 1.0:
        bins['0.95-1.0'] += 1
    else:
        bins['=1.0'] += 1

for k,v in bins.items():
    pct = v/len(ratios)*100
    print(f'{k}: {v} ({pct:.1f}%)')
