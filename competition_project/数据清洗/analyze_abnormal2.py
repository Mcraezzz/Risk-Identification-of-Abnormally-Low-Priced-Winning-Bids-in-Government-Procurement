# -*- coding: utf-8 -*-
# 数据分析脚本：详细分析中标/预算比例的异常分布情况
# 生成日期: 2026-05-10

import csv
import sys
import math

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500.csv','r',encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Check all ratios
ratios = []
for i,row in enumerate(rows):
    val = row['中标/预算比例']
    try:
        ratio = float(val)
        ratios.append(ratio)
    except:
        ratios.append(None)

# Count by ranges
lt0 = sum(1 for r in ratios if r is not None and r < 0)
gt1 = sum(1 for r in ratios if r is not None and r > 1)
eq0 = sum(1 for r in ratios if r is not None and r == 0)
eq1 = sum(1 for r in ratios if r is not None and r == 1)
nulls = sum(1 for r in ratios if r is None)
valid = [r for r in ratios if r is not None]

print(f'总记录数: {len(rows)}')
print(f'<0: {lt0}')
print(f'>1: {gt1}')
print(f'==0: {eq0}')
print(f'==1: {eq1}')
print(f'空值/非数字: {nulls}')
if valid:
    print(f'最小值: {min(valid)}')
    print(f'最大值: {max(valid)}')
    print(f'平均值: {sum(valid)/len(valid):.4f}')

# Show sample rows with ratio > 1 or < 0 or empty
print('\n--- ratio > 1 ---')
count = 0
for i,row in enumerate(rows):
    try:
        ratio = float(row['中标/预算比例'])
        if ratio > 1:
            count += 1
            print(f"ID={row['记录ID']}, 预算={row['预算金额']}, 中标={row['中标金额']}, 比例={ratio}, 节约率={row['节约率']}")
            if count >= 20:
                break
    except:
        pass

print('\n--- ratio < 0 ---')
count = 0
for i,row in enumerate(rows):
    try:
        ratio = float(row['中标/预算比例'])
        if ratio < 0:
            count += 1
            print(f"ID={row['记录ID']}, 预算={row['预算金额']}, 中标={row['中标金额']}, 比例={ratio}, 节约率={row['节约率']}")
            if count >= 20:
                break
    except:
        pass

print('\n--- empty/null ratio ---')
count = 0
for i,row in enumerate(rows):
    val = row['中标/预算比例']
    if val is None or val.strip() == '':
        count += 1
        if count <= 10:
            print(f"ID={row['记录ID']}, 预算={row['预算金额']}, 中标={row['中标金额']}, 比例='{val}', 节约率={row['节约率']}")
print(f'空值总数: {count}')
