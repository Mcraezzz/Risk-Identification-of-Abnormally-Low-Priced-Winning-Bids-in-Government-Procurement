# -*- coding: utf-8 -*-
# 数据探索脚本：探测合并数据集CSV文件的字符编码
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'

# Try different encodings
encodings = ['gb18030', 'cp936', 'gbk', 'utf-8-sig']
for enc in encodings:
    try:
        with open(fp, 'r', encoding=enc) as f:
            reader = csv.reader(f)
            headers = next(reader)
            print(f'成功使用编码: {enc}')
            print('字段数:', len(headers))
            for i, field in enumerate(headers, 1):
                print(f'{i}. {field}')
            
            # Count rows
            row_count = 0
            for row in reader:
                row_count += 1
            print(f'\n总记录数: {row_count}')
            break
    except Exception as e:
        print(f'{enc} 失败: {e}')
