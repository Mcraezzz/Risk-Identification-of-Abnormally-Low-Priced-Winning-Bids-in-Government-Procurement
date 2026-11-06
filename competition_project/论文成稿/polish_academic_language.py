# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph


SCRIPT_DIR = Path(__file__).resolve().parent
DOCX_IN = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_格式规范修订版.docx")
FORMULA_SOURCE = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_最终版.docx")
DOCX_OUT = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_学术润色版.docx")
CODE_OUT = SCRIPT_DIR / DOCX_OUT.name
AUDIT_OUT = SCRIPT_DIR / "academic_polish_audit.json"

INK = RGBColor(0, 0, 0)
CAPTION_COLOR = RGBColor(23, 32, 51)
FORMULA_LABEL_RE = re.compile(r"公式\((\d+)\)")
FORMULA_TEXTS = {
    1: "R_i=M_i/B_i, G_i=1-R_i",
    2: "T_{g,α}=Q_α(R_i|c_i=g), α∈{0.05,0.10}",
    3: "T_{g,IQR}=Q_{1,g}-1.5(Q_{3,g}-Q_{1,g})",
    4: "Z_i=(R_i-Median_g)/(1.4826×MAD_g)",
    5: "A_i=I_{i,65}+I_{i,10%}+I_{i,5%}+I_{i,IQR}+I_{i,Z}",
    6: "E_i=0.30IF_i+0.25LOF_i+0.20OCSVM_i+0.25A_i",
}


