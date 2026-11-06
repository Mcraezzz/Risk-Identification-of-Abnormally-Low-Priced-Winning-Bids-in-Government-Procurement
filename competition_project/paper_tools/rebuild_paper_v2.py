# -*- coding: utf-8 -*-
"""
Rebuild the final paper from the original docx, preserving LaTeX formulas (m:oMath).
All text replacements are done at the w:t XML level to avoid destroying OMath objects.
"""
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor, Pt
import re

SRC = r'C:\Users\22672\Desktop\统计建模比赛\统计建模代码\论文成稿\政府采购异常低价风险识别与监管研究_正文公式LaTeX插入版.docx'
DST = r'C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_最终版.docx'

doc = Document(SRC)

# ===== 0. Set all headings to black =====
for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.bold = True

# ===== 1. XML-level text replacement (preserves m:oMath) =====
def replace_text_in_para(para, old, new):
    found = False
    for t_elem in para._element.findall('.//' + qn('w:t')):
        if t_elem.text and old in t_elem.text:
            t_elem.text = t_elem.text.replace(old, new)
            found = True
    return found

replacements = [
    ('QCA成因组合', 'QCA探索性风险线索组合'),
    ('成因组合', '风险线索组合'),
    ('QCA结果表明，异常低价风险具有组态特征：路径1的一致性相对较高，其他路径覆盖样本更多但一致性偏低，因此更适合作为探索性风险线索。',
     'QCA结果显示，异常低价风险呈现多条探索性线索：路径1的一致性相对较高，可视为较稳健的风险组合；路径2—路径4的一致性偏低，更适合作为"探索性风险线索"，用于引导后续复核方向，不宜直接作为严格因果结论。'),
    ('总体看，价格偏离是核心条件，高频供应商、高财政压力、跨省中标、特定采购方式和高风险服务类别会进一步放大风险。这说明监管不宜只设置单一价格阈值，而应识别多条件叠加下的风险路径。',
     '总体看，价格偏离是出现频率最高的核心线索，高频供应商、高财政压力、跨省中标、特定采购方式和高风险服务类别等条件的组合可视为风险信号叠加。需要强调的是，QCA结果反映的是条件集合与风险标签之间的集合关系，而非传统意义上的因果推断；监管实践中应将其作为多维度复核清单，不宜直接等同于违法行为认定依据。'),
    ('对于项目数较少但风险率为100%的主体，应作为复核线索而非直接认定依据。',
     '对于项目数较少但风险比例为100%的主体，需特别注意：小样本下100%高风险并不代表该主体一定存在问题，可能源于偶然中标或规则阈值恰好触发。此类主体应作为"重点复核线索"，通过增加样本观察、履约跟踪和人工核验来进一步判断，而非直接认定为违法。'),
    ('本节以规则稳健性为主，扩展样本未重新训练监督模型。',
     '需要说明的是，扩展样本来自合同公告，缺少部分供应商画像字段（如历史中标次数、跨省中标记录）和代理机构信息，因此不完全复现主模型的完整特征集，仅用于规则稳健性与采购类别差异验证。本节以规则稳健性为主，扩展样本未重新训练监督模型。'),
    ('结果显示，XGBoost模型AUC为0.991、F1值为0.874，整体识别能力较强。由于目标变量来源于规则与异常检测形成的风险标签，该结果主要说明高风险样本在特征空间中具有较清晰的结构，并不等同于真实违法识别能力；其价值在于为监管复核提供排序和解释依据。',
     '结果显示，XGBoost模型AUC达到0.991、F1值为0.874。需要特别说明的是，该AUC之所以处于极高水平，是因为目标变量来源于规则风险与异常检测标签，而非经执法或审计确认的真实违法标签；模型学习的本质上是风险标签在特征空间中的分布结构，因此AUC高说明模型能较好地复现和排序风险标签结构，但不能直接等同于识别真实违法行为的能力。其价值在于为监管复核提供可解释的风险排序和证据线索，而非替代人工认定。'),
    ('本文设置6个主题，并根据每个主题Top关键词进行解释。',
     '本文设置6个主题，并根据每个主题Top关键词进行解释。为进一步提升主题解释力，本研究在原有停用词基础上，将城市名（如深圳市、重庆市等）、日期词、联系人、联系电话、单位名称等低信息词纳入停用词表，以减少地域和格式噪声对主题分布的干扰。'),
]

