# -*- coding: utf-8 -*-
# 数据探索脚本：分析合并数据集的采购方式、省份、服务类别分布
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'

with open(fp, 'r', encoding='gb18030') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'总记录数: {len(rows)}')

# Procurement methods
methods = {}
provinces = {}
categories = {}
budgets = []
winnings = []
zero_win = 0
neg_budget = 0
neg_win = 0
null_budget = 0
null_win = 0

for row in rows:
    m = row.get('采购方式', '')
    methods[m] = methods.get(m, 0) + 1
    
    p = row.get('项目省份', '')
    if p:
        provinces[p] = provinces.get(p, 0) + 1
    
    cat = row.get('服务类别', '')
    if cat:
        categories[cat] = categories.get(cat, 0) + 1
    
    b = row.get('预算金额', '').strip()
    w = row.get('中标金额', '').strip()
    
    if b == '' or b == 'None':
        null_budget += 1
    else:
        try:
            bv = float(b)
            budgets.append(bv)
            if bv < 0:
                neg_budget += 1
        except:
            null_budget += 1
    
    if w == '' or w == 'None':
        null_win += 1
    else:
        try:
            wv = float(w)
            winnings.append(wv)
            if wv < 0:
                neg_win += 1
            if wv == 0:
                zero_win += 1
        except:
            null_win += 1

print('\n=== 采购方式分布 ===')
for m, c in sorted(methods.items(), key=lambda x: -x[1]):
    print(f'  {m}: {c}')

print('\n=== 项目省份分布 (Top 30) ===')
for p, c in sorted(provinces.items(), key=lambda x: -x[1])[:30]:
    print(f'  {p}: {c}')

print('\n=== 服务类别分布 (Top 30) ===')
for cat, c in sorted(categories.items(), key=lambda x: -x[1])[:30]:
    print(f'  {cat}: {c}')

print('\n=== 金额统计 ===')
print(f'预算金额 - null/invalid: {null_budget}, 负值: {neg_budget}')
if budgets:
    print(f'  min={min(budgets):.2f}, max={max(budgets):.2f}, avg={sum(budgets)/len(budgets):.2f}')
print(f'中标金额 - null/invalid: {null_win}, 负值: {neg_win}, 为零: {zero_win}')
if winnings:
    print(f'  min={min(winnings):.2f}, max={max(winnings):.2f}, avg={sum(winnings)/len(winnings):.2f}')