REPLACEMENTS: dict[int, str] = {
    14: "异常低价中标是政府采购领域较为典型且长期存在的监管难题。其表层特征表现为成交价格明显低于预算或同类项目常规水平，深层机理则可能关联履约质量下降、供应商策略性报价、采购方式约束、地区财政压力以及交易关系固化等多重因素。随着政府采购公告、合同与信用信息持续在线化，单纯依赖人工经验和统一价格阈值的审查方式，已难以满足多类别、多主体、多地区风险识别的治理需求。",
    15: "本文以中国政府采购网公告数据、2025年第一季度合同扩展样本和2024年省级宏观指标为基础，经过清洗、标准化和跨源融合，形成7,885条项目级样本，其中价格有效样本7,720条、服务类主样本5,588条、2025Q1扩展样本4,500条。在指标构造方面，研究从政策参考阈值、类别内分位数、箱线图IQR和稳健Z分数四个维度生成异常低价初始标签。",
    16: "在此基础上，本文进一步采用Isolation Forest、LOF和One-Class SVM构建集成异常检测模型，并将规则风险得分纳入综合风险分数。模型在服务类主样本中识别出高风险项目559个，占比10.00%。随后，研究利用Logistic回归、Random Forest、XGBoost和SHAP开展风险因素解释。结果表明，XGBoost能够较好复现风险标签在特征空间中的分布结构，价格比例、节约率、供应商风险画像、财政压力和人均GDP等变量对模型输出具有较强解释力。进一步的QCA和关系网络分析显示，异常低价风险具有多条件并发和主体关系嵌入特征。",
    17: "研究表明，异常低价风险并非单一价格偏离问题，而是采购类别、供应商行为、地区环境和交易网络共同作用的结果。基于实证发现，本文建议建立自动预警、类别阈值、供应商画像、重点地区与采购方式监管以及履约跟踪相衔接的闭环治理机制。",
    18: "关键词：政府采购；异常低价中标；风险识别；异常检测；监管治理",
    26: "六、风险因素解释与风险线索组合分析",
    34: "政府采购是财政资金配置、公共服务供给和国家治理能力现代化的重要制度安排。伴随采购规模扩大和电子化平台建设推进，公告文本、合同信息、供应商资料、价格数据与履约线索不断沉淀为可计算、可追溯的数据资源。与此同时，异常低价中标现象在实践中仍较为突出：部分项目以显著低于预算或同类项目市场水平的价格成交，后续可能通过降低服务质量、追加变更、压缩人员配置或履约替代等方式转移成本。与一般意义上的节约财政资金不同，异常低价更强调价格偏离与履约风险之间的联动关系，因而具有更强的治理复杂性。",
    35: "从监管实践观察，异常低价中标通常伴随三类后续风险：其一，履约阶段通过降低服务标准、减少资源投入或申请合同变更弥补报价缺口；其二，形成“低价中标—履约困难—追加采购”的循环，导致财政资金综合支出上升；其三，个别供应商利用低价策略排挤竞争者，并在后续续约或关联采购中提高报价，削弱市场竞争。由此可见，异常低价识别不能停留于投标价格本身，还应关注其背后的履约能力、竞争结构和监管可验证性。",
    36: "传统监管主要依赖固定阈值、专家经验和人工复核。这一方式在小规模、低频次采购场景中具有一定可行性，但面对跨地区、多类别、高频次的政府采购数据时，容易暴露三方面不足：第一，统一阈值难以反映不同服务类别的成本结构差异，可能混淆合理让利与异常低价；第二，公告文本和供应商交易行为未被充分利用，难以解释风险形成机制；第三，监管对象多聚焦单个项目，较少识别供应商—采购人关系网络中的重复交易和风险聚集。",
    37: "基于上述问题，本文将异常低价识别界定为多源数据支撑下的风险治理问题，而非单纯的价格审查问题。研究以政府采购项目级数据为对象，旨在构建可解释、可复核并可服务监管决策的异常低价风险识别框架。需要强调的是，模型输出并不等同于违法认定，而是用于形成监管预警线索，为后续人工复核、履约跟踪和分类处置提供依据。该定位有助于在提高识别效率的同时，保持行政监管必要的审慎性和程序正当性。",
    39: "国外关于异常低价识别的研究大体形成三类路径。第一类聚焦价格统计检验和计量识别。Jeong、Lee和Kim通过判别分析识别采购市场中的异常低价投标[8]；Conti、De Giovanni和Naldi提出rank-and-compare算法检测采购拍卖中的异常低价报价[9]；Hinojosa、Muñoz和Oviedo则围绕PPP项目提出统计检验方案[10]。相关研究共同表明，异常低价识别需要兼顾检测概率、误报风险和报价离散程度。",
    40: "第二类关注公共采购腐败风险和红旗指标。Fazekas、Tóth和King基于公共采购大数据构建客观腐败风险指数，强调限制竞争、重复中标和程序异常等红旗变量[13]；Decarolis和Giorgiantonio进一步利用意大利招标公告构造腐败红旗指标[14]。此类研究提示，价格异常往往需要与程序、主体和文本线索结合解释，才能形成更具监管意义的风险判断。",
    41: "第三类强调机器学习、文本挖掘和网络分析方法。Rabuzin和Modrušan使用机器学习与文本挖掘预测公共采购腐败指数[11]；Lima等构建多面向采购文本学习数据集，为公共采购文本建模提供数据基础[12]；Lyra、Pinheiro和Bação综述网络分析在公共采购欺诈检测中的应用，指出主体连接结构能够揭示重复交易、中心节点和潜在合谋关系[16]。这些成果表明，异常低价风险具有多维数据特征，单一价格变量难以完整刻画其生成机制。",
    42: "国内研究更多围绕政府采购文本挖掘、异常低价法律规制和招投标数据治理展开。王宏等将K近邻算法用于政府采购数据挖掘[1]，韩利利研究中标公告文本挖掘在政府采购中的应用[2]；苏莹莹和张怀营分别从法律规制与指导性案例角度讨论异常低价投标行为[3-4]；魏俊奎等以电力供应商投标评估为例说明大数据分析在供应商预测评价中的应用[5]。总体而言，国内研究已认识到异常低价问题的复杂性，但在跨源数据融合、模型解释和监管应用转化方面仍有进一步拓展空间。",
    43: "具体来看，既有研究仍存在三方面不足：第一，部分价格规则采用全局阈值或简单分位数，未充分区分不同服务类别的成本差异；第二，文本挖掘和主题模型在政府采购场景中的应用仍处于拓展阶段，对采购需求结构、限制性条款和地区因素的挖掘不够深入；第三，异常检测、监督解释和关系网络分析多被分散使用，较少形成从识别、解释到监管行动的完整闭环。对于监管部门而言，真正有价值的模型不仅应给出风险排序，还应说明风险来自何种价格偏离、主体行为和制度环境，并能够转化为可执行的复核清单。",
    45: "本文构建“数据治理—风险标签—异常检测—风险解释—监管决策”的五阶段研究框架。第一阶段对原始公告和合同数据进行清洗、字段统一、服务类型映射、供应商名称标准化以及省级宏观指标融合；第二阶段从固定阈值、类别分位数、IQR和稳健Z分数构造异常低价规则标签；第三阶段采用Isolation Forest、LOF和One-Class SVM识别多维异常项目；第四阶段借助XGBoost、SHAP和QCA解释风险因素及其组合路径；第五阶段结合关系网络和稳健性检验提出可操作的监管建议。该框架兼顾统计识别、业务解释和监管落地，力求避免模型结果停留在技术层面。",
    46: "本文的可能创新主要体现在三个方面：一是将异常低价识别由单一固定阈值扩展为类别内相对价格偏离和多规则投票，提高规则标签的稳健性；二是将公告文本主题、供应商画像和地区宏观变量纳入模型特征，避免仅以价格判断风险；三是将模型结果嵌入主体关系网络和监管建议，形成从风险识别到证据解释、再到分类监管的分析链条。",
    51: "本文使用两类政府采购项目数据：一类来源于中国政府采购网公告与中标信息，另一类为2025年第一季度合同扩展样本。宏观控制变量来自2024年省级GDP、人口、人均GDP、财政收入、财政支出、财政压力、平均工资、第三产业占比和城镇化率等指标。2025年部分省级指标主要用于补充描述，正式建模中的地区控制变量以2024年完整省级数据为准。",
    56: "数据清洗遵循项目级分析口径。首先统一公告标题、项目名称、采购人、供应商、预算金额、中标金额、采购方式、服务类别、项目省份和公告正文等字段；其次剔除预算金额或中标金额缺失、为零以及解析明显异常的记录；再次将深圳、青岛、厦门等城市型字段映射至所属省份，并在项目省份缺失但城市可识别时反推省份；最后合并省级宏观指标，形成可用于建模的项目层数据集。",
    57: "在供应商名称标准化方面，本文针对同一供应商因简称、括号注释、空格差异或行政区划前缀不同而形成的多条记录，设计了基于关键词规则和模糊相似度的归并流程：先剔除常见无实质含义后缀，再对剩余核心名称计算编辑距离，对名称高度相似且中标地区重合的记录进行合并。该处理有助于减少供应商画像中的虚假多主体问题。",
    58: "清洗后的字段可概括为公告文本、价格、采购主体、类型、地区、宏观环境和规则风险七类，分别服务于文本特征提取、价格规则构造、供应商画像、分组比较、地区差异分析和异常标签生成。",
    62: "清洗后主表共包含7,885条记录。为匹配论文分析逻辑，本文从主表派生四个正式分析版本：全样本表用于描述性统计，价格有效样本表用于异常低价规则构造，服务类主样本表用于主模型、解释分析和关系网络，2025Q1扩展样本表用于稳健性检验。",
    67: "从采购大类看，服务类样本占比最高，因而构成本文主模型分析重点；货物类、工程类和其他项目主要用于全样本描述和扩展样本稳健性比较。服务类别方面，物业管理、办公设备与耗材、信息化服务、运维维护、保洁服务和安保服务构成主要类别，反映样本同时覆盖后勤服务、信息技术服务和通用货物采购等典型场景。",
    76: "异常低价首先体现为成交价格相对预算或同类项目价格的显著偏离。本文以预算金额和中标金额为基础，构造中标/预算比例、节约率、对数预算金额和对数中标金额。为降低金额解析异常对规则识别的干扰，仅将预算金额大于100元、中标金额大于100元且0<中标/预算比例≤1的记录纳入价格有效样本。其中，M_i表示第i个项目的中标金额，B_i表示预算金额，R_i表示中标/预算比例，G_i表示节约率。",
    77: "清洗结果显示，价格有效样本为7,720条。主表中仍保留异常价格标记，以便开展数据说明和稳健性讨论。其中，中标/预算比例小于0.01的记录60条，比例等于0的记录17条，比例大于1的记录93条，中标金额不超过100元的记录74条，预算金额不超过100元的记录48条。",
    83: "单一价格阈值容易忽略采购类别差异。借鉴异常低价统计检验和红旗指标研究[8-14]，本文从固定阈值、类别分位数、箱线图异常值和稳健Z分数四个角度构造规则标签。固定阈值用于捕捉明显低于预算的项目，类别分位数用于识别同类项目中的相对低价，IQR适合检测箱线图下界外的离群值，稳健Z分数则通过中位数和MAD降低极端观测值影响。",
    84: "具体规则如下。其中，c_i表示第i个项目所属的统一服务类别，g表示某一服务类别，α取0.05或0.10，T表示相应规则阈值；当R_i低于阈值或Z_i小于设定界限时，项目触发对应异常规则：",
    92: "本文将五项规则触发结果相加，形成可复核的规则风险得分。式中，I表示第i个项目是否触发相应规则的0/1指示变量，A_i表示综合规则风险得分：",
    93: "当规则得分为0时定义为正常，得分为1时定义为低风险，得分为2时定义为中风险，得分大于等于3时定义为高风险。该规则兼顾审慎性与可解释性：只有多个规则共同指向价格显著偏低时，项目才被划入高风险类别。价格有效样本中高风险项目649个，占比8.41%；服务类主样本中高风险项目525个，占比9.40%。",
    102: "政府采购公告文本包含项目需求、资格条件、服务范围、履约期限和供应商信息，是识别异常低价风险的重要补充。国内研究已证明政府采购公告文本可用于采购领域分类和供应商行为分析[1-2]，国际研究也表明文本挖掘能够揭示竞争限制和腐败风险线索[11-12,15]。本文将公告标题、项目名称、公告正文、统一服务类别和采购方式合并为文本语料，用于构造TF-IDF和主题特征。",
    103: "文本预处理包括文本合并、字符清洗、jieba分词、停用词删除、TF-IDF降维和LDA主题提取六个环节。其中，文本合并覆盖公告标题、项目名称、公告正文、服务类别和采购方式，字符清洗保留中英文与数字信息。",
    105: "TF-IDF方法通过词频与逆文档频率的乘积衡量词项区分度[17]，适合从公告文本中抽取服务类别、技术需求和采购对象特征。本文选取高频且具有区分度的关键词，并通过截断奇异值分解获得文本主成分，用于后续异常检测和监督模型。",
    111: "为进一步刻画项目需求结构，本文采用LDA主题模型识别公告文本中的潜在主题。LDA将文档视为主题混合、主题视为词项分布[18]，能够将长文本压缩为具有解释意义的主题概率变量。本文设置6个主题，并依据各主题Top关键词进行解释。为提升主题可解释性，研究在原有停用词基础上，进一步剔除城市名、日期词、联系电话和公告模板词等低信息量词项。",
    119: "项目画像包括价格画像、文本画像、采购画像、地区画像和风险画像。供应商画像重点刻画中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险画像分。供应商维度能够反映重复中标、跨区域经营和低价策略倾向，为后续网络分析提供节点属性。",
    120: "供应商画像从中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险分六个维度刻画其市场活跃度、价格行为和跨区域经营特征。",
    126: "异常低价风险属于小比例、弱标签和多维异常识别问题。本文以服务类主样本作为主模型样本，输入特征包括价格特征、采购特征、文本主题特征、供应商画像特征和地区宏观特征。考虑到规则标签具有不完全性，本文采用无监督/半监督异常检测模型识别潜在异常项目。Isolation Forest通过随机切分特征空间隔离异常点[19]，LOF基于局部密度偏离识别异常[20]，One-Class SVM则学习正常样本边界[21]。在监管情境中，多模型集成有助于降低单一算法对分布假设和参数设定的依赖。",
    127: "在异常检测模型中，Isolation Forest侧重全局异常隔离，LOF强调局部密度偏离，One-Class SVM用于刻画正常样本边界；三者集成后取标准化得分的加权平均。",
    132: "由于各异常检测模型输出分数的尺度并不一致，本文先对Isolation Forest、LOF和One-Class SVM得分进行0—1标准化，再与规则风险得分融合，形成集成异常分数。式中，E_i表示第i个项目的集成异常分数，A_i表示标准化后的规则风险得分：",
    133: "集成策略遵循两个原则：一是互补性，Isolation Forest擅长识别全局偏离点，LOF对局部密度异常更为敏感，One-Class SVM能够捕捉高维边界外样本，三者结合可覆盖不同异常模式；二是可解释性，规则风险得分直接来源于可复核的价格阈值，将其纳入集成有助于防止纯数据驱动模型脱离业务逻辑。最终集成得分赋予规则风险得分30%权重、Isolation Forest 30%权重、LOF 20%权重和One-Class SVM 20%权重。",
    134: "本文将集成异常分数位于前10%的服务类项目定义为模型高风险项目。该设定既保留异常检测模型对多维特征的敏感性，也避免完全脱离可解释的价格规则。",
    142: "集成异常检测模型在服务类主样本中识别高风险项目559个，占比10.00%。与规则标签相比，集成模型不仅关注价格显著偏低的项目，也会识别文本需求、供应商画像和地区环境共同呈现异常的项目。从服务类别看，高风险项目集中于后勤服务、运维维护和信息化服务；从地区看，高风险项目更易在样本量较高或财政压力较大的地区聚集。总体上，模型结果为后续解释分析和监管排序提供了基础。由于高风险项目只是监管线索而非最终结论，后续仍需结合合同文本、履约记录和投诉质疑信息进行综合判断。",
    151: "六、风险因素解释与风险线索组合分析",
    153: "异常检测模型给出风险识别结果后，仍需回答“为什么这些项目被识别为高风险”。因此，本文以final_high_risk为目标变量，构建Logistic回归、Random Forest和XGBoost监督模型。Logistic回归用于观察变量方向和统计解释，Random Forest用于非线性变量重要性对照[22]，XGBoost用于刻画复杂非线性关系[23]。通过多模型比较，可以检验风险标签在特征空间中的可解释程度。",
    158: "结果显示，XGBoost模型AUC达到0.991、F1值为0.874。需要说明的是，该AUC处于较高水平，主要因为目标变量来源于规则风险与异常检测标签，而非经执法或审计确认的真实违法标签；模型学习的实质是风险标签在特征空间中的分布结构。因此，较高AUC说明模型能够较好复现并排序风险标签，但不能直接等同于识别真实违法行为。后续监管应用中，应将模型评价结果理解为预警排序能力，而非行政认定准确率。",
    167: "为解释XGBoost模型中单个变量的边际贡献，本文引入SHAP方法。SHAP基于Shapley值思想，将模型输出分解为各特征的贡献份额，能够同时提供全局重要性和局部解释[24]。在政府采购监管场景下，SHAP的价值在于将黑箱模型输出转化为可供人工复核的风险证据链。",
    174: "SHAP结果显示，影响模型输出的前五个变量为price_ratio_clean、supplier_risk_score、saving_rate_clean、fiscal_pressure和gdp_per_capita。其中，price_ratio_clean和saving_rate_clean直接反映价格偏离程度；supplier_risk_score体现供应商历史低价行为和风险积累；fiscal_pressure和gdp_per_capita则揭示地区财政约束与经济发展水平可能对采购价格形成的影响。该结果表明，异常低价风险既受项目价格因素驱动，也受供应商行为和地区环境共同影响。",
    175: "从监管应用角度看，SHAP输出的核心价值在于把黑箱预测转化为可复核证据。例如，当某项目被模型判定为高风险时，SHAP可分解出price_ratio_clean对风险得分的正向贡献，同时显示fiscal_pressure和supplier_risk_score是否进一步放大风险。这种分解结果可写入监管平台预警摘要，帮助监管人员快速定位复核重点。",
    176: "（四）QCA探索性风险线索组合",
    177: "异常低价风险往往不是单一变量造成，而是多条件并发的结果。本文借鉴fsQCA方法[25]，将高节约率、低价格比例、高频供应商、跨省中标、高财政压力、公开招标、供应商信息缺失和高风险服务类别等变量转化为集合条件，分析其与高风险结果之间的组合关系。",
    182: "QCA结果显示，异常低价风险呈现多条探索性线索：路径1的一致性相对较高，可视为较稳健的风险组合；路径2—路径4的一致性偏低，更适合作为引导后续复核的探索性线索，不宜直接解释为严格因果结论。总体看，价格偏离是出现频率最高的核心线索，高频供应商、高财政压力、跨省中标、特定采购方式和高风险服务类别等条件的组合，能够进一步提高风险识别的针对性。",
    185: "公共采购风险具有明显的关系嵌入性。供应商与采购人之间的重复交易、核心主体位置和社群结构，可能反映市场进入壁垒、信息不对称或监管盲区。网络分析文献指出，公共采购欺诈和腐败风险可以通过主体连接结构、中心性和社群发现获得线索[16]。本文构建供应商—采购人二部关系网络，节点包括供应商和采购人，边表示中标交易关系，边权为交易项目数量。",
    186: "供应商—采购人二部网络以统一供应商名称和采购人名称为节点，以中标交易关系为边，边权为交易项目数量；网络指标包括加权度、度中心性、介数中心性、特征向量中心性和Louvain社群。",
    191: "本文计算加权度、度中心性、介数中心性和特征向量中心性，并结合关联高风险项目数量和高风险比例识别监管重点。供应商中心性排名反映其在交易网络中的活跃度和核心位置，采购人风险排名则反映其关联项目中高风险项目占比。",
    203: "核心主体名单较长，正文仅呈现社群规模、交易项目数和高风险比例等结构特征；具体供应商和采购人可结合表14、表15的中心性排名追踪。对于项目数较少但风险比例为100%的主体，需要特别注意：小样本下100%高风险并不意味着主体必然存在问题，可能源于偶然中标或规则阈值恰好触发。此类主体更适合作为重点复核线索，应通过增加样本观察、核验履约资料和比对历史交易进一步判断。",
    206: "社群分析表明，高风险项目并非完全随机分散，而是在若干供应商—采购人交易群体中呈现聚集。对于监管部门而言，社群结果可用于形成“项目—主体—类别—地区”的联动审查清单：当某一社群同时具有高交易密度、高风险比例和核心供应商重复出现等特征时，应优先开展合同履约、报价合理性和供应商资质复核。网络证据的价值不在于单独证明违规，而在于帮助监管部门识别需要连续观察的主体组合。",
    209: "为检验规则与模型结论是否具有样本外稳定性，本文使用2025Q1扩展样本进行稳健性检验。扩展样本来自合同公告，项目类型覆盖服务、货物、工程和其他类别，能够与服务类主样本形成互补。异常低价研究文献强调，不同制度环境和项目类型下的低价判断应进行样本外验证[9-10]。",
    215: "扩展样本中规则高风险比例为6.47%，低于服务类主样本，但主要风险方向仍与价格偏离、服务类别差异和供应商行为有关。采购大类比较显示，服务、货物和工程项目的风险率存在差异，说明异常低价审查阈值不宜完全统一。需要说明的是，扩展样本来自合同公告，缺少部分供应商画像字段和代理机构信息，因此不完全等同于主样本建模场景，其结果主要用于检验规则方向和结论稳健性。该结果也提示，跨数据源应用模型时应关注字段口径、公告类型和样本结构差异。",
    226: "阈值敏感性结果表明，当固定阈值由0.60放宽至0.70时，识别数量明显增加；类别分位数由5%提高到15%时，预警范围同样扩大。这说明规则阈值本质上是监管资源配置参数：阈值越宽松，覆盖面越大但复核成本越高；阈值越严格，误报较少但可能遗漏边界风险。本文建议在正式监管中采用“基础阈值+类别阈值+模型排序”的组合方式，而非依赖单一固定阈值。",
    229: "本文基于政府采购公告、合同扩展样本和省级宏观指标，构建异常低价风险识别与监管决策模型，并从价格规则、机器学习解释和关系网络三个层面开展验证，得到以下主要结论和监管治理启示，可归纳如下：",
    230: "第一，异常低价风险具有显著类别差异。服务类项目是主样本主体，不同统一服务类别的中标/预算比例分布和高风险比例存在差异，说明统一阈值难以覆盖不同服务的成本结构。",
    231: "第二，价格偏离、节约率和供应商风险画像是异常低价识别的核心因素。SHAP结果显示，price_ratio_clean、saving_rate_clean和supplier_risk_score对模型输出影响最大，验证了价格规则与供应商历史行为结合的必要性。",
    232: "第三，地区宏观环境具有解释作用。财政压力和人均GDP进入SHAP前列，表明地方财政约束和经济发展水平可能影响采购预算约束、供应商竞争格局和低价中标策略。",
    233: "第四，异常低价风险具有组态成因。QCA结果显示，高节约率、低价格比例、高频供应商、跨省中标、高财政压力和高风险服务类别之间存在多种组合路径，单因素解释并不充分。",
    234: "第五，风险存在网络聚集特征。供应商—采购人网络揭示了核心主体、高风险采购单位和风险社群，为监管部门由单项目审查转向主体关系治理提供了依据。",
    235: "本研究的局限也需要正视：一是异常低价标签本质上是基于统计规则和异常检测的风险标签，而非经审计或司法确认的真实违法标签，模型输出只能作为预警线索；二是公告文本长度和字段完整性存在差异，部分项目的文本特征可能受公告模板影响而出现系统性偏差；三是关系网络仅覆盖单一时期截面数据，无法捕捉供应商进入、退出和关系断裂的动态过程；四是扩展样本字段与主样本并不完全一致，稳健性检验仍受到数据可得性限制。因此，本文结论更适合解释异常低价风险的结构性特征和监管优先级，而不宜被理解为对具体主体的直接责任认定。",
    239: "第一，建立异常低价自动预警机制。监管平台可实时计算中标/预算比例、节约率、类别偏离度和规则风险得分，并结合异常检测模型输出形成项目风险排序。对于多规则触发或模型得分位于高分位的项目，应纳入人工复核清单。预警结果应同时展示触发规则、关键变量贡献和历史同类项目价格区间，以便提高复核效率和解释透明度。",
    240: "第二，按采购类别设置差异化审查阈值。物业管理、绿化养护、信息化、运维维护、咨询评估检测等服务类型的成本结构差异较大，应建立类别内分位数阈值和历史价格参照库，避免用同一固定阈值判断所有项目。",
    241: "第三，建立供应商低价中标画像机制。对供应商中标次数、低价中标次数、平均节约率、跨省中标比例和服务类别广度进行持续更新，形成供应商风险画像。对高频低价中标且网络中心性较高的供应商，应强化履约质量和报价合理性复核。",
    242: "第四，加强高风险采购方式和高风险地区监管。对于风险率较高的采购方式以及财政压力较高地区，应适当提高抽查比例，重点关注低价中标后的合同变更、追加采购和履约评价。",
    243: "第五，建立中标后履约跟踪机制。异常低价项目的风险不止发生在中标阶段，还可能在履约阶段表现为服务质量下降、人员配置不足或后续变更增加。因此，应将模型预警结果与履约验收、投诉质疑和信用评价衔接，形成全过程监管闭环。对于连续低价中标且履约反馈较差的供应商，可适当提高后续项目的资格核验和履约抽查强度。",
    247: "本文仍存在若干不足。第一，部分项目省份和城市字段由文本或城市映射推断，仍可能存在识别误差；第二，异常低价标签是风险标签而非执法认定，尚缺少履约质量、投诉处理和审计处罚等外部结果变量；第三，文本主题模型主要使用公告正文，尚未纳入招标文件全文和合同履约细节；第四，关系网络以供应商—采购人为主，未来可进一步扩展到代理机构、评审专家和投诉处理等主体。后续研究可在更长时间序列和更完整履约数据基础上，对异常低价风险的动态演化、履约后果和治理效果开展评估，并进一步检验不同地区、不同采购类别下模型阈值的适用性。",
}


