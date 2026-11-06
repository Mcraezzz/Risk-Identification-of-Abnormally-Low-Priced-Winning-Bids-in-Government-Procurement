# -*- coding: utf-8 -*-
# 【数据清洗脚本】将2024省级宏观指标合并到风险分析主表
# 生成日期: 2026-05-10

"""
将 2024 省级宏观指标合并到风险分析主表
"""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

MAIN_TABLE = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'
INDICATORS = r'C:\Users\22672\Desktop\统计建模原数据\provincial_indicators_2024.csv'
OUTPUT = r'C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表.csv'

# 省份名称标准化：将指标文件中的完整名称映射到主表中的简称
PROVINCE_NORMALIZE = {
    '北京市': '北京',
    '天津市': '天津',
    '河北省': '河北',
    '山西省': '山西',
    '内蒙古自治区': '内蒙古',
    '辽宁省': '辽宁',
    '吉林省': '吉林',
    '黑龙江省': '黑龙江',
    '上海市': '上海',
    '江苏省': '江苏',
    '浙江省': '浙江',
    '安徽省': '安徽',
    '福建省': '福建',
    '江西省': '江西',
    '山东省': '山东',
    '河南省': '河南',
    '湖北省': '湖北',
    '湖南省': '湖南',
    '广东省': '广东',
    '广西壮族自治区': '广西',
    '海南省': '海南',
    '重庆市': '重庆',
    '四川省': '四川',
    '贵州省': '贵州',
    '云南省': '云南',
    '西藏自治区': '西藏',
    '陕西省': '陕西',
    '甘肃省': '甘肃',
    '青海省': '青海',
    '宁夏回族自治区': '宁夏',
    '新疆维吾尔自治区': '新疆',
}


def normalize_province(p):
    return PROVINCE_NORMALIZE.get(p, p)


def main():
    print('读取省级宏观指标...')
    with open(INDICATORS, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        indicator_rows = list(reader)
    
    # Build province -> indicators mapping
    province_indicators = {}
    for row in indicator_rows:
        raw_prov = row['province']
        norm_prov = normalize_province(raw_prov)
        province_indicators[norm_prov] = row
    
    print(f'  指标覆盖省份: {len(province_indicators)}')
    
    # Read main table
    print('读取风险分析主表...')
    with open(MAIN_TABLE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        main_rows = list(reader)
        main_fields = reader.fieldnames
    
    print(f'  主表记录数: {len(main_rows)}')
    print(f'  当前字段数: {len(main_fields)}')
    
    # Define new indicator fields to add
    indicator_fields = [
        'gdp', 'population', 'gdp_per_capita', 'fiscal_revenue',
        'fiscal_expenditure', 'fiscal_pressure', 'average_wage',
        'tertiary_value_added', 'tertiary_industry_share',
        'urban_population', 'urbanization_rate'
    ]
    
    # Remove any existing indicator fields to avoid duplication
    cleaned_fields = [f for f in main_fields if f not in indicator_fields]
    
    # Add new fields at the correct position (after 是否跨省中标)
    if '是否跨省中标' in cleaned_fields:
        insert_pos = cleaned_fields.index('是否跨省中标') + 1
        new_fields = cleaned_fields[:insert_pos] + indicator_fields + cleaned_fields[insert_pos:]
    else:
        # Fallback: append before 公告来源 and 公告正文 if they exist
        if '公告来源' in cleaned_fields and '公告正文' in cleaned_fields:
            idx = cleaned_fields.index('公告来源')
            new_fields = cleaned_fields[:idx] + indicator_fields + cleaned_fields[idx:]
        else:
            new_fields = cleaned_fields + indicator_fields
    
    print(f'  去重后字段数: {len(cleaned_fields)}')
    print(f'  最终字段数: {len(new_fields)}')
    
    # Merge
    print('合并数据...')
    merged_count = 0
    unmatched_provinces = set()
    output_rows = []
    
    for row in main_rows:
        prov = row.get('项目省份', '')
        # 新疆生产建设兵团使用新疆指标
        lookup_prov = '新疆' if prov == '新疆生产建设兵团' else prov
        indicators = province_indicators.get(lookup_prov)
        
        new_row = {}
        # First copy only the cleaned fields
        for field in cleaned_fields:
            new_row[field] = row.get(field, '')
        
        # Then add indicator fields
        if indicators:
            for field in indicator_fields:
                new_row[field] = indicators.get(field, '')
            merged_count += 1
        else:
            for field in indicator_fields:
                new_row[field] = ''
            if prov and prov != '新疆生产建设兵团':
                unmatched_provinces.add(prov)
        
        output_rows.append(new_row)
    
    print(f'  成功匹配: {merged_count} 条')
    if unmatched_provinces:
        print(f'  未匹配省份: {sorted(unmatched_provinces)}')
    
    # Write output
    print('写入更新后的风险分析主表...')
    with open(OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fields)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)
    
    print(f'完成。输出文件: {OUTPUT}')
    print(f'总字段数: {len(new_fields)}')
    print(f'新增强度指标字段: {indicator_fields}')


if __name__ == '__main__':
    main()
