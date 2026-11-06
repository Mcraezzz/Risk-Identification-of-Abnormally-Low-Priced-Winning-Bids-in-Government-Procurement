# -*- coding: utf-8 -*-
"""
清洗两个政府采购数据集并构造风险分析主表
"""
import csv
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# ============== 配置 ==============
MERGED_CSV = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.csv'
SAMPLE_CSV = r'C:\Users\22672\Desktop\统计建模原数据\government_contract_q1_2025_sample_4500_服务类型.csv'
OUTPUT_CSV = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'

# 金额异常阈值（超过则认为异常）
BUDGET_MAX = 1e15  # 预算金额超过此值视为异常
WINNING_MAX = 1e12  # 中标金额超过此值视为异常

# ============== 省份映射 ==============
CITY_PROVINCE_MAP = {
    '深圳': '广东',
    '青岛': '山东',
    '厦门': '福建',
    '宁波': '浙江',
    '大连': '辽宁',
}

# ============== 采购方式标准化 ==============
METHOD_KEYWORDS = {
    '公开招标': ['公开招标', '公开 招标'],
    '竞争性磋商': ['竞争性磋商'],
    '竞争性谈判': ['竞争性谈判'],
    '单一来源': ['单一来源'],
    '框架协议': ['框架协议'],
    '电子卖场': ['电子卖场'],
    '询价': ['询价'],
    '邀请招标': ['邀请招标'],
    '定点采购': ['定点采购'],
}

def normalize_method(raw):
    if not raw or not str(raw).strip():
        return '其他'
    raw_str = str(raw).strip()
    for standard, keywords in METHOD_KEYWORDS.items():
        for kw in keywords:
            if kw in raw_str:
                return standard
    return '其他'

# ============== 服务类别 -> 采购大类 & 统一服务类别 ==============
# 合并数据集的7个类别
MERGED_CATEGORY_MAP = {
    '物业管理服务': ('服务类', '物业'),
    '保洁服务': ('服务类', '保洁'),
    '绿化服务': ('服务类', '运维'),
    '安保服务': ('服务类', '安保'),
    '餐饮服务': ('服务类', '餐饮'),
    '信息化服务': ('服务类', '信息化'),
    '运维服务': ('服务类', '运维'),
}

# 4500样本的30+个类别
SAMPLE_CATEGORY_MAP = {
    '物业管理服务': ('服务类', '物业'),
    '保洁服务': ('服务类', '保洁'),
    '安保服务': ('服务类', '安保'),
    '餐饮服务': ('服务类', '餐饮'),
    '信息技术服务-运维/网络/云服务': ('服务类', '运维'),
    '信息技术服务-软件/系统开发': ('服务类', '信息化'),
    '计算机/信息化设备采购': ('货物类', '信息化'),
    '软件产品采购': ('货物类', '信息化'),
    '园林绿化服务/工程': ('工程类', '运维'),
    '工程施工/修缮装修': ('工程类', '工程'),
    '车辆维修保养服务': ('服务类', '车辆服务'),
    '车辆加油/能源服务': ('服务类', '车辆服务'),
    '车辆租赁/运输服务': ('服务类', '车辆服务'),
    '车辆采购': ('货物类', '车辆服务'),
    '咨询评估审计法律服务': ('服务类', '咨询检测'),
    '鉴定检测测绘服务': ('服务类', '咨询检测'),
    '办公耗材采购': ('货物类', '其他'),
    '办公设备采购': ('货物类', '其他'),
    '家具用具采购': ('货物类', '其他'),
    '医疗设备采购': ('货物类', '其他'),
    '消防/应急装备采购': ('货物类', '其他'),
    'LED/显示音视频设备采购': ('货物类', '其他'),
    '空调/电器设备采购': ('货物类', '其他'),
    '仪器仪表/科研设备采购': ('货物类', '其他'),
    '印刷出版服务': ('服务类', '其他'),
    '图书/文体用品采购': ('货物类', '其他'),
    '服装被装采购': ('货物类', '其他'),
    '食品食材供应/配送': ('货物类', '其他'),
    '保险服务': ('服务类', '其他'),
    '其他服务': ('服务类', '其他'),
}

