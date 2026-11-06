# -*- coding: utf-8 -*-
# 数据验证脚本：验证最终风险分析主表的字段结构和指标合并结果
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print('总记录数:', len(rows))
    print('字段数:', len(reader.fieldnames))
    for i, h in enumerate(reader.fieldnames, 1):
        print(f'{i}. {h}')
    print()
    print('第一条记录（含指标）:')
    row = rows[0]
    for k in ['项目省份', 'gdp', 'population', 'gdp_per_capita', 'fiscal_pressure', 'urbanization_rate']:
        print(f'  {k}: {row.get(k, "")}')
    print()
    print('一条有指标的4500样本记录:')
    for row in rows:
        if row['数据来源'] == 'gov_contract_q1_2025' and row.get('gdp'):
            print(f'  项目省份: {row["项目省份"]}')
            print(f'  gdp: {row["gdp"]}')
            print(f'  population: {row["population"]}')
            print(f'  gdp_per_capita: {row["gdp_per_capita"]}')
            break