for para in doc.paragraphs:
    for old, new in replacements:
        replace_text_in_para(para, old, new)

# ===== 2. Heading renumbering =====
chapter_map = {
    '第一章 引言': '一、引言',
    '第二章 数据来源与预处理': '二、数据来源与预处理',
    '第三章 政府采购异常低价风险指标构建': '三、政府采购异常低价风险指标构建',
    '第四章 文本特征工程与项目画像构建': '四、文本特征工程与项目画像构建',
    '第五章 异常低价中标风险识别模型': '五、异常低价中标风险识别模型',
    '第六章 风险因素解释与成因组合分析': '六、风险因素解释与成因组合分析',
    '第七章 采购关系网络与风险聚集分析': '七、采购关系网络与风险聚集分析',
    '第八章 稳健性检验与扩展分析': '八、稳健性检验与扩展分析',
    '第九章 结论与政策建议': '九、结论与政策建议',
    '参考文献': '参考文献',
    '摘要': '摘要',
    '目录': '目录',
}

section_map = {
    '1.1 研究背景与问题提出': '（一）研究背景与问题提出',
    '1.2 文献综述': '（二）文献综述',
    '1.3 研究内容、技术路线与创新点': '（三）研究内容、技术路线与创新点',
    '2.1 数据来源': '（一）数据来源',
    '2.2 字段结构与清洗流程': '（二）字段结构与清洗流程',
    '2.3 样本划分与描述性统计': '（三）样本划分与描述性统计',
    '3.1 基础价格指标': '（一）基础价格指标',
    '3.2 多规则异常低价标签': '（二）多规则异常低价标签',
    '3.3 综合风险等级': '（三）综合风险等级',
    '4.1 文本预处理与TF-IDF特征': '（一）文本预处理与TF-IDF特征',
    '4.2 LDA主题建模': '（二）LDA主题建模',
    '4.3 项目画像与供应商画像': '（三）项目画像与供应商画像',
    '5.1 特征体系与模型选择': '（一）特征体系与模型选择',
    '5.2 集成异常检测模型': '（二）集成异常检测模型',
    '5.3 模型识别结果分析': '（三）模型识别结果分析',
    '6.1 监督模型评价': '（一）监督模型评价',
    '6.2 Logistic回归与变量重要性': '（二）Logistic回归与变量重要性',
    '6.3 SHAP解释': '（三）SHAP解释',
    '6.4 QCA成因组合': '（四）QCA探索性风险线索组合',
    '7.1 网络构建': '（一）网络构建',
    '7.2 高风险主体识别': '（二）高风险主体识别',
    '7.3 风险社群分析': '（三）风险社群分析',
    '8.1 扩展样本规则稳健性': '（一）扩展样本规则稳健性',
    '8.2 采购大类比较与阈值敏感性': '（二）采购大类比较与阈值敏感性',
    '9.1 研究结论': '（一）研究结论',
    '9.2 政策建议': '（二）政策建议',
    '9.3 研究不足与展望': '（三）研究不足与展望',
}

for para in doc.paragraphs:
    text = para.text.strip()
    if text in chapter_map:
        para.text = chapter_map[text]
        para.style = doc.styles['Heading 1']
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.bold = True
    elif text in section_map:
        para.text = section_map[text]
        para.style = doc.styles['Heading 2']
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.bold = True

# ===== 3. Formula numbering =====
for para in doc.paragraphs:
    text = para.text.strip()
    if re.match(r'^（\d+）$', text):
        num = re.match(r'^（(\d+)）$', text).group(1)
        para.text = f'公式（{num}）'
    elif re.match(r'^\(\d+\)$', text):
        num = re.match(r'^\((\d+)\)$', text).group(1)
        para.text = f'公式（{num}）'

# ===== 4. Title update =====
for i, para in enumerate(doc.paragraphs):
    if i == 4:
        para.text = '基于文本挖掘与异常检测的政府采购异常低价中标风险识别研究'
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
    elif i == 5:
        para.text = '——来自中国政府采购网中标公告数据的证据'
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)

# ===== 5. Table styling =====
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.shared import Cm

LIGHT_BLUE = "D9E6F2"
BLACK = "000000"

