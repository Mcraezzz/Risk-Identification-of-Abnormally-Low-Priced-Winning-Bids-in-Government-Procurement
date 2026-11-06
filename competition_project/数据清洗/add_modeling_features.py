# -*- coding: utf-8 -*-
# 【数据清洗脚本】为风险分析主表新增建模特征字段：基础价格指标、规则识别、综合风险
import csv
import math
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv'
OUTPUT = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv'

# ============== 统计函数（纯Python实现） ==============
def percentile(values, p):
    """计算列表的 p 分位数 (0-100)"""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return None
    k = (n - 1) * p / 100.0
    f = int(math.floor(k))
    c = min(f + 1, n - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def median(values):
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return None
    if n % 2 == 1:
        return sorted_vals[n // 2]
    return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0


def mad(values):
    """Median Absolute Deviation"""
    med = median(values)
    if med is None:
        return None
    abs_devs = [abs(v - med) for v in values]
    return median(abs_devs)


def compute_group_stats(rows_by_service):
    """按统一服务类别计算分组统计量"""
    stats = {}
    for service, ratios in rows_by_service.items():
        if len(ratios) < 10:
            continue  # 样本量太小，跳过
        
        q10 = percentile(ratios, 10)
        q5 = percentile(ratios, 5)
        med = median(ratios)
        m = mad(ratios)
        q1 = percentile(ratios, 25)
        q3 = percentile(ratios, 75)
        iqr = q3 - q1 if q3 is not None and q1 is not None else 0
        lower_iqr = q1 - 1.5 * iqr if q1 is not None else None
        robust_sd = 1.4826 * m if m and m > 0 else None
        
        stats[service] = {
            'q10': q10,
            'q5': q5,
            'median': med,
            'mad': m,
            'lower_iqr': lower_iqr,
            'robust_sd': robust_sd,
            'count': len(ratios),
        }
    return stats


def main():
    print('读取风险分析主表_v2...')
    with open(INPUT, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    
    print(f'  记录数: {len(rows)}')
    
    # ============== 步骤1：计算基础价格指标 ==============
    print('\n计算基础价格指标...')
    
    # 按统一服务类别收集有效的 price_ratio_clean
    rows_by_service = {}
    for row in rows:
        try:
            ratio = float(row['中标/预算比例'])
            budget = float(row['预算金额'])
            winning = float(row['中标金额'])
            service = row.get('统一服务类别', '其他')
            
            # price_ratio_clean: 只保留 (0, 1] 范围内的值
            if 0 < ratio <= 1:
                row['_price_ratio_clean'] = ratio
                row['_saving_rate_clean'] = 1 - ratio
            else:
                row['_price_ratio_clean'] = None
                row['_saving_rate_clean'] = None
            
            # 对数金额
            if budget > 0:
                row['_log_budget'] = math.log(budget)
            else:
                row['_log_budget'] = None
            
            if winning > 0:
                row['_log_bid'] = math.log(winning)
            else:
                row['_log_bid'] = None
            
            # valid_price_sample
            if budget > 100 and winning > 100 and 0 < ratio <= 1:
                row['_valid_price_sample'] = 1
            else:
                row['_valid_price_sample'] = 0
            
            # 收集有效比例用于分组统计
            if row['_price_ratio_clean'] is not None:
                rows_by_service.setdefault(service, []).append(row['_price_ratio_clean'])
        except:
            row['_price_ratio_clean'] = None
            row['_saving_rate_clean'] = None
            row['_log_budget'] = None
            row['_log_bid'] = None
            row['_valid_price_sample'] = 0
    
    valid_count = sum(1 for r in rows if r['_valid_price_sample'] == 1)
    print(f'  价格有效样本: {valid_count}')
    
    # ============== 步骤2：计算分组统计量 ==============
    print('\n按统一服务类别计算分组统计量...')
    group_stats = compute_group_stats(rows_by_service)
    for service, st in group_stats.items():
        print(f'  {service}: n={st["count"]}, q10={st["q10"]:.4f}, q5={st["q5"]:.4f}, median={st["median"]:.4f}, mad={st["mad"]:.6f}, lower_iqr={st["lower_iqr"]:.4f}')
    
    # ============== 步骤3：计算规则识别字段 ==============
    print('\n计算规则识别字段...')
    for row in rows:
        ratio_clean = row.get('_price_ratio_clean')
        service = row.get('统一服务类别', '其他')
        stats = group_stats.get(service)
        
        # rule_policy_65
        if ratio_clean is not None and ratio_clean < 0.65:
            row['rule_policy_65'] = 1
        else:
            row['rule_policy_65'] = 0
        
        # rule_quantile_10
        if ratio_clean is not None and stats and stats['q10'] is not None:
            row['rule_quantile_10'] = 1 if ratio_clean < stats['q10'] else 0
        else:
            row['rule_quantile_10'] = 0
        
        # rule_quantile_5
        if ratio_clean is not None and stats and stats['q5'] is not None:
            row['rule_quantile_5'] = 1 if ratio_clean < stats['q5'] else 0
        else:
            row['rule_quantile_5'] = 0
        
        # rule_iqr
        if ratio_clean is not None and stats and stats['lower_iqr'] is not None:
            row['rule_iqr'] = 1 if ratio_clean < stats['lower_iqr'] else 0
        else:
            row['rule_iqr'] = 0
        
        # rule_robust_z
        if ratio_clean is not None and stats and stats['robust_sd'] is not None and stats['robust_sd'] > 0:
            z = (ratio_clean - stats['median']) / stats['robust_sd']
            row['rule_robust_z'] = 1 if z < -3 else 0
        else:
            row['rule_robust_z'] = 0
    
    # ============== 步骤4：计算综合风险字段 ==============
    print('\n计算综合风险字段...')
    risk_counts = {'正常': 0, '低风险': 0, '中风险': 0, '高风险': 0}
    
    for row in rows:
        score = (row['rule_policy_65'] + row['rule_quantile_10'] + 
                 row['rule_quantile_5'] + row['rule_iqr'] + row['rule_robust_z'])
        row['rule_risk_score'] = score
        
        if score == 0:
            level = '正常'
        elif score == 1:
            level = '低风险'
        elif score == 2:
            level = '中风险'
        else:
            level = '高风险'
        row['rule_risk_level'] = level
        risk_counts[level] = risk_counts.get(level, 0) + 1
        
        row['is_suspicious_low_price'] = 1 if score >= 1 else 0
        row['is_high_risk_low_price'] = 1 if level == '高风险' else 0
    
    # ============== 步骤5：整理输出字段 ==============
    new_fields = [
        'price_ratio_clean', 'saving_rate_clean', 'log_budget', 'log_bid', 'valid_price_sample',
        'rule_policy_65', 'rule_quantile_10', 'rule_quantile_5', 'rule_iqr', 'rule_robust_z',
        'rule_risk_score', 'rule_risk_level', 'is_suspicious_low_price', 'is_high_risk_low_price'
    ]
    
    # 移除可能已存在的旧字段
    cleaned_fields = [f for f in fields if f not in new_fields]
    
    # 在合适的位置插入新字段（在 小金额标记 之后）
    insert_after = '小金额标记'
    if insert_after in cleaned_fields:
        idx = cleaned_fields.index(insert_after)
        final_fields = cleaned_fields[:idx+1] + new_fields + cleaned_fields[idx+1:]
    else:
        final_fields = cleaned_fields + new_fields
    
    print(f'\n输出字段数: {len(final_fields)}')
    
    # ============== 步骤6：写入输出 ==============
    print('写入更新后的主表...')
    with open(OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=final_fields)
        writer.writeheader()
        for row in rows:
            # 将临时字段转为正式字段
            row['price_ratio_clean'] = row.get('_price_ratio_clean', '') if row.get('_price_ratio_clean') is not None else ''
            row['saving_rate_clean'] = row.get('_saving_rate_clean', '') if row.get('_saving_rate_clean') is not None else ''
            row['log_budget'] = row.get('_log_budget', '') if row.get('_log_budget') is not None else ''
            row['log_bid'] = row.get('_log_bid', '') if row.get('_log_bid') is not None else ''
            row['valid_price_sample'] = row.get('_valid_price_sample', 0)
            
            # 清理临时字段，避免写入输出
            for key in list(row.keys()):
                if key.startswith('_'):
                    del row[key]
            
            writer.writerow(row)
    
    print(f'\n完成。输出: {OUTPUT}')
    print(f'\n风险等级分布:')
    for level, cnt in risk_counts.items():
        print(f'  {level}: {cnt}')
    
    print(f'\n规则触发统计:')
    for rule in ['rule_policy_65', 'rule_quantile_10', 'rule_quantile_5', 'rule_iqr', 'rule_robust_z']:
        triggered = sum(1 for r in rows if r.get(rule) == 1)
        print(f'  {rule}: {triggered}')


if __name__ == '__main__':
    main()
