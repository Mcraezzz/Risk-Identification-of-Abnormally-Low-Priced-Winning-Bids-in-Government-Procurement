# -*- coding: utf-8 -*-
# 数据验证脚本：验证清洗后输出文件的结构和记录数
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
with open(fp, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print('总记录数:', len(rows))
    print('字段:', reader.fieldnames)
    print()
    print('第一条记录:')
    for k, v in rows[0].items():
        val = v[:60] if v else ''
        print(f'  {k}: {val}')
    print()
    print('最后一条记录:')
    for k, v in rows[-1].items():
        val = v[:60] if v else ''
        print(f'  {k}: {val}')