def clear_paragraph(paragraph: Paragraph) -> None:
    p_pr = paragraph._p.pPr
    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)


def set_run_font(run, east_asia: str, size_pt: float, bold: bool = False, color: RGBColor = INK) -> None:
    run.font.name = "Times New Roman"
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = color


def set_table_border_invisible(table: Table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "0")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "FFFFFF")


def set_cell_border_invisible(cell) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "0")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "FFFFFF")


def set_cell_width(cell, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_width_dxa(table: Table, width_dxa: int) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(width_dxa))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")


def set_table_grid(table: Table, widths_dxa: list[int]) -> None:
    tbl_grid = table._tbl.tblGrid
    if tbl_grid is None:
        tbl_grid = OxmlElement("w:tblGrid")
        table._tbl.insert(1, tbl_grid)
    for child in list(tbl_grid):
        tbl_grid.remove(child)
    for width in widths_dxa:
        grid_col = OxmlElement("w:gridCol")
        grid_col.set(qn("w:w"), str(width))
        tbl_grid.append(grid_col)


def set_exact_line(paragraph: Paragraph, size_pt: float = 24) -> None:
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    paragraph.paragraph_format.line_spacing = Pt(size_pt)


def replace_text(paragraph: Paragraph, text: str) -> None:
    clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    paragraph.paragraph_format.first_line_indent = None
    return run


