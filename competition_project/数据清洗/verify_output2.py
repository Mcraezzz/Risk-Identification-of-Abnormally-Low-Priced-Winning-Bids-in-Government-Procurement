# -*- coding: utf-8 -*-
# 数据验证脚本：验证省份映射、服务类别映射和4500样本映射结果
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Check a 4500 sample record
print('=== 4500样本记录示例 ===')
for row in rows:
    if row['数据来源'] == 'gov_contract_q1_2025':
        print(f"ID: {row['记录ID']}")
        print(f"标题: {row['公告标题'][:50]}")
        print(f"省份: {row['项目省份']}")
        print(f"采购方式: {row['采购方式']} -> {row['采购方式标准化']}")
        print(f"服务类别: {row['服务类别']}")
        print(f"采购大类: {row['采购大类']}")
        print(f"统一服务类别: {row['统一服务类别']}")
        print()
        break

# Check "其他" category breakdown
print('=== 采购大类=其他 的服务类别分布 ===')
other_cats = {}
for row in rows:
    if row['采购大类'] == '其他':
        cat = row['服务类别']
        other_cats[cat] = other_cats.get(cat, 0) + 1
for cat, c in sorted(other_cats.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {c}')

# Check records that were originally from problematic provinces
print('\n=== 原省份为深圳/青岛/厦门的记录 ===')
for row in rows:
    if row['项目省份'] in ['广东', '山东', '福建'] and row['数据来源'] == 'ccgp_merged':
        # We can't directly tell if it was originally mapped, but we can check city
        city = row.get('项目城市', '')
        if city in ['深圳市', '青岛市', '厦门市']:
            print(f"  省份={row['项目省份']}, 城市={city}, ID={row['记录ID']}")
