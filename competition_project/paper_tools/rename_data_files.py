# -*- coding: utf-8 -*-
import os
import shutil

base = r'C:\Users\22672\Desktop\统计建模比赛\统计建模原数据'

mapping = {
    '政府采购项目风险分析_全样本表.csv': 'full_sample.csv',
    '政府采购项目风险分析_价格有效样本表.csv': 'price_valid_sample.csv',
    '政府采购项目风险分析_服务类主样本表.csv': 'service_main_sample.csv',
    '政府采购项目风险分析_2025Q1扩展样本表.csv': 'extension_2025q1_sample.csv',
    '政府采购项目风险分析主表_v2.csv': 'main_table_v2.csv',
}

# Use bytes to get correct filenames
for b in os.listdir(base.encode('utf-8')):
    try:
        name = b.decode('utf-8')
        if name in mapping:
            src = os.path.join(base, name)
            dst = os.path.join(base, mapping[name])
            shutil.copy2(src, dst)
            print(f'Copied: {name} -> {mapping[name]}')
    except Exception as e:
        print(f'Error: {e}')
