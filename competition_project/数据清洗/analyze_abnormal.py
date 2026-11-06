# -*- coding: utf-8 -*-
# 数据分析脚本：检查政府采购数据集中中标/预算比例的异常值
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500.csv','r',encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Find abnormal rows
abnormal = []
for i,row in enumerate(rows):
    try:
        ratio = float(row['中标/预算比例'])
        if ratio < 0 or ratio > 1:
            abnormal.append({
                'idx': i,
                '记录ID': row['记录ID'],
                '预算金额': row['预算金额'],
                '中标金额': row['中标金额'],
                '中标/预算比例': ratio,
                '节约率': row['节约率']
            })
    except:
        pass

print('异常数据总数:', len(abnormal))
print('\n前50条异常数据:')
for r in abnormal[:50]:
    print(f"ID={r['记录ID']}, 预算={r['预算金额']}, 中标={r['中标金额']}, 比例={r['中标/预算比例']:.4f}, 节约率={r['节约率']}")