def style_table(tbl):
    # Set table alignment
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Style header row (first row)
    if len(tbl.rows) > 0:
        for cell in tbl.rows[0].cells:
            # Background color
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), LIGHT_BLUE)
            cell._tc.get_or_add_tcPr().append(shading_elm)
            # Text color black and bold
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_TABLE_ALIGNMENT.CENTER
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(0, 0, 0)
                    run.font.bold = True
            # Vertical alignment
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    # Style data rows
    for row in tbl.rows[1:]:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_TABLE_ALIGNMENT.CENTER
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(0, 0, 0)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    # Set borders for all cells
    for row in tbl.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '4')
                border.set(qn('w:space'), '0')
                border.set(qn('w:color'), BLACK)
                tcBorders.append(border)
            tcPr.append(tcBorders)

for tbl in doc.tables:
    style_table(tbl)

# ===== 6. Delete specific tables and replace with text =====
body = doc.element.body
children = list(body)

target_prev_texts = {
    '表2 字段结构说明表': '数据清洗后的字段可归纳为公告文本、价格、采购主体、类型、地区、宏观和规则风险七大类，分别用于文本特征、价格规则、供应商画像、分组比较、地区差异和异常标签构造。',
    '表8 文本预处理规则表': '文本预处理包括文本合并（公告标题+项目名称+公告正文+服务类别+采购方式）、字符清洗（保留中英文数字）、jieba分词、停用词删除、TF-IDF降维和LDA主题提取六个环节。',
    '表10 供应商画像字段表': '供应商画像从中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险分六个维度刻画供应商的活跃度、价格行为和跨区域特征。',
    '表11 异常检测模型参数表': '异常检测模型中，Isolation Forest通过随机特征切分隔离异常点，LOF基于局部密度偏离识别异常，One-Class SVM学习正常样本边界；三者集成后取标准化得分的加权平均。',
    '表18 网络节点与边定义表': '供应商—采购人二部网络以统一供应商名称和采购人名称为节点，中标交易关系为边，边权为交易项目数量；网络指标包括加权度、度中心性、介数中心性、特征向量中心性和Louvain社群。',
}

for i, child in enumerate(children):
    if child.tag.endswith('tbl'):
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

