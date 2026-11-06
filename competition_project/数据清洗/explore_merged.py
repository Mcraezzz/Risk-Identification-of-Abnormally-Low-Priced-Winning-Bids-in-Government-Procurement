# -*- coding: utf-8 -*-
# 数据探索脚本：查看合并后数据集的基本结构和样本数据
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'
with open(fp, 'r', encoding='gb2312') as f:
    reader = csv.reader(f)
    headers = next(reader)
    print('字段数:', len(headers))
    for i, field in enumerate(headers, 1):
        print(f'{i}. {field}')
    
    print('\n前2行数据示例:')
    for _ in range(2):
        row = next(reader)
        for k, v in zip(headers, row):
            val = v[:60] if v else ''
            print(f'  {k}: {val}')
        print('---')

    # Check value distributions for key fields
    print('\n=== 采购方式分布 ===')
    methods = {}
    budgets = []
    winnings = []
    provinces = {}
    categories = {}
    
    for row in reader:
        method = row[headers.index('采购方式')] if '采购方式' in headers else ''
        methods[method] = methods.get(method, 0) + 1
        
        province = row[headers.index('项目省份')] if '项目省份' in headers else ''
        if province:
            provinces[province] = provinces.get(province, 0) + 1
        
        cat = row[headers.index('服务类别')] if '服务类别' in headers else ''
        if cat:
            categories[cat] = categories.get(cat, 0) + 1
        
        try:
            b = float(row[headers.index('预算金额')])
            budgets.append(b)
        except:
            pass
        try:
            w = float(row[headers.index('中标金额')])
            winnings.append(w)
        except:
            pass

print('\n采购方式分布 (Top 20):')
for m, c in sorted(methods.items(), key=lambda x: -x[1])[:20]:
    print(f'  {m}: {c}')

print('\n项目省份分布 (Top 20):')
for p, c in sorted(provinces.items(), key=lambda x: -x[1])[:20]:
    print(f'  {p}: {c}')

print('\n服务类别分布 (Top 20):')
for cat, c in sorted(categories.items(), key=lambda x: -x[1])[:20]:
    print(f'  {cat}: {c}')

if budgets:
    print(f'\n预算金额统计: min={min(budgets)}, max={max(budgets)}, avg={sum(budgets)/len(budgets):.2f}')
if winnings:
    print(f'中标金额统计: min={min(winnings)}, max={max(winnings)}, avg={sum(winnings)/len(winnings):.2f}')