def clear_cell(cell) -> None:
    for paragraph in cell.paragraphs:
        clear_paragraph(paragraph)


def is_level1(text: str) -> bool:
    return bool(re.match(r"^[一二三四五六七八九十]+、", text))


def is_level2(text: str) -> bool:
    return bool(re.match(r"^（[一二三四五六七八九十]+）", text))


def is_level3(text: str) -> bool:
    return bool(re.match(r"^\d+(\.\d+)+\s*", text))


def apply_page_setup(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)


def get_formula_nodes() -> dict[int, list]:
    source = Document(str(FORMULA_SOURCE))
    formulas: dict[int, list] = {}
    for paragraph in source.paragraphs:
        match = re.search(r"公式[（(](\d+)[）)]", paragraph.text)
        nodes = paragraph._p.xpath(".//m:oMath")
        if match and nodes:
            formulas[int(match.group(1))] = [deepcopy(node) for node in nodes]
    return formulas


def table_text_for_formula_detection(table: Table) -> str:
    parts: list[str] = []
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                text = paragraph.text.strip()
                if text:
                    parts.append(text)
    return "".join(parts)


def replace_formula_tables_with_word_math(doc: Document) -> int:
    formula_nodes = get_formula_nodes()
    formula_tables = [
        table for table in doc.tables if FORMULA_LABEL_RE.search(table_text_for_formula_detection(table))
    ]
    converted = 0
    for formula_no, table in zip(sorted(formula_nodes), formula_tables):
        if len(table.rows[0].cells) < 2:
            continue
        left_width = 6612
        right_width = 1700
        table.autofit = False
        set_table_width_dxa(table, left_width + right_width)
        set_table_grid(table, [left_width, right_width])
        set_table_border_invisible(table)

        left = table.cell(0, 0)
        right = table.cell(0, 1)
        left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_width(left, left_width)
        set_cell_width(right, right_width)
        set_cell_border_invisible(left)
        set_cell_border_invisible(right)
        clear_cell(left)
        clear_cell(right)

        lp = left.paragraphs[0]
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.paragraph_format.space_before = Pt(2)
        lp.paragraph_format.space_after = Pt(2)
        for node in formula_nodes[formula_no]:
            lp._p.append(deepcopy(node))

        rp = right.paragraphs[0]
        rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rp.paragraph_format.space_before = Pt(2)
        rp.paragraph_format.space_after = Pt(2)
        label_run = rp.add_run(f"公式({formula_no})")
        set_run_font(label_run, "宋体", 12)
        converted += 1
    return converted


