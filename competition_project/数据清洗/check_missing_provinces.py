# -*- coding: utf-8 -*-
# 数据探索脚本：检查省份缺失但城市不缺失的记录分布
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Find records with empty province but non-empty city
missing_prov = {}
for row in rows:
    prov = row.get('项目省份', '').strip()
    city = row.get('项目城市', '').strip()
    if not prov and city:
        missing_prov[city] = missing_prov.get(city, 0) + 1

print(f'省份缺失但城市不缺失的记录数: {sum(missing_prov.values())}')
print('\n城市分布:')
for city, cnt in sorted(missing_prov.items(), key=lambda x: -x[1]):
    print(f'  {city}: {cnt}')
