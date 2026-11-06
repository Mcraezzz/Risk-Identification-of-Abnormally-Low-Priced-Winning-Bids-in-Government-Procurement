# -*- coding: utf-8 -*-
"""
为数据清洗相关Python脚本批量添加中文说明头
"""
import os

base_dir = r'C:\Users\22672\Desktop\统计建模原数据'

file_descriptions = {
    'analyze_abnormal.py': '数据分析脚本：检查政府采购数据集中中标/预算比例的异常值',
    'analyze_abnormal2.py': '数据分析脚本：详细分析中标/预算比例的异常分布情况',
    'analyze_abnormal3.py': '数据分析脚本：分析预算金额和中标金额的异常记录',
    'analyze_distribution.py': '数据分析脚本：统计中标/预算比例在各区间段的分布',
    'check_encoding.py': '数据预处理脚本：检测CSV文件的字符编码格式',
    'clean_and_merge.py': '【数据清洗主脚本】清洗两个政府采购数据集，标准化字段，构造风险分析主表',
    'explore_4500_service.py': '数据探索脚本：查看4500样本数据集的字段结构和服务类型分布',
    'explore_merged.py': '数据探索脚本：查看合并后数据集的基本结构和样本数据',
    'explore_merged2.py': '数据探索脚本：探测合并数据集CSV文件的字符编码',
    'explore_merged3.py': '数据探索脚本：分析合并数据集的采购方式、省份、服务类别分布',
    'explore_service_type.py': '数据探索脚本：查看服务类型CSV文件的字段和样本数据',
    'merge_awards.py': '数据合并脚本：将ccgp_info_service_awards数据合并到supplier_credit并补全缺失字段',
    'merge_indicators.py': '【数据清洗脚本】将2024省级宏观指标合并到风险分析主表',
    'process_contract.py': '【数据清洗脚本】处理政府合同CSV：字段中文改名、增加是否跨省中标字段',
    'verify_final.py': '数据验证脚本：验证最终风险分析主表的字段结构和指标合并结果',
    'verify_output.py': '数据验证脚本：验证清洗后输出文件的结构和记录数',
    'verify_output2.py': '数据验证脚本：验证省份映射、服务类别映射和4500样本映射结果',
    'verify_provinces.py': '数据验证脚本：验证清洗后项目省份的分布情况',
    'verify_removals.py': '数据验证脚本：统计被删除的异常记录数量和原因',
    'xlsx_to_csv.py': '格式转换脚本：将Excel文件转换为CSV格式',
}

for filename, description in file_descriptions.items():
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        print(f'跳过（不存在）: {filename}')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有中文说明头
    if '【数据' in content or '数据清洗' in content or '数据探索' in content or '数据验证' in content or '数据分析' in content:
        print(f'已存在标记，跳过: {filename}')
        continue
    
    # 构建中文说明头
    header = f"# -*- coding: utf-8 -*-\n# {description}\n# 生成日期: 2026-05-10\n\n"
    
    # 如果文件已有编码声明，替换它；否则在开头插入
    if content.startswith('# -*- coding: utf-8 -*-'):
        content = header + content[len('# -*- coding: utf-8 -*-'):].lstrip('\n')
    else:
        content = header + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'已添加中文标记: {filename}')

print('\n全部处理完成。')