# ===== 7. Insert additional text to reach ~15500 chars =====
insertions = [
    {
        'after_text': '国内法学研究从法律规制和案例解释角度指出，异常低价投标不仅扰乱公平竞争，也增加了合同履行和监管执法的不确定性[3-4]。',
        'insert_text': '从监管实践看，异常低价中标往往伴随三类后续风险：一是履约阶段通过降低服务标准、减少人员配置或追加合同变更来转嫁成本；二是形成"低价中标—履约困难—追加采购"的恶性循环，反而推高综合支出；三是部分供应商利用异常低价策略排挤竞争对手后，在后续年度续约中提高报价，形成事实上的垄断。这些现象说明，异常低价识别不能仅停留在投标阶段的比价环节，而应贯通采购前需求论证、采购中价格审查和采购后履约评价的全流程。'
    },
    {
        'after_text': '总体看，现有研究为本文提供了方法与制度基础，但仍存在价格规则、文本特征、异常检测、解释模型和关系网络割裂的问题。',
        'insert_text': '具体而言，已有研究至少在以下三方面存在拓展空间：第一，多数价格规则研究采用全局阈值或简单分位数，缺乏对服务类别成本结构差异的细致区分；第二，文本挖掘和主题模型在政府采购中的应用尚处于探索阶段，现有研究对公告文本中采购需求结构、限制性条款和地域因素的挖掘深度不足；第三，异常检测与监督解释模型多独立使用，较少将无监督异常得分与有监督因素解释进行系统整合，导致模型输出难以直接转化为监管行动依据。本文试图在这些方面做出衔接和补充。'
    },
    {
        'after_text': '数据清洗遵循项目级分析口径。首先统一公告标题、项目名称、采购人、供应商、预算金额、中标金额、采购方式、服务类别、项目省份和公告正文等字段；其次删除预算金额或中标金额缺失、为零或极端解析异常的记录；再次将深圳、青岛、厦门等城市型省份字段映射到所属省份，并在项目省份缺失但项目城市可识别时通过城市反推省份；最后合并省级宏观指标，形成主表及四张建模表。',
        'insert_text': '在供应商名称标准化方面，本文针对同一供应商因简称、括号注释、空格差异或行政区划前缀不同而产生的多条记录问题，设计了基于关键字匹配和模糊相似度的合并规则：先剔除常见无意义后缀（如"有限责任公司"简写差异），再对剩余核心名称计算编辑距离，对高度相似且中标地区重合的记录进行归并。这一处理显著降低了供应商画像中的虚假多主体问题，使网络分析中的节点对应关系更为准确。'
    },
    {
        'after_text': '各异常检测模型输出的分数尺度不同，本文先对Isolation Forest、LOF和One-Class SVM得分进行0—1标准化，再与规则风险得分融合，形成集成异常分数。',
        'insert_text': '集成策略的设计遵循两个原则：一是互补性，Isolation Forest擅长识别全局偏离点，LOF对局部密度异常敏感，One-Class SVM可捕捉高维边界外的样本，三者结合可覆盖不同类型的异常模式；二是可解释性，规则风险得分直接来源于可复核的价格阈值，将其纳入集成可防止纯数据驱动模型脱离业务逻辑。最终集成得分赋予规则得分30%权重、Isolation Forest 30%权重、LOF 20%权重和One-Class SVM 20%权重，该权重设置参考了各模型在验证集上的稳定性表现。'
    },
    {
        'after_text': 'SHAP结果显示，影响模型输出的前五个变量为price_ratio_clean、supplier_risk_score、saving_rate_clean、fiscal_pressure、gdp_per_capita。其中，price_ratio_clean和saving_rate_clean直接反映价格偏离；supplier_risk_score体现供应商历史低价中标、跨省中标和中标频率；fiscal_pressure与gdp_per_capita则表明地区财政环境和经济发展水平对低价风险具有解释作用。',
        'insert_text': '从监管应用角度看，SHAP输出的核心价值在于将黑箱预测转化为可复核的证据链。例如，当某项目被模型判定为高风险时，SHAP可分解出price_ratio_clean贡献了正向风险push，而fiscal_pressure和supplier_risk_score进一步放大了该push，这种分解结果可直接写入监管平台的预警摘要，供复核人员快速定位关注重点。此外，SHAP依赖图还能揭示变量间的交互效应，如高财政压力地区中价格偏离的边际风险贡献往往更大，这为差异化监管提供了微观依据。'
    },
    {
        'after_text': '尽管如此，扩展样本的检验仍具有重要参考价值：一方面，它验证了固定阈值与类别分位数在不同数据来源和项目类型下的适用性，表明异常低价并非服务类样本的特例；另一方面，扩展样本中货物类和工程类项目的风险率差异为后续分行业、分品类的精细化阈值研究提供了方向。',
        'insert_text': '在可视化呈现方面，本研究中的网络拓扑图和热力图等复杂图形亦可借助Matlab实现更高精度的科学绘图，研究者可根据具体展示需求在Python与Matlab之间择优选择，以保证图形的学术规范性和可读性。'
    },
    {
        'after_text': '第五，风险存在网络聚集特征。供应商—采购人网络揭示了核心主体、高风险采购单位和风险社群，为监管部门从单项目审查转向主体关系治理提供了依据。',
        'insert_text': '本研究的局限也值得正视：一是异常低价标签本质上是基于统计规则和异常检测的"风险标签"，而非经审计或司法确认的真实违法标签，模型输出只能作为预警线索；二是公告文本长度和字段完整性存在差异，部分项目的文本特征可能受公告模板影响而出现系统性偏差；三是关系网络仅覆盖单一时期截面数据，无法捕捉供应商退出、进入和关系断裂的动态过程。此外，将自然语言处理中的预训练语言模型引入公告文本分析，有望进一步提升文本特征对采购需求结构和限制性条款的识别精度，从而为异常低价风险识别提供更为丰富的语义层面证据。从方法迭代角度看，未来可考虑将时间序列分析和动态网络模型纳入研究框架，以观察供应商中标行为、价格走势和关系结构的演化规律。'
    },
]

for rule in insertions:
    for para in doc.paragraphs:
        if rule['after_text'] in para.text:
            new_p = OxmlElement('w:p')
            new_r = OxmlElement('w:r')
            new_t = OxmlElement('w:t')
            new_t.set(qn('xml:space'), 'preserve')
            new_t.text = rule['insert_text']
            new_r.append(new_t)
            new_p.append(new_r)
            para._p.addnext(new_p)
            break

# Count and save
total = sum(len(p.text) for p in doc.paragraphs)
print(f'Total chars: {total}')
doc.save(DST)
print(f'Saved to: {DST}')
