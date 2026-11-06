# -*- coding: utf-8 -*-
# 数据分析脚本：分析预算金额和中标金额的异常记录
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500.csv','r',encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Check budget and winning amounts
zero_budget = []
neg_budget = []
zero_win = []
neg_win = []
empty_budget = []
empty_win = []

for i,row in enumerate(rows):
    budget = row['预算金额'].strip()
    winning = row['中标金额'].strip()
    
    if budget == '':
        empty_budget.append(i)
    else:
        try:
            b = float(budget)
            if b == 0:
                zero_budget.append(i)
            elif b < 0:
                neg_budget.append(i)
        except:
            empty_budget.append(i)
    
    if winning == '':
        empty_win.append(i)
    else:
        try:
            w = float(winning)
            if w == 0:
                zero_win.append(i)
            elif w < 0:
                neg_win.append(i)
        except:
            empty_win.append(i)

print(f'预算金额为0: {len(zero_budget)}')
print(f'预算金额为负: {len(neg_budget)}')
print(f'预算金额为空/非数字: {len(empty_budget)}')
print(f'中标金额为0: {len(zero_win)}')
print(f'中标金额为负: {len(neg_win)}')
print(f'中标金额为空/非数字: {len(empty_win)}')

# Show some examples
if zero_budget:
    print('\n预算金额为0的例子:')
    for idx in zero_budget[:5]:
        row = rows[idx]
        print(f"ID={row['记录ID']}, 预算='{row['预算金额']}', 中标={row['中标金额']}, 比例={row['中标/预算比例']}")

if neg_budget:
    print('\n预算金额为负的例子:')
    for idx in neg_budget[:5]:
        row = rows[idx]
        print(f"ID={row['记录ID']}, 预算='{row['预算金额']}', 中标={row['中标金额']}, 比例={row['中标/预算比例']}")

# Check if winning > budget (ratio > 1 implicitly)
win_gt_budget = []
for i,row in enumerate(rows):
    try:
        b = float(row['预算金额'])
        w = float(row['中标金额'])
        if w > b:
            win_gt_budget.append((i, row['记录ID'], b, w, float(row['中标/预算比例'])))
    except:
        pass

print(f'\n中标金额 > 预算金额: {len(win_gt_budget)}')
if win_gt_budget:
    print('例子:')
    for item in win_gt_budget[:10]:
        print(f"ID={item[1]}, 预算={item[2]}, 中标={item[3]}, 比例={item[4]}")
