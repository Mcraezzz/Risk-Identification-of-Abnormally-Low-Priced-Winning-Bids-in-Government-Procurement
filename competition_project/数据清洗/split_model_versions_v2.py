# -*- coding: utf-8 -*-
# 【数据清洗脚本】将风险分析主表_v2（含建模特征）重新拆分为4个建模版本
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv'
OUTPUT_DIR = r'C:\Users\22672\Desktop\统计建模原数据'


def write_csv(rows, fields, filepath):
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    print('读取风险分析主表_v2（含建模特征）...')
    with open(INPUT, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    
    print(f'  总记录: {len(rows)}, 字段: {len(fields)}')
    
    # ========== 版本 A：全样本 ==========
    version_a = rows
    path_a = f'{OUTPUT_DIR}\\政府采购项目风险分析_全样本表.csv'
    write_csv(version_a, fields, path_a)
    print(f'\n版本 A（全样本）: {len(version_a)} 条 -> {path_a}')
    
    # ========== 版本 B：价格有效样本 ==========
    version_b = []
    for row in rows:
        try:
            budget = float(row['预算金额'])
            winning = float(row['中标金额'])
            ratio = float(row['中标/预算比例'])
            if budget > 100 and winning > 100 and 0 < ratio <= 1:
                version_b.append(row)
        except:
            pass
    path_b = f'{OUTPUT_DIR}\\政府采购项目风险分析_价格有效样本表.csv'
    write_csv(version_b, fields, path_b)
    print(f'版本 B（价格有效样本）: {len(version_b)} 条 -> {path_b}')
    
    # ========== 版本 C：服务类主样本 ==========
    version_c = []
    for row in rows:
        if row.get('采购大类') == '服务类' and str(row.get('valid_price_sample', '')) == '1':
            version_c.append(row)
    path_c = f'{OUTPUT_DIR}\\政府采购项目风险分析_服务类主样本表.csv'
    write_csv(version_c, fields, path_c)
    print(f'版本 C（服务类主样本）: {len(version_c)} 条 -> {path_c}')
    
    # ========== 版本 D：2025 Q1 扩展样本 ==========
    version_d = []
    for row in rows:
        if row.get('数据来源') == 'gov_contract_q1_2025':
            version_d.append(row)
    path_d = f'{OUTPUT_DIR}\\政府采购项目风险分析_2025Q1扩展样本表.csv'
    write_csv(version_d, fields, path_d)
    print(f'版本 D（2025 Q1 扩展样本）: {len(version_d)} 条 -> {path_d}')
    
    # ========== 各版本建模特征统计 ==========
    print('\n=== 版本 B - 价格有效样本：风险等级分布 ===')
    dist = {}
    for row in version_b:
        dist[row.get('rule_risk_level', '')] = dist.get(row.get('rule_risk_level', ''), 0) + 1
    for k, v in sorted(dist.items(), key=lambda x: {'正常': 0, '低风险': 1, '中风险': 2, '高风险': 3}.get(x[0], 99)):
        print(f'  {k}: {v}')
    
    print('\n=== 版本 C - 服务类主样本：风险等级分布 ===')
    dist = {}
    for row in version_c:
        dist[row.get('rule_risk_level', '')] = dist.get(row.get('rule_risk_level', ''), 0) + 1
    for k, v in sorted(dist.items(), key=lambda x: {'正常': 0, '低风险': 1, '中风险': 2, '高风险': 3}.get(x[0], 99)):
        print(f'  {k}: {v}')
    
    print('\n=== 版本 C - 服务类主样本：规则触发统计 ===')
    for rule in ['rule_policy_65', 'rule_quantile_10', 'rule_quantile_5', 'rule_iqr', 'rule_robust_z']:
        triggered = sum(1 for r in version_c if r.get(rule) == '1')
        print(f'  {rule}: {triggered}')
    
    print('\n=== 版本 D - 2025 Q1 扩展样本：采购大类分布 ===')
    dist = {}
    for row in version_d:
        dist[row.get('采购大类', '')] = dist.get(row.get('采购大类', ''), 0) + 1
    for k, v in sorted(dist.items(), key=lambda x: -x[1]):
        print(f'  {k}: {v}')
    
    print('\n全部完成。')


if __name__ == '__main__':
    main()
