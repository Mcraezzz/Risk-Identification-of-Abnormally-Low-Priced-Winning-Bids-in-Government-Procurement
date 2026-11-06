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
    print('第一条记录建模字段:')
    row = rows[0]
    for k in ['price_ratio_clean', 'saving_rate_clean', 'log_budget', 'log_bid', 'valid_price_sample',
              'rule_policy_65', 'rule_quantile_10', 'rule_quantile_5', 'rule_iqr', 'rule_robust_z',
              'rule_risk_score', 'rule_risk_level', 'is_suspicious_low_price', 'is_high_risk_low_price']:
        print(f'  {k}: {row.get(k, "")}')
    print()
    print('一条高风险记录:')
    for row in rows:
        if row.get('rule_risk_level') == '高风险':
            for k in ['记录ID', '统一服务类别', 'price_ratio_clean', 'rule_risk_score', 'rule_risk_level',
                      'is_suspicious_low_price', 'is_high_risk_low_price']:
                print(f'  {k}: {row.get(k, "")}')
            break
