# -*- coding: utf-8 -*-
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

src = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版v4.docx'
dst = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_最终版.docx'

doc = Document(src)

# 在多个可靠位置追加内容
additions = [
    {
        'search': '此外，将自然语言处理中的预训练语言模型引入公告文本分析',
        'text': '在可视化呈现方面，本研究中的网络拓扑图和热力图等复杂图形亦可借助Matlab实现更高精度的科学绘图，研究者可根据具体展示需求在Python与Matlab之间择优选择，以保证图形的学术规范性和可读性。'
    },
    {
        'search': '本研究的局限也值得正视：一是异常低价标签本质上是基于统计规则和异常检测的"风险标签"',
        'text': '从方法迭代角度看，未来可考虑将时间序列分析和动态网络模型纳入研究框架，以观察供应商中标行为、价格走势和关系结构的演化规律；同时，随着政府采购数据质量的持续提升，深度学习模型在公告文本语义理解中的应用前景亦值得关注。'
    },
    {
        'search': '一是价格偏离是出现频率最高的核心线索',
        'text': '同时应注意到，QCA路径对前因变量的校准方式较为敏感，不同的分位数切点可能导致路径组合变化，因此在应用于监管决策时，建议将QCA结果与专家经验和历史案例库进行交叉验证，避免过度依赖单一路径解释。'
    },
]

for add in additions:
    found = False
    for para in doc.paragraphs:
        if add['search'] in para.text:
            # 创建新段落
            new_p = OxmlElement('w:p')
            new_r = OxmlElement('w:r')
            new_t = OxmlElement('w:t')
            new_t.set(qn('xml:space'), 'preserve')
            new_t.text = add['text']
            new_r.append(new_t)
            new_p.append(new_r)
            para._p.addnext(new_p)
            found = True
            break
    if not found:
        print(f"Not found: {add['search'][:40]}")

total = sum(len(p.text) for p in doc.paragraphs)
print(f'Total chars: {total}')

doc.save(dst)
print(f'Saved to: {dst}')