def classify_service(category, dataset='merged'):
    """根据服务类别返回 (采购大类, 统一服务类别)"""
    if not category:
        return ('其他', '其他')
    cat = str(category).strip()
    if dataset == 'merged':
        return MERGED_CATEGORY_MAP.get(cat, ('其他', '其他'))
    else:
        return SAMPLE_CATEGORY_MAP.get(cat, ('其他', '其他'))


# ============== 金额清洗 ==============
def is_amount_valid(val, max_val=None):
    if val is None or str(val).strip() == '' or str(val).strip() == 'None':
        return False
    try:
        v = float(val)
        if v < 0:
            return False
        if max_val and v > max_val:
            return False
        return True
    except:
        return False


def is_winning_valid(val):
    """中标金额必须 > 0"""
    if not is_amount_valid(val, WINNING_MAX):
        return False
    try:
        return float(val) > 0
    except:
        return False


# ============== 读取数据 ==============
def read_csv_file(path, encoding):
    with open(path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        return list(reader)


# ============== 主流程 ==============
def main():
    print('=== 开始数据清洗与合并 ===\n')
    
    # 1. 读取两个数据集
    print('读取合并数据集...')
    merged_rows = read_csv_file(MERGED_CSV, 'gb18030')
    print(f'  原始记录: {len(merged_rows)}')
    
    print('读取4500样本数据集...')
    sample_rows = read_csv_file(SAMPLE_CSV, 'utf-8-sig')
    print(f'  原始记录: {len(sample_rows)}')
    
    # 2. 定义输出字段
    output_fields = [
        '数据来源', '记录ID', '公告标题', '公告链接', '发布日期',
        '项目省份', '项目城市', '项目编号', '项目名称',
        '采购人名称', '代理机构名称',
        '原始供应商名称', '统一供应商名称',
        '预算金额', '中标金额', '中标/预算比例', '节约率',
        '采购方式', '采购方式标准化',
        '服务期限', '服务类别',
        '采购大类', '统一服务类别',
        '是否跨省中标',
        '公告来源', '公告正文'
    ]
    
    cleaned_rows = []
    stats = {
        'merged_total': len(merged_rows),
        'sample_total': len(sample_rows),
        'merged_removed': 0,
        'sample_removed': 0,
        'merged_kept': 0,
        'sample_kept': 0,
    }
    
    # 3. 处理合并数据集
    print('\n清洗合并数据集...')
    for row in merged_rows:
        # 检查金额有效性
        if not is_amount_valid(row.get('预算金额'), BUDGET_MAX):
            stats['merged_removed'] += 1
            continue
        if not is_winning_valid(row.get('中标金额')):
            stats['merged_removed'] += 1
            continue
        
        # 标准化省份
        province = str(row.get('项目省份', '') or '').strip()
        if province in CITY_PROVINCE_MAP:
            province = CITY_PROVINCE_MAP[province]
        
        # 标准化采购方式
        raw_method = row.get('采购方式', '')
        norm_method = normalize_method(raw_method)
        
        # 统一供应商名称（如为空则使用原始供应商名称）
        unified_supplier = row.get('统一供应商名称', '') or row.get('原始供应商名称', '')
        
        # 服务类别映射
        category = row.get('服务类别', '')
        procurement_type, unified_service = classify_service(category, 'merged')
        
        new_row = {
            '数据来源': 'ccgp_merged',
            '记录ID': row.get('记录ID', ''),
            '公告标题': row.get('公告标题', ''),
            '公告链接': row.get('公告链接', ''),
            '发布日期': row.get('发布日期', ''),
            '项目省份': province,
            '项目城市': row.get('项目城市', ''),
            '项目编号': row.get('项目编号', ''),
            '项目名称': row.get('项目名称', ''),
            '采购人名称': row.get('采购人名称', ''),
            '代理机构名称': row.get('代理机构名称', ''),
            '原始供应商名称': row.get('原始供应商名称', ''),
            '统一供应商名称': unified_supplier,
            '预算金额': row.get('预算金额', ''),
            '中标金额': row.get('中标金额', ''),
            '中标/预算比例': row.get('中标/预算比例', ''),
            '节约率': row.get('节约率', ''),
            '采购方式': raw_method,
            '采购方式标准化': norm_method,
            '服务期限': row.get('服务期限', ''),
            '服务类别': category,
            '采购大类': procurement_type,
            '统一服务类别': unified_service,
            '是否跨省中标': row.get('是否跨省中标', ''),
            '公告来源': row.get('公告来源', ''),
            '公告正文': row.get('公告正文', ''),
        }
        cleaned_rows.append(new_row)
        stats['merged_kept'] += 1
    
    # 4. 处理4500样本数据集
    print('清洗4500样本数据集...')
    for row in sample_rows:
        # 检查金额有效性
        if not is_amount_valid(row.get('预算金额'), BUDGET_MAX):
            stats['sample_removed'] += 1
            continue
        if not is_winning_valid(row.get('中标金额')):
            stats['sample_removed'] += 1
            continue
        
        # 标准化省份
        province = str(row.get('项目省份', '') or '').strip()
        if province in CITY_PROVINCE_MAP:
            province = CITY_PROVINCE_MAP[province]
        
        # 标准化采购方式
        raw_method = row.get('采购方式', '')
        norm_method = normalize_method(raw_method)
        
        # 统一供应商名称（4500数据集没有该字段，使用原始供应商名称）
        unified_supplier = row.get('原始供应商名称', '')
        
        # 服务类别映射（优先使用"服务类型"字段，若为空则使用"服务类别"）
        category = row.get('服务类型', '') or row.get('服务类别', '')
        procurement_type, unified_service = classify_service(category, 'sample')
        
        new_row = {
            '数据来源': 'gov_contract_q1_2025',
            '记录ID': row.get('记录ID', ''),
            '公告标题': row.get('公告标题', ''),
            '公告链接': row.get('公告链接', ''),
            '发布日期': row.get('发布日期', ''),
            '项目省份': province,
            '项目城市': row.get('项目城市', ''),
            '项目编号': row.get('项目编号', ''),
            '项目名称': row.get('项目名称', ''),
            '采购人名称': row.get('采购人名称', ''),
            '代理机构名称': row.get('代理机构名称', ''),
            '原始供应商名称': row.get('原始供应商名称', ''),
            '统一供应商名称': unified_supplier,
            '预算金额': row.get('预算金额', ''),
            '中标金额': row.get('中标金额', ''),
            '中标/预算比例': row.get('中标/预算比例', ''),
            '节约率': row.get('节约率', ''),
            '采购方式': raw_method,
            '采购方式标准化': norm_method,
            '服务期限': row.get('服务期限', ''),
            '服务类别': category,
            '采购大类': procurement_type,
            '统一服务类别': unified_service,
            '是否跨省中标': row.get('是否跨省中标', ''),
            '公告来源': row.get('公告来源', ''),
            '公告正文': row.get('公告正文', ''),
        }
        cleaned_rows.append(new_row)
        stats['sample_kept'] += 1
    
    # 5. 写入输出
    print(f'\n写入风险分析主表...')
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        for row in cleaned_rows:
            writer.writerow(row)
    
    # 6. 统计报告
    print('\n=== 清洗统计 ===')
    print(f"合并数据集: 原始 {stats['merged_total']}, 剔除 {stats['merged_removed']}, 保留 {stats['merged_kept']}")
    print(f"4500样本: 原始 {stats['sample_total']}, 剔除 {stats['sample_removed']}, 保留 {stats['sample_kept']}")
    print(f"风险分析主表总记录: {len(cleaned_rows)}")
    
    # 分布统计
    print('\n=== 采购方式标准化分布 ===')
    method_dist = {}
    for row in cleaned_rows:
        m = row['采购方式标准化']
        method_dist[m] = method_dist.get(m, 0) + 1
    for m, c in sorted(method_dist.items(), key=lambda x: -x[1]):
        print(f'  {m}: {c}')
    
    print('\n=== 采购大类分布 ===')
    type_dist = {}
    for row in cleaned_rows:
        t = row['采购大类']
        type_dist[t] = type_dist.get(t, 0) + 1
    for t, c in sorted(type_dist.items(), key=lambda x: -x[1]):
        print(f'  {t}: {c}')
    
    print('\n=== 统一服务类别分布 ===')
    svc_dist = {}
    for row in cleaned_rows:
        s = row['统一服务类别']
        svc_dist[s] = svc_dist.get(s, 0) + 1
    for s, c in sorted(svc_dist.items(), key=lambda x: -x[1]):
        print(f'  {s}: {c}')
    
    print(f'\n输出文件: {OUTPUT_CSV}')


if __name__ == '__main__':
    main()
