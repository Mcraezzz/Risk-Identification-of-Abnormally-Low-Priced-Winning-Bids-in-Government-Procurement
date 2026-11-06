# -*- coding: utf-8 -*-
# 数据验证脚本：统计被删除的异常记录数量和原因
# 生成日期: 2026-05-10

import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'
with open(fp, 'r', encoding='gb18030') as f:
    reader = csv.DictReader(f)
    null_budget = 0
    invalid_budget = 0
    huge_budget = 0
    null_win = 0
    invalid_win = 0
    zero_win = 0
    huge_win = 0
    
    for row in reader:
        b = row.get('预算金额', '').strip()
        w = row.get('中标金额', '').strip()
        
        if b == '' or b == 'None':
            null_budget += 1
        else:
            try:
                bv = float(b)
                if bv < 0:
                    invalid_budget += 1
                elif bv > 1e15:
                    huge_budget += 1
            except:
                invalid_budget += 1
        
        if w == '' or w == 'None':
            null_win += 1
        else:
            try:
                wv = float(w)
                if wv < 0:
                    invalid_win += 1
                elif wv == 0:
                    zero_win += 1
                elif wv > 1e12:
                    huge_win += 1
            except:
                invalid_win += 1

print('合并数据集金额异常统计:')
print(f'  预算为空: {null_budget}')
print(f'  预算无效(负数/非数字): {invalid_budget}')
print(f'  预算极大(>1e15): {huge_budget}')
print(f'  中标为空: {null_win}')
print(f'  中标无效(负数/非数字): {invalid_win}')
print(f'  中标为零: {zero_win}')
print(f'  中标极大(>1e12): {huge_win}')
