# -*- coding: utf-8 -*-
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

src = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版.docx'
dst = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版v3.docx'

doc = Document(src)
body = doc.element.body
children = list(body)

# 精确匹配表格前的段落文本（完整标题）
target_prev_texts = {
    '表2 字段结构说明表': '数据清洗后的字段可归纳为公告文本、价格、采购主体、类型、地区、宏观和规则风险七大类，分别用于文本特征、价格规则、供应商画像、分组比较、地区差异和异常标签构造。',
    '表8 文本预处理规则表': '文本预处理包括文本合并（公告标题+项目名称+公告正文+服务类别+采购方式）、字符清洗（保留中英文数字）、jieba分词、停用词删除、TF-IDF降维和LDA主题提取六个环节。',
    '表10 供应商画像字段表': '供应商画像从中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险分六个维度刻画供应商的活跃度、价格行为和跨区域特征。',
    '表11 异常检测模型参数表': '异常检测模型中，Isolation Forest通过随机特征切分隔离异常点，LOF基于局部密度偏离识别异常，One-Class SVM学习正常样本边界；三者集成后取标准化得分的加权平均。',
    '表18 网络节点与边定义表': '供应商—采购人二部网络以统一供应商名称和采购人名称为节点，中标交易关系为边，边权为交易项目数量；网络指标包括加权度、度中心性、介数中心性、特征向量中心性和Louvain社群。',
}

deleted = 0
for i, child in enumerate(children):
    if child.tag.endswith('tbl'):
        # 找前一个非空段落
        prev_text = ""
        for j in range(i-1, -1, -1):
            if children[j].tag.endswith('p'):
                t = children[j].text or ""
                if t.strip():
                    prev_text = t.strip()
                    break
        if prev_text in target_prev_texts:
            p = OxmlElement('w:p')
            r = OxmlElement('w:r')
            t = OxmlElement('w:t')
            t.set(qn('xml:space'), 'preserve')
            t.text = target_prev_texts[prev_text]
            r.append(t)
            p.append(r)
            child.addprevious(p)
            body.remove(child)
            deleted += 1
            print(f"Deleted and replaced: {prev_text}")

print(f'Total deleted tables: {deleted}')
doc.save(dst)
print(f'Saved to: {dst}')
