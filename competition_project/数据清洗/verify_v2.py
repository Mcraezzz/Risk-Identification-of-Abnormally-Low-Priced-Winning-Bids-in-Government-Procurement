# -*- coding: utf-8 -*-
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print('总记录数:', len(rows))
    print('字段数:', len(reader.fieldnames))
    for i, h in enumerate(reader.fieldnames, 1):
        print(f'{i}. {h}')
    print()
    print('第一条记录关键字段:')
    row = rows[0]
    for k in ['项目省份', '项目城市', '统一服务类别', '价格有效样本', '极端价格异常标记', '比例异常标记', '小金额标记']:
        print(f'  {k}: {row.get(k, "")}')
    print()
    print('一条省份反推的记录:')
    for row in rows:
        if row.get('项目省份') == '湖北' and row.get('项目城市') == '武汉市':
            print(f'  ID: {row["记录ID"]}')
            print(f'  数据来源: {row["数据来源"]}')
            print(f'  省份: {row["项目省份"]}')
            print(f'  城市: {row["项目城市"]}')
            break
