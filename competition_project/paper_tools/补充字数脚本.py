# -*- coding: utf-8 -*-
from docx import Document

src = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版v4.docx'
dst = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_修改版v5.docx'

doc = Document(src)

insertions = [
    {
        'after_text': '在监管应用角度看，SHAP输出的核心价值在于将黑箱预测转化为可复核的证据链。',
        'insert_text': '在可视化呈现方面，本研究中的部分复杂网络图和三维关系图亦可借助Matlab实现更高精度的科学绘图，研究者可根据具体展示需求在Python与Matlab之间择优选择，以保证图形的学术规范性和可读性。'
    },
    {
        'after_text': '这说明监管不宜只设置单一价格阈值，而应识别多条件叠加下的风险路径。',
        'insert_text': '需要进一步指出的是，QCA路径结果对校准阈值和条件选择较为敏感，不同的一致性门槛可能导致路径组合变化，因此在监管应用中应将QCA结果视为启发式线索，结合领域专家判断进行动态调整。'
    },
    {
        'after_text': '第三，关系网络以供应商—采购人为主，未来可进一步扩展到代理机构、评审专家和信用处罚信息。',
        'insert_text': '此外，将自然语言处理中的预训练语言模型引入公告文本分析，有望进一步提升文本特征对采购需求结构和限制性条款的识别精度，从而为异常低价风险识别提供更为丰富的语义层面证据。'
    },
]

for rule in insertions:
    found = False
    for para in doc.paragraphs:
        if rule['after_text'] in para.text:
            new_para = para.insert_paragraph_before(rule['insert_text'])
            para._p.addnext(new_para._p)
            found = True
            break
    if not found:
        print(f"Warning: not found: {rule['after_text'][:40]}...")

total = sum(len(p.text) for p in doc.paragraphs)
print(f'Total chars: {total}')

doc.save(dst)
print(f'Saved to: {dst}')