def style_paragraph(paragraph: Paragraph) -> None:
    text = paragraph.text.strip()
    if not text:
        return
    if paragraph._p.xpath(".//w:drawing") or paragraph._p.xpath(".//m:oMath|.//m:oMathPara"):
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return
    if re.match(r"^(图|表)\d+", text):
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(4)
        paragraph.paragraph_format.space_after = Pt(6)
        for run in paragraph.runs:
            set_run_font(run, "宋体", 12, bold=True, color=CAPTION_COLOR)
        return
    if text in {"摘要", "目录", "参考文献"}:
        for run in paragraph.runs:
            set_run_font(run, "黑体", 14)
        set_exact_line(paragraph)
    elif is_level1(text):
        for run in paragraph.runs:
            set_run_font(run, "黑体", 15)
        set_exact_line(paragraph)
    elif is_level2(text):
        for run in paragraph.runs:
            set_run_font(run, "楷体", 14)
        set_exact_line(paragraph)
    elif is_level3(text):
        for run in paragraph.runs:
            set_run_font(run, "宋体", 12, bold=True)
        set_exact_line(paragraph)
    else:
        for run in paragraph.runs:
            set_run_font(run, "宋体", 12)
        set_exact_line(paragraph)


def iter_body_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield "p", Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "tbl", Table(child, doc)


