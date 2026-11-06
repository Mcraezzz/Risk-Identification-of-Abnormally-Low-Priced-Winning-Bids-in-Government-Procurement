# -*- coding: utf-8 -*-
# 数据预处理脚本：检测CSV文件的字符编码格式
# 生成日期: 2026-05-10

import chardet
import os

base = r'C:\Users\22672\Desktop\统计建模原数据'
for fname in ['ccgp_merged_supplier_credit_merged.csv', 'government_contract_q1_2025_sample_4500_服务类型.csv']:
    fp = os.path.join(base, fname)
    with open(fp, 'rb') as f:
        result = chardet.detect(f.read(200000))
        print(f'{fname}: {result}')
