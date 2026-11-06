# -*- coding: utf-8 -*-
# 数据探索脚本：检查价格异常分布
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

counts = {
    'ratio_lt_0.01': 0,
    'ratio_eq_0': 0,
    'ratio_gt_1': 0,
    'winning_le_100': 0,
    'budget_le_100': 0,
    'extreme': 0,
}

examples = {
    'ratio_lt_0.01': [],
    'ratio_eq_0': [],
    'ratio_gt_1': [],
    'winning_le_100': [],
    'budget_le_100': [],
    'extreme': [],
}

for row in rows:
    try:
        ratio = float(row['中标/预算比例'])
        budget = float(row['预算金额'])
        winning = float(row['中标金额'])
        
        if ratio < 0.01:
            counts['ratio_lt_0.01'] += 1
            if len(examples['ratio_lt_0.01']) < 3:
                examples['ratio_lt_0.01'].append((row['记录ID'], budget, winning, ratio))
        if ratio == 0:
            counts['ratio_eq_0'] += 1
            if len(examples['ratio_eq_0']) < 3:
                examples['ratio_eq_0'].append((row['记录ID'], budget, winning, ratio))
        if ratio > 1:
            counts['ratio_gt_1'] += 1
            if len(examples['ratio_gt_1']) < 3:
                examples['ratio_gt_1'].append((row['记录ID'], budget, winning, ratio))
        if winning <= 100:
            counts['winning_le_100'] += 1
            if len(examples['winning_le_100']) < 3:
                examples['winning_le_100'].append((row['记录ID'], budget, winning, ratio))
        if budget <= 100:
            counts['budget_le_100'] += 1
            if len(examples['budget_le_100']) < 3:
                examples['budget_le_100'].append((row['记录ID'], budget, winning, ratio))
        if ratio > 10 or ratio < 0.001 or (budget <= 100 and winning > 100000) or (winning <= 100 and budget > 100000):
            counts['extreme'] += 1
            if len(examples['extreme']) < 3:
                examples['extreme'].append((row['记录ID'], budget, winning, ratio))
    except:
        pass

for k, v in counts.items():
    print(f'{k}: {v}')
    if examples[k]:
        print('  示例:', examples[k])