def block_text(block) -> str:
    if isinstance(block, Paragraph):
        return block.text.replace("\t", " ").strip()
    parts: list[str] = []
    for row in block.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                text = paragraph.text.replace("\t", " ").strip()
                if text:
                    parts.append(text)
    joined = "".join(parts)
    match = FORMULA_LABEL_RE.search(joined)
    if match:
        formula_no = int(match.group(1))
        return FORMULA_TEXTS.get(formula_no, "") + f"公式({formula_no})"
    return joined


def body_char_count(doc: Document) -> int:
    blocks = list(iter_body_blocks(doc))
    start = None
    end = None
    for i, (kind, block) in enumerate(blocks):
        text = block_text(block)
        if start is None and text == "一、引言" and i > 30:
            start = i
        elif start is not None and text == "参考文献":
            end = i
            break
    if start is None or end is None:
        raise RuntimeError("未能定位正文起止位置")
    return len("".join(block_text(block) for _, block in blocks[start:end]))


def main() -> None:
    doc = Document(str(DOCX_IN))
    apply_page_setup(doc)
    before_count = body_char_count(doc)

    for idx, text in REPLACEMENTS.items():
        run = replace_text(doc.paragraphs[idx], text)
        style_paragraph(doc.paragraphs[idx])

    for paragraph in doc.paragraphs:
        style_paragraph(paragraph)

    converted_formula_count = replace_formula_tables_with_word_math(doc)
    after_count = body_char_count(doc)
    if not (15500 <= after_count <= 16000):
        raise RuntimeError(f"正文字符数不在15500到16000之间：{after_count}")

    doc.save(str(DOCX_OUT))
    shutil.copy2(DOCX_OUT, CODE_OUT)
    audit = {
        "input": str(DOCX_IN),
        "output": str(DOCX_OUT),
        "code_copy": str(CODE_OUT),
        "body_char_count_before": before_count,
        "body_char_count_after": after_count,
        "keyword_count": 5,
        "keyword_line": REPLACEMENTS[18],
        "changed_paragraphs": len(REPLACEMENTS),
        "word_math_formula_count": converted_formula_count,
    }
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(DOCX_OUT)
    print(CODE_OUT)
    print(AUDIT_OUT)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
