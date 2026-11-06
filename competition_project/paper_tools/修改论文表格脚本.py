# -*- coding: utf-8 -*-
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

src = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版.docx'
dst = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版v2.docx'

doc = Document(src)

# 辅助函数：在指定元素前插入段落
def insert_paragraph_before(element, text, style='Normal'):
    p = OxmlElement('w:p')
    r = OxmlElement('w:r')
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    p.append(r)
    element.addprevious(p)
    return p

# 辅助函数：删除表格
def delete_table(table):
    tbl = table._tbl
    tbl.getparent().remove(tbl)

# 我们需要遍历body的children，找到表格并判断其对应标题
# 策略：查找每个表格前的段落文本，根据关键词判断表格身份
body = doc.element.body
children = list(body)

# 记录表格索引和前文信息
table_info = []
tbl_idx = 0
for i, child in enumerate(children):
    if child.tag.endswith('tbl'):
        # 找前一个段落
        prev_text = ""
        for j in range(i-1, -1, -1):
            if children[j].tag.endswith('p'):
                prev_text = children[j].text or ""
                if prev_text.strip():
                    break
        table_info.append((tbl_idx, prev_text.strip(), child))
        tbl_idx += 1

print(f'Found {len(table_info)} tables')

# 定义要删除的表格及替代文字
# 根据前文关键词匹配
delete_rules = [
    {
        'keywords': ['字段结构说明表', '表2'],
        'replace_text': '数据清洗后的字段可归纳为公告文本、价格、采购主体、类型、地区、宏观和规则风险七大类，分别用于文本特征、价格规则、供应商画像、分组比较、地区差异和异常标签构造。',
        'reason': '表2字段结构说明表'
    },
    {
        'keywords': ['文本预处理规则表', '表8'],
        'replace_text': '文本预处理包括文本合并（公告标题+项目名称+公告正文+服务类别+采购方式）、字符清洗（保留中英文数字）、jieba分词、停用词删除、TF-IDF降维和LDA主题提取六个环节。',
        'reason': '表8文本预处理规则表'
    },
    {
        'keywords': ['供应商画像字段表', '表10'],
        'replace_text': '供应商画像从中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险分六个维度刻画供应商的活跃度、价格行为和跨区域特征。',
        'reason': '表10供应商画像字段表'
    },
    {
        'keywords': ['异常检测模型参数表', '表11'],
        'replace_text': '异常检测模型中，Isolation Forest通过随机特征切分隔离异常点，LOF基于局部密度偏离识别异常，One-Class SVM学习正常样本边界；三者集成后取标准化得分的加权平均。',
        'reason': '表11异常检测模型参数表'
    },
    {
        'keywords': ['网络节点与边定义表', '表18'],
        'replace_text': '供应商—采购人二部网络以统一供应商名称和采购人名称为节点，中标交易关系为边，边权为交易项目数量；网络指标包括加权度、度中心性、介数中心性、特征向量中心性和Louvain社群。',
        'reason': '表18网络节点与边定义表'
    },
]

deleted = 0
for tbl_idx, prev_text, child in table_info:
    for rule in delete_rules:
        matched = any(kw in prev_text for kw in rule['keywords'])
        if matched:
            insert_paragraph_before(child, rule['replace_text'], 'Normal')
            body.remove(child)
            deleted += 1
            print(f"Deleted: {rule['reason']} (prev: {prev_text[:40]}...)")
            break

print(f'Total deleted tables: {deleted}')

# 保存
doc.save(dst)
print(f'Saved to: {dst}')
