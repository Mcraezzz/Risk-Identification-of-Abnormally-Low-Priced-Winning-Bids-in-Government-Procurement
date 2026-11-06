# -*- coding: utf-8 -*-
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Count empty provinces before and after
empty_before = 0
empty_after = 0
for row in rows:
    city = row.get('项目城市', '').strip()
    prov = row.get('项目省份', '').strip()
    if not prov:
        empty_after += 1
        if city:
            empty_before += 1

print(f'省份为空但城市不为空: {empty_before} 条（这些是通过城市反推的）')
print(f'反推后仍为空: {empty_after} 条')

# Check inferred provinces distribution
inferred = {}
for row in rows:
    city = row.get('项目城市', '').strip()
    prov = row.get('项目省份', '').strip()
    if city and prov:
        # Check if this city typically had empty province in original data
        # We can only approximate by looking at records from gov_contract_q1_2025
        if row['数据来源'] == 'gov_contract_q1_2025':
            inferred[prov] = inferred.get(prov, 0) + 1

print('\n4500样本反推后的省份分布（Top 15）:')
for p, c in sorted(inferred.items(), key=lambda x: -x[1])[:15]:
    print(f'  {p}: {c}')
