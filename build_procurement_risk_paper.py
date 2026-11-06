from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(r"C:\Users\22672\Desktop\统计建模代码")
OUT_DIR = ROOT / "论文成稿"
TABLE_DIR = ROOT / "输出结果" / "tables"
FIG_DIR = ROOT / "输出结果" / "figures"
DATA_DIR = ROOT / "输出结果" / "data"
DOCX_PATH = OUT_DIR / "政府采购异常低价风险识别与监管研究.docx"


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / name, encoding="utf-8-sig")


def fmt(value, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    try:
        value = float(value)
    except Exception:
        return str(value)
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if 0 <= value <= 1:
        return f"{value:.{digits}f}"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def pct(value, digits: int = 2) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except Exception:
        return str(value)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 10, align=WD_ALIGN_PARAGRAPH.CENTER) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(14)
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def set_run_font(run, font: str = "宋体", size: int = 12, bold: bool | None = None) -> None:
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def add_page_number(section) -> None:
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("第 ")
    set_run_font(run, size=10)
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    run2 = p.add_run(" 页")
    set_run_font(run2, size=10)


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)
    # Page numbers are intentionally left for Word to manage if needed; the
    # artifact renderer does not refresh PAGE fields reliably.

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.paragraph_format.first_line_indent = Cm(0.74)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    normal.paragraph_format.line_spacing = Pt(24)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)

    for name, font, size, bold in [
        ("Heading 1", "黑体", 15, False),
        ("Heading 2", "楷体", 14, False),
        ("Heading 3", "宋体", 12, True),
    ]:
        style = styles[name]
        style.font.name = font
        style._element.rPr.rFonts.set(qn("w:eastAsia"), font)
        style.font.size = Pt(size)
        style.font.bold = bold
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        style.paragraph_format.line_spacing = Pt(24)
        style.paragraph_format.space_before = Pt(6)
        style.paragraph_format.space_after = Pt(6)


def add_para(doc: Document, text: str = "", style: str | None = None, align=None, first_line: bool = True):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if style is None:
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(24)
        p.paragraph_format.first_line_indent = Cm(0.74 if first_line else 0)
    run = p.add_run(text)
    set_run_font(run, "宋体", 12)
    return p


def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, "黑体", 15, False)
    elif level == 2:
        set_run_font(run, "楷体", 14, False)
    else:
        set_run_font(run, "宋体", 12, True)
    return p


def add_caption(doc: Document, text: str, kind: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(18)
    p.paragraph_format.space_before = Pt(4 if kind == "table" else 2)
    p.paragraph_format.space_after = Pt(4 if kind == "table" else 8)
    run = p.add_run(text)
    set_run_font(run, "黑体", 11, False)


def add_table_from_df(
    doc: Document,
    caption: str,
    df: pd.DataFrame,
    columns: list[str] | None = None,
    max_rows: int | None = None,
    percent_cols: set[str] | None = None,
    width_hints: list[float] | None = None,
) -> None:
    add_caption(doc, caption, "table")
    if columns is not None:
        df = df[columns].copy()
    if max_rows is not None:
        df = df.head(max_rows).copy()
    percent_cols = percent_cols or set()
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = True
    hdr = table.rows[0].cells
    for j, col in enumerate(df.columns):
        set_cell_text(hdr[j], str(col), bold=True, size=9)
        set_cell_shading(hdr[j], "D9EAF7")
        hdr[j].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(df.columns):
            value = row[col]
            if col in percent_cols and not isinstance(value, str):
                text = pct(value)
            elif isinstance(value, float):
                text = fmt(value)
            else:
                text = "" if pd.isna(value) else str(value)
            align = WD_ALIGN_PARAGRAPH.LEFT if len(text) > 12 or j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            set_cell_text(cells[j], text, size=9, align=align)
            cells[j].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if width_hints:
        for row in table.rows:
            for idx, width in enumerate(width_hints[: len(row.cells)]):
                row.cells[idx].width = Cm(width)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = Pt(8)
    p.paragraph_format.first_line_indent = Cm(0)


def add_figure(doc: Document, filename: str, caption: str, width_cm: float = 14.2) -> None:
    path = FIG_DIR / filename
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    add_caption(doc, caption, "figure")


def make_title_page(doc: Document) -> None:
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run("政府采购异常低价中标风险识别与监管决策研究")
    set_run_font(r, "黑体", 20, False)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run("——基于公告文本、价格规则、机器学习与关系网络的实证分析")
    set_run_font(r, "黑体", 15, False)
    for _ in range(6):
        doc.add_paragraph()
    meta = [
        "论文类型：统计建模与政府采购风险治理实证研究",
        "数据来源：中国政府采购网公告与2025Q1合同扩展样本、省级宏观指标",
        "模型路线：数据治理—风险标签—异常检测—风险解释—监管决策",
        "生成日期：2026年5月",
    ]
    for line in meta:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(line)
        set_run_font(r, "宋体", 12)
    doc.add_page_break()


def make_abstract(doc: Document, summary: dict) -> None:
    add_heading(doc, "摘要", 1)
    add_para(
        doc,
        f"异常低价中标是政府采购领域长期存在的监管难题，其表面表现为报价明显低于预算或同类项目常规价格，深层则可能与履约质量下降、供应商策略性报价、采购方式约束、地区财政环境及交易关系固化等因素有关。随着政府采购公告、合同和信用信息不断在线化，传统依赖人工经验和单一价格阈值的审查方式，已经难以适应多类别、多主体、多地区的风险识别要求。本文围绕“数据治理—风险标签—异常检测—风险解释—监管决策”的五阶段模型框架，构建政府采购异常低价风险识别与解释体系。",
    )
    add_para(
        doc,
        f"研究首先对中国政府采购网公告数据、2025年第一季度合同扩展样本和2024年省级宏观指标进行清洗融合，形成{summary['full_n']:,}条项目级样本，其中价格有效样本{summary['price_n']:,}条、服务类主样本{summary['service_n']:,}条、2025Q1扩展样本{summary['extend_n']:,}条。其次，从政策参考阈值、类别内分位数、箱线图IQR和稳健Z分数四个角度构造异常低价初始标签。结果显示，价格有效样本中规则高风险项目为{summary['price_rule_high_n']:,}个，占{summary['price_rule_high_rate']:.2%}；服务类主样本中规则高风险项目为{summary['service_rule_high_n']:,}个，占{summary['service_rule_high_rate']:.2%}。",
    )
    add_para(
        doc,
        f"在此基础上，本文采用Isolation Forest、LOF和One-Class SVM构建集成异常检测模型，并将规则风险得分纳入集成风险分数。模型在服务类主样本中识别高风险项目{summary['model_high_n']:,}个，占{summary['model_high_rate']:.2%}。进一步利用Logistic回归、Random Forest、XGBoost和SHAP进行风险因素解释，XGBoost模型测试集AUC达到{summary['xgb_auc']:.3f}，F1值为{summary['xgb_f1']:.3f}。SHAP结果表明，{summary['shap_top5']}是影响高风险识别的主要变量。QCA分析揭示了高节约率、低价格比例、高频供应商、跨省中标、高财政压力地区和高风险服务类别等因素的多重并发关系。最后，本文构建供应商—采购人关系网络，识别核心供应商、高风险采购单位和风险社群，并通过2025Q1扩展样本验证主要结论的稳健性。",
    )
    add_para(
        doc,
        "研究认为，异常低价风险并非单纯价格问题，而是价格偏离、采购类别、供应商行为、地区环境和交易网络共同作用的结果。基于实证发现，本文建议建立异常低价自动预警机制、按服务类别设置差异化阈值、完善供应商低价中标画像、强化高风险采购方式与地区监管，并将中标后履约跟踪纳入风险闭环治理。",
    )
    p = add_para(doc, "关键词：政府采购；异常低价；异常检测；XGBoost；SHAP；QCA；关系网络", first_line=False)
    p.paragraph_format.first_line_indent = Cm(0)
    add_heading(doc, "Abstract", 1)
    add_para(
        doc,
        "Abnormally low bidding in public procurement may undermine contract performance, market competition and public expenditure efficiency. Based on procurement announcements, contract records and provincial macro indicators, this study develops a five-stage analytical framework covering data governance, rule-based risk labeling, anomaly detection, risk interpretation and regulatory decision-making. A project-level dataset is constructed after service-category harmonization, supplier-name standardization, province inference and macro-data integration.",
    )
    add_para(
        doc,
        f"The empirical sample contains {summary['full_n']:,} projects, including {summary['price_n']:,} valid price observations, {summary['service_n']:,} service-sector modeling samples and {summary['extend_n']:,} out-of-sample contract observations. Rule-based labels are derived from a policy threshold, category quantiles, IQR outliers and robust Z-scores. The integrated anomaly detection model combines Isolation Forest, LOF and One-Class SVM. It identifies {summary['model_high_n']:,} high-risk projects in the main service sample. XGBoost achieves an AUC of {summary['xgb_auc']:.3f}, and SHAP analysis shows that price ratio, supplier risk score, saving rate, fiscal pressure and GDP per capita are the most influential factors.",
    )
    add_para(
        doc,
        "The findings suggest that abnormally low-bid risk is driven by the interaction between price deviation, supplier behavior, procurement mode, local fiscal environment and transaction networks. The study provides an empirical basis for differentiated review thresholds, supplier risk profiling, network-based supervision and post-award performance tracking.",
    )
    p = add_para(doc, "Keywords: public procurement; abnormally low bids; anomaly detection; XGBoost; SHAP; QCA; network analysis", first_line=False)
    p.paragraph_format.first_line_indent = Cm(0)
    doc.add_page_break()


def add_toc(doc: Document) -> None:
    add_heading(doc, "目录", 1)
    toc_lines = [
        "第一章 引言",
        "第二章 数据来源与预处理",
        "第三章 政府采购异常低价风险指标构建",
        "第四章 文本特征工程与项目画像构建",
        "第五章 异常低价中标风险识别模型",
        "第六章 风险因素解释与成因组合分析",
        "第七章 采购关系网络与风险聚集分析",
        "第八章 稳健性检验与扩展分析",
        "第九章 结论与政策建议",
        "参考文献",
    ]
    for line in toc_lines:
        p = add_para(doc, line, first_line=False)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(0)
    doc.add_page_break()


def build_paper() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "输出结果" / "analysis_key_results.json", "r", encoding="utf-8") as f:
        summary = json.load(f)

    doc = Document()
    configure_document(doc)
    make_title_page(doc)
    make_abstract(doc, summary)
    add_toc(doc)

    # Tables
    t1 = read_table("Table01_data_sources.csv")
    t2 = read_table("Table02_field_structure.csv")
    t3 = read_table("Table03_sample_split.csv")
    t4 = read_table("Table04_procurement_category_distribution.csv")
    t6 = read_table("Table06_rule_detection_comparison.csv")
    t7 = read_table("Table07_service_category_risk_rate.csv")
    t7b = read_table("Table07b_procurement_method_risk_rate.csv")
    t9 = read_table("Table09_lda_topic_interpretation.csv")
    t11 = read_table("Table11_anomaly_model_parameters.csv")
    t12 = read_table("Table12_anomaly_model_results.csv")
    t13 = read_table("Table13_high_risk_descriptive_statistics.csv")
    t14 = read_table("Table14_logistic_regression_results.csv")
    t15 = read_table("Table15_supervised_model_evaluation.csv")
    t16 = read_table("Table16_shap_importance.csv")
    t17 = read_table("Table17_qca_causal_paths.csv")
    t18 = read_table("Table18_network_node_edge_definitions.csv")
    t19 = read_table("Table19_supplier_centrality_ranking.csv")
    t20 = read_table("Table20_buyer_risk_ranking.csv")
    t21 = read_table("Table21_high_risk_community_features.csv")
    t22 = read_table("Table22_robustness_results.csv")
    t23 = read_table("Table23_procurement_category_risk_comparison.csv")
    t24 = read_table("Table24_threshold_sensitivity.csv")
    t25 = read_table("Table25_policy_recommendation_evidence.csv")

    # Chapter 1
    add_heading(doc, "第一章 引言", 1)
    add_heading(doc, "1.1 研究背景与问题提出", 2)
    add_para(doc, "政府采购是财政资金配置和公共服务供给的重要制度安排。随着采购规模扩大和电子化程度提高，采购公告、合同文本、供应商信息、价格信息和履约线索逐渐沉淀为可计算的数据资源。与此同时，异常低价中标问题在实践中频繁出现：部分项目以显著低于预算或同类项目市场水平的价格中标，后续可能通过降低服务质量、追加变更、偷工减料或履约替代等方式转嫁成本，进而损害采购人利益与公共资金绩效。国内法学研究从法律规制和案例解释角度指出，异常低价投标不仅扰乱公平竞争，也增加了合同履行和监管执法的不确定性[3-4]。")
    add_para(doc, "传统监管主要依赖固定阈值、专家经验和人工复核。该方式在小规模采购活动中具有一定可行性，但面对跨地区、多品类、高频次的政府采购数据时，容易出现三类不足：一是价格阈值缺乏类别差异，难以区分合理让利与异常低价；二是公告文本和供应商交易行为未被充分利用，难以揭示低价风险的形成机制；三是监管对象往往聚焦单个项目，忽视供应商—采购人交易网络中的风险聚集。已有政府采购数据挖掘研究表明，采购公告文本和中标信息可以通过文本分类、K近邻、主题模型等方法转化为监管特征[1-2]；招投标全流程数据整合也为跨环节风险识别提供了基础[7]。")
    add_para(doc, "基于此，本文将异常低价识别从单一价格审查拓展为多源数据融合的风险治理问题。研究对象为政府采购项目级数据，核心目标是构建可解释、可复核、可用于监管决策的异常低价风险识别框架。本文并不把模型结果直接等同于违法结论，而是将其定位为监管预警工具：通过规则标签、异常检测、监督解释和关系网络分析，为后续人工复核、履约跟踪和分类监管提供证据线索。")
    add_heading(doc, "1.2 文献综述", 2)
    add_para(doc, "异常低价识别的国外研究大体形成了三条路径。第一类是价格统计检验和计量识别。Jeong、Lee和Kim通过判别分析识别采购市场中的异常低价投标[8]，Conti、De Giovanni和Naldi提出rank-and-compare算法检测采购拍卖中的异常低价报价[9]，Hinojosa、Muñoz和Oviedo则围绕PPP项目中的异常低价报价提出统计检验思路[10]。这类研究强调报价相对分布和竞争结构，为本文构造类别分位数、IQR和稳健Z分数提供了方法启发。")
    add_para(doc, "第二类是公共采购腐败风险和红旗指标研究。Fazekas、Tóth和King基于公共采购大数据构建客观腐败风险指数，强调限制竞争、重复中标和程序异常等红旗变量[13]；Decarolis和Giorgiantonio进一步利用意大利招标公告构造腐败红旗指标[14]。Katona和Fazekas从文本挖掘角度识别限制竞争的隐性障碍[15]。这些研究表明，采购风险不只是价格偏离，还与竞争强度、文本限制条件和主体关系相关。")
    add_para(doc, "第三类是机器学习、文本挖掘和网络分析方法。Rabuzin和Modrušan使用机器学习与文本挖掘预测公共采购腐败指数[11]；Lima等构建多面向采购文本学习数据集，为公共采购文本建模提供数据范式[12]；Lyra、Pinheiro和Bação综述了网络分析在公共采购欺诈检测中的应用，指出关系结构可揭示重复交易、中心节点和风险社群[16]。在通用方法上，TF-IDF[17]、LDA[18]、Isolation Forest[19]、LOF[20]、One-Class SVM[21]、Random Forest[22]、XGBoost[23]、SHAP[24]和fsQCA[25]分别为文本特征、异常检测、监督预测、模型解释和成因组合分析提供了技术基础。")
    add_para(doc, "国内研究则更多聚焦政府采购文本挖掘、异常低价法律规制和招投标数据治理。王宏等将K近邻算法用于政府采购数据挖掘[1]，韩利利系统研究中标公告文本挖掘在政府采购中的应用[2]；苏莹莹和张怀营分别从法律规制与指导性案例角度讨论异常低价投标行为[3-4]；魏俊奎等以电力供应商投标评估为例说明大数据分析在供应商预测评价中的应用[5]；华玉雯关注大数据环境下围标串标识别[6]。总体看，现有研究为本文提供了方法与制度基础，但仍存在价格规则、文本特征、异常检测、解释模型和关系网络割裂的问题。本文的贡献在于将上述方法纳入统一的五阶段模型框架，并基于项目级真实数据给出可复核的风险识别结果。")
    add_heading(doc, "1.3 研究内容、技术路线与创新点", 2)
    add_para(doc, "本文构建“数据治理—风险标签—异常检测—风险解释—监管决策”的五阶段模型框架。第一阶段对原始公告与合同数据进行清洗、字段统一、服务类型映射、供应商名称标准化和省级宏观指标融合；第二阶段从固定阈值、类别分位数、IQR和稳健Z分数构造异常低价规则标签；第三阶段采用Isolation Forest、LOF和One-Class SVM构建集成异常检测模型；第四阶段通过Logistic、Random Forest、XGBoost、SHAP和QCA解释风险因素及其组合路径；第五阶段构建供应商—采购人关系网络，识别高风险主体和风险社群。")
    add_para(doc, "本文创新点主要体现在三方面：一是将异常低价识别从固定阈值扩展为类别内相对价格偏离与多规则投票，提高规则标签的稳健性；二是将公告文本主题、供应商画像和宏观环境变量纳入模型特征，避免只看价格而忽略风险形成条件；三是将模型输出嵌入关系网络和政策建议，形成从识别到解释再到监管行动的闭环。")
    add_figure(doc, "Fig01_research_technical_route.png", "图1 研究技术路线图")

    # Chapter 2
    add_heading(doc, "第二章 数据来源与预处理", 1)
    add_heading(doc, "2.1 数据来源", 2)
    add_para(doc, "本文使用两类政府采购项目数据：一类来自中国政府采购网公告与中标信息，另一类为2025年第一季度合同扩展样本。宏观控制变量来自2024年省级GDP、人口、人均GDP、财政收入、财政支出、财政压力、平均工资、第三产业占比和城镇化率等指标。2025年部分省级指标主要用于补充描述，正式建模中的地区控制变量采用2024年完整省级指标，以保证31个省级地区覆盖一致。")
    add_table_from_df(doc, "表1 数据来源说明表", t1, columns=["数据集", "样本量", "字段数", "正式用途"], max_rows=5, width_hints=[3, 2, 2, 7])
    add_heading(doc, "2.2 字段结构与清洗流程", 2)
    add_para(doc, "数据清洗遵循项目级分析口径。首先统一公告标题、项目名称、采购人、供应商、预算金额、中标金额、采购方式、服务类别、项目省份和公告正文等字段；其次删除预算金额或中标金额缺失、为零或极端解析异常的记录；再次将深圳、青岛、厦门等城市型省份字段映射到所属省份，并在项目省份缺失但项目城市可识别时通过城市反推省份；最后合并省级宏观指标，形成主表及四张建模表。")
    add_table_from_df(doc, "表2 字段结构说明表", t2, max_rows=7, width_hints=[3, 6, 5])
    add_figure(doc, "Fig02_data_cleaning_flow.png", "图2 数据清洗流程图")
    add_heading(doc, "2.3 样本划分与描述性统计", 2)
    add_para(doc, f"清洗后主表共包含{summary['full_n']:,}条记录。为匹配论文分析逻辑，本文从主表派生四个正式分析版本：全样本表用于描述性统计，价格有效样本表用于异常低价规则构造，服务类主样本表用于主模型、解释分析和关系网络，2025Q1扩展样本表用于稳健性检验。")
    add_table_from_df(doc, "表3 清洗后样本划分表", t3, max_rows=4, width_hints=[4, 2, 3, 3, 3])
    add_table_from_df(doc, "表4 采购大类分布表", t4, max_rows=6, width_hints=[4, 3, 3])
    add_para(doc, "从采购大类看，服务类样本占比最高，是本文主模型分析的重点；货物类、工程类和其他项目主要用于全样本描述和扩展样本稳健性比较。服务类别方面，物业管理、办公设备与耗材、信息化服务、运维维护、保洁服务和安保服务构成主要类别，说明政府采购项目同时具有后勤服务、信息技术服务和通用货物采购等多重属性。")
    add_figure(doc, "Fig03_procurement_category_distribution.png", "图3 采购大类分布图")
    add_figure(doc, "Fig04_service_category_distribution.png", "图4 统一服务类别分布图")
    add_figure(doc, "Fig05_province_distribution_top15.png", "图5 项目省份分布图")

    # Chapter 3
    add_heading(doc, "第三章 政府采购异常低价风险指标构建", 1)
    add_heading(doc, "3.1 基础价格指标", 2)
    add_para(doc, "异常低价首先表现为价格相对预算的显著偏离。本文以预算金额和中标金额为基础，构造中标/预算比例、节约率、对数预算金额和对数中标金额。为避免金额解析异常影响规则识别，仅将预算金额大于100元、中标金额大于100元且0<中标/预算比例≤1的记录纳入价格有效样本。基础指标定义如下：")
    add_para(doc, "price_ratio_i = bid_i / budget_i；saving_rate_i = 1 - price_ratio_i；log_budget_i = ln(budget_i)；log_bid_i = ln(bid_i)。", first_line=False)
    add_para(doc, "清洗结果显示，价格有效样本为7,720条。主表中仍保留异常价格标记以供数据说明和稳健性讨论，其中中标/预算比例小于0.01的记录60条，比例等于0的记录17条，比例大于1的记录93条，中标金额不超过100元的记录74条，预算金额不超过100元的记录48条。")
    add_figure(doc, "Fig06_price_ratio_histogram.png", "图6 中标/预算比例分布图")
    add_figure(doc, "Fig07_saving_rate_histogram.png", "图7 节约率分布图")
    add_heading(doc, "3.2 多规则异常低价标签", 2)
    add_para(doc, "单一价格阈值容易忽略采购类别差异。借鉴异常低价统计检验和红旗指标研究[8-14]，本文从固定阈值、类别分位数、箱线图异常值和稳健Z分数四个角度构造规则标签。固定阈值用于捕捉明显低于预算的项目，类别分位数用于识别同类项目中的相对低价，IQR适合检测箱线图下界外的离群值，稳健Z分数则通过中位数和MAD降低极端值影响。")
    add_table_from_df(doc, "表5 规则识别结果对比表", t6, max_rows=5, width_hints=[4, 3, 3, 5])
    add_figure(doc, "Fig08_service_price_ratio_boxplot.png", "图8 不同服务类别价格比例箱线图")
    add_figure(doc, "Fig09_rule_detection_counts.png", "图9 规则识别异常数量对比图")
    add_heading(doc, "3.3 综合风险等级", 2)
    add_para(doc, "本文将五个规则触发结果相加得到规则风险得分：")
    add_para(doc, "rule_risk_score_i = rule_policy65_i + rule_quantile10_i + rule_quantile5_i + rule_iqr_i + rule_robustZ_i。", first_line=False)
    add_para(doc, "当规则得分为0时定义为正常，得分为1时定义为低风险，得分为2时定义为中风险，得分大于等于3时定义为高风险。该规则兼顾严格性和可解释性：只有多个规则同时指向价格显著偏低时，项目才被划为高风险。价格有效样本中高风险项目649个，占8.41%；服务类主样本中高风险项目525个，占9.40%。")
    service_risk_view = t7[["统一服务类别", "项目数量", "规则高风险数量", "高风险比例", "中标预算比例中位数", "平均节约率"]].head(10)
    add_table_from_df(doc, "表6 不同服务类别风险率表（前10类）", service_risk_view, max_rows=10, percent_cols={"高风险比例", "平均节约率"}, width_hints=[4, 2, 2.5, 2, 2, 2])
    add_table_from_df(doc, "表7 不同采购方式风险率表", t7b[["采购方式标准化", "项目数量", "高风险数量", "高风险比例"]], max_rows=10, percent_cols={"高风险比例"}, width_hints=[4, 2, 2, 3])
    add_figure(doc, "Fig10_rule_risk_level_distribution.png", "图10 综合风险等级分布图")

    # Chapter 4
    add_heading(doc, "第四章 文本特征工程与项目画像构建", 1)
    add_heading(doc, "4.1 文本预处理与TF-IDF特征", 2)
    add_para(doc, "政府采购公告文本包含项目需求、资格条件、服务范围、履约期限和供应商信息，是异常低价风险识别的重要补充。国内研究已证明政府采购公告文本可用于采购领域分类和供应商行为分析[1-2]，国际研究也表明文本挖掘能够揭示采购竞争限制和腐败风险[11-12,15]。本文将公告标题、项目名称、公告正文、统一服务类别和采购方式合并为text_all，经过字符清洗、中文分词、停用词处理后形成词项序列，并采用TF-IDF构造文本向量。")
    add_table_from_df(doc, "表8 文本预处理规则表", read_table("Table08_text_preprocessing_rules.csv"), max_rows=6, width_hints=[3, 7, 4])
    add_para(doc, "TF-IDF方法通过词频与逆文档频率的乘积衡量词项区分度[17]，适合从公告文本中抽取服务类别、技术需求和采购对象特征。本文选取高频且具有区分度的关键词，并通过截断奇异值分解获得文本主成分，用于后续异常检测和监督模型。")
    add_figure(doc, "Fig11_overall_keyword_wordcloud.png", "图11 政府采购公告关键词词云图")
    add_figure(doc, "Fig12_high_risk_keyword_wordcloud.png", "图12 高风险项目关键词词云图")
    add_heading(doc, "4.2 LDA主题建模", 2)
    add_para(doc, "为进一步刻画项目需求结构，本文采用LDA主题模型识别公告文本中的潜在主题。LDA将文档视为主题混合、主题视为词项分布[18]，能够将长文本压缩为具有解释意义的主题概率变量。本文设置6个主题，并根据每个主题Top关键词进行解释。")
    add_table_from_df(doc, "表9 LDA主题解释表", t9[["主题编号", "主题关键词Top10", "项目数量", "规则高风险比例"]], max_rows=6, percent_cols={"规则高风险比例"}, width_hints=[2, 8, 2, 3])
    add_figure(doc, "Fig13_lda_topic_keywords.png", "图13 LDA主题关键词图")
    add_figure(doc, "Fig14_topic_high_risk_rate.png", "图14 不同主题下异常低价风险率柱状图")
    add_heading(doc, "4.3 项目画像与供应商画像", 2)
    add_para(doc, "项目画像包括价格画像、文本画像、采购画像、地区画像和风险画像。供应商画像则重点刻画中标次数、低价中标次数、平均节约率、跨省中标比例、涉及类别数和综合风险画像分。供应商维度能够反映重复中标、跨区域经营和低价策略倾向，为后续网络分析提供节点属性。")
    add_table_from_df(doc, "表10 供应商画像字段表", read_table("Table10_supplier_profile_fields.csv"), max_rows=6, width_hints=[4, 6, 4])
    add_figure(doc, "Fig15_supplier_win_count_distribution.png", "图15 供应商中标次数分布图")

    # Chapter 5
    add_heading(doc, "第五章 异常低价中标风险识别模型", 1)
    add_heading(doc, "5.1 特征体系与模型选择", 2)
    add_para(doc, "异常低价风险属于典型的小比例、弱标签和多维异常识别问题。本文以服务类主样本为主模型样本，输入特征包括价格特征、采购特征、文本主题特征、供应商画像特征和地区宏观特征。考虑到规则标签可能存在不完全性，本文采用无监督/半监督异常检测模型识别潜在异常项目。Isolation Forest通过随机切分特征空间实现异常隔离[19]，LOF基于局部密度识别相对异常点[20]，One-Class SVM通过学习高维分布支撑域识别边界外样本[21]。")
    add_table_from_df(doc, "表11 异常检测模型参数表", t11, max_rows=5, width_hints=[4, 6, 5])
    add_figure(doc, "Fig16_anomaly_detection_flow.png", "图16 异常检测模型流程图")
    add_heading(doc, "5.2 集成异常检测模型", 2)
    add_para(doc, "各异常检测模型输出的分数尺度不同，本文先对Isolation Forest、LOF和One-Class SVM得分进行0—1标准化，再与规则风险得分融合，形成集成异常分数：")
    add_para(doc, "ensemble_score_i = 0.30 IF_i + 0.25 LOF_i + 0.20 OCSVM_i + 0.25 Rule_i。", first_line=False)
    add_para(doc, "其中Rule_i为标准化后的规则风险得分。本文将集成异常分数位于前10%的服务类项目定义为模型高风险项目。该设定既保留异常检测模型对多维特征的敏感性，也避免完全脱离可解释的价格规则。")
    add_table_from_df(doc, "表12 异常检测模型结果表", t12, max_rows=5, width_hints=[4, 3, 3])
    add_figure(doc, "Fig17_anomaly_model_counts.png", "图17 不同模型识别异常项目数量对比图")
    add_figure(doc, "Fig18_anomaly_model_venn.png", "图18 异常检测模型结果重叠韦恩图")
    add_heading(doc, "5.3 模型识别结果分析", 2)
    add_para(doc, f"集成异常检测模型在服务类主样本中识别高风险项目{summary['model_high_n']:,}个，占{summary['model_high_rate']:.2%}。与规则标签相比，集成模型不仅关注价格明显偏低的项目，也会识别文本需求、供应商画像和地区环境共同显示异常的项目。从服务类别分布看，高风险项目集中于若干后勤服务和运维类项目；从地区分布看，高风险项目在样本量较高和财政压力较高地区更容易形成聚集。")
    descript = t13[t13["风险组"].eq("高风险")][["变量", "样本量", "均值", "中位数", "标准差"]].head(10)
    add_table_from_df(doc, "表13 高风险项目统计描述表", descript, max_rows=10, width_hints=[5, 2, 3, 3, 3])
    add_figure(doc, "Fig19_high_risk_service_category.png", "图19 高风险项目服务类别分布图")
    add_figure(doc, "Fig20_high_risk_province.png", "图20 高风险项目省份分布图")
    add_figure(doc, "Fig21_pca_anomaly_scatter.png", "图21 PCA二维异常项目散点图")

    # Chapter 6
    add_heading(doc, "第六章 风险因素解释与成因组合分析", 1)
    add_heading(doc, "6.1 监督模型评价", 2)
    add_para(doc, "异常检测模型给出风险识别结果后，仍需回答“为什么这些项目被识别为高风险”。因此，本文以final_high_risk为目标变量，构建Logistic回归、Random Forest和XGBoost监督模型。Logistic回归用于观察变量方向和统计解释，Random Forest用于非线性变量重要性对照[22]，XGBoost作为主要预测模型，利用梯度提升树处理复杂交互和非线性关系[23]。")
    add_table_from_df(doc, "表14 监督模型评价结果表", t15, max_rows=3, width_hints=[3, 2, 2, 2, 2, 2])
    add_figure(doc, "Fig22_supervised_model_metrics.png", "图22 模型评价指标对比图")
    add_para(doc, f"结果显示，XGBoost模型AUC为{summary['xgb_auc']:.3f}、F1值为{summary['xgb_f1']:.3f}，整体识别能力较强。需要强调的是，较高的模型表现主要说明集成高风险标签在特征空间中具有清晰结构，并不意味着模型可以直接替代监管判断；其价值在于为监管复核提供排序和解释依据。")
    add_heading(doc, "6.2 Logistic回归与变量重要性", 2)
    logit_view = t14[["变量", "系数", "p值", "优势比OR"]].head(12)
    add_table_from_df(doc, "表15 Logistic回归结果表", logit_view, max_rows=12, width_hints=[5, 3, 3, 3])
    add_figure(doc, "Fig23_random_forest_importance.png", "图23 Random Forest变量重要性图")
    add_figure(doc, "Fig24_xgboost_importance.png", "图24 XGBoost变量重要性图")
    add_heading(doc, "6.3 SHAP解释", 2)
    add_para(doc, "为解释XGBoost模型的单个变量贡献，本文引入SHAP方法。SHAP基于Shapley值思想，将模型输出分解为各特征的边际贡献，能够同时提供全局重要性和局部解释[24]。在政府采购监管场景下，SHAP的意义在于把黑箱模型输出转化为可供人工复核的风险证据链。")
    add_table_from_df(doc, "表16 SHAP重要变量排序表", t16[["变量", "mean_abs_SHAP"]].head(12), max_rows=12, width_hints=[7, 4])
    add_figure(doc, "Fig25_shap_summary.png", "图25 SHAP Summary Plot")
    add_figure(doc, "Fig26_shap_dependence_top4.png", "图26 SHAP Dependence Plot")
    add_para(doc, f"SHAP结果显示，影响模型输出的前五个变量为{summary['shap_top5']}。其中，price_ratio_clean和saving_rate_clean直接反映价格偏离；supplier_risk_score体现供应商历史低价中标、跨省中标和中标频率；fiscal_pressure与gdp_per_capita则表明地区财政环境和经济发展水平对低价风险具有解释作用。")
    add_heading(doc, "6.4 QCA成因组合", 2)
    add_para(doc, "异常低价风险往往不是单一变量导致，而是多条件并发的结果。本文借鉴fsQCA方法[25]，将高节约率、低价格比例、高频供应商、跨省中标、高财政压力、公开招标、供应商信息缺失和高风险服务类别等变量转化为集合条件，分析其与高风险结果之间的组合关系。")
    add_table_from_df(doc, "表17 QCA成因组合路径表", t17, max_rows=10, width_hints=[2, 8, 2, 2, 2, 2])
    add_figure(doc, "Fig27_qca_causal_paths.png", "图27 QCA成因路径图")
    add_para(doc, "QCA结果表明，异常低价风险具有明显的组态特征：部分路径以价格偏离为核心，叠加高频供应商和高财政压力；部分路径则由跨省中标、特定采购方式和高风险服务类别共同构成。这说明监管不宜只设置单一价格阈值，而应识别多条件叠加下的风险路径。")

    # Chapter 7
    add_heading(doc, "第七章 采购关系网络与风险聚集分析", 1)
    add_heading(doc, "7.1 网络构建", 2)
    add_para(doc, "公共采购风险具有关系嵌入性。供应商与采购人之间的重复交易、核心主体位置和社群结构，可能反映市场进入壁垒、信息不对称或监管盲区。网络分析文献指出，公共采购欺诈和腐败风险可以通过主体连接结构、中心性和社群发现获得线索[16]。本文构建供应商—采购人二部关系网络，节点包括供应商和采购人，边表示中标交易关系，边权为交易项目数量，并将高风险项目数量和平均风险分作为边属性。")
    add_table_from_df(doc, "表18 网络节点与边定义表", t18, max_rows=7, width_hints=[4, 5, 5])
    add_figure(doc, "Fig28_procurement_relation_network.png", "图28 采购关系网络总体图")
    add_heading(doc, "7.2 高风险主体识别", 2)
    add_para(doc, "本文计算加权度、度中心性、介数中心性和特征向量中心性，并结合关联高风险项目数量和高风险比例识别监管重点。供应商中心性排名反映其在交易网络中的活跃度和核心位置；采购人风险排名则反映其关联项目中高风险项目占比。")
    supplier_view = t19[["主体名称", "项目数量", "高风险项目数量", "高风险比例", "特征向量中心性", "主服务类别"]].head(10)
    buyer_view = t20[["主体名称", "项目数量", "高风险项目数量", "高风险比例", "特征向量中心性", "主服务类别"]].head(10)
    add_table_from_df(doc, "表19 高风险供应商排名表（前10）", supplier_view, max_rows=10, width_hints=[5, 2, 2, 2, 2, 4])
    add_table_from_df(doc, "表20 高风险采购单位排名表（前10）", buyer_view, max_rows=10, width_hints=[5, 2, 2, 2, 2, 4])
    add_figure(doc, "Fig29_high_risk_supplier_buyer_network.png", "图29 高风险供应商—采购人子网络图")
    add_figure(doc, "Fig30_supplier_centrality_top20.png", "图30 供应商中心性 Top 20 条形图")
    add_figure(doc, "Fig31_buyer_risk_rate_top20.png", "图31 采购单位风险率 Top 20 图")
    add_heading(doc, "7.3 风险社群分析", 2)
    community_view = t21[["社群", "节点数量", "供应商数量", "采购人数量", "关联项目数量", "高风险项目数量", "高风险比例"]].head(10)
    add_table_from_df(doc, "表21 高风险社群特征表（前10）", community_view, max_rows=10, width_hints=[1.4, 1.5, 1.6, 1.6, 2, 2.1, 1.8])
    add_para(doc, "核心主体名单较长，正文以社群规模、交易项目数和高风险比例呈现结构特征；具体供应商和采购人可结合表19、表20的中心性排名进行追踪。")
    add_figure(doc, "Fig32_risk_community_network.png", "图32 风险社群网络图")
    add_para(doc, "社群分析表明，高风险项目并非完全随机分散，而是在若干供应商—采购人交易群体中呈现聚集。对于监管部门而言，社群结果可用于形成“项目—主体—类别—地区”的联动审查清单：当某一社群同时具有高交易密度、高风险比例和核心供应商重复出现时，应优先开展合同履约、报价合理性和供应商资质复核。")

    # Chapter 8
    add_heading(doc, "第八章 稳健性检验与扩展分析", 1)
    add_heading(doc, "8.1 扩展样本规则稳健性", 2)
    add_para(doc, "为检验规则与模型结论是否具有样本外稳定性，本文使用2025Q1扩展样本进行稳健性检验。扩展样本来自合同公告，项目类型覆盖服务、货物、工程和其他类别，能够与服务类主样本形成互补。异常低价研究文献强调，不同制度环境和项目类型下低价判断应进行样本外验证[9-10]。")
    add_table_from_df(doc, "表22 稳健性检验结果表", t22, max_rows=2, width_hints=[4, 2, 3, 3, 3, 3])
    add_figure(doc, "Fig33_main_vs_extension_risk_rate.png", "图33 主样本与扩展样本风险率对比图")
    add_heading(doc, "8.2 采购大类比较与阈值敏感性", 2)
    add_para(doc, f"扩展样本中规则高风险比例为{summary['extend_rule_high_rate']:.2%}，低于服务类主样本，但主要风险方向仍与价格偏离、服务类别差异和供应商行为有关。采购大类比较显示，服务、货物和工程项目的风险率存在差异，说明异常低价审查阈值不宜完全统一。")
    add_table_from_df(doc, "表23 采购大类风险率对比表", t23, max_rows=5, width_hints=[4, 2, 2, 3])
    add_table_from_df(doc, "表24 阈值敏感性分析表", t24, max_rows=8, width_hints=[4, 4, 3, 3])
    add_figure(doc, "Fig34_category_risk_rate_comparison.png", "图34 服务类、货物类、工程类风险率对比图")
    add_figure(doc, "Fig35_threshold_sensitivity.png", "图35 不同阈值下高风险项目数量变化图")
    add_figure(doc, "Fig36_extension_high_risk_service_distribution.png", "图36 扩展样本高风险服务类型分布图")
    add_para(doc, "阈值敏感性结果表明，当固定阈值从0.60放宽至0.70时，识别数量明显增加；类别分位数从5%提高到15%也会扩大预警范围。这说明规则阈值本质上是监管资源配置参数：阈值越宽松，覆盖面越大但复核成本越高；阈值越严格，误报较少但可能遗漏边界风险。本文建议在正式监管中采用“基础阈值+类别阈值+模型排序”的组合方式，而非单一阈值。")

    # Chapter 9
    add_heading(doc, "第九章 结论与政策建议", 1)
    add_heading(doc, "9.1 研究结论", 2)
    add_para(doc, "本文基于政府采购公告、合同扩展样本和省级宏观指标，构建异常低价风险识别与监管决策模型，得到以下结论。")
    conclusions = [
        "第一，异常低价风险具有显著类别差异。服务类项目是主样本主体，不同统一服务类别的中标/预算比例分布和高风险比例存在差异，说明统一阈值难以覆盖不同服务的成本结构。",
        "第二，价格偏离、节约率和供应商风险画像是异常低价识别的核心因素。SHAP结果显示，price_ratio_clean、saving_rate_clean和supplier_risk_score对模型输出影响最大，验证了价格规则与供应商历史行为结合的必要性。",
        "第三，地区宏观环境具有解释作用。财政压力和人均GDP进入SHAP前列，表明地方财政约束和经济发展水平可能影响采购预算、供应商竞争和低价中标策略。",
        "第四，异常低价风险具有组态成因。QCA结果显示，高节约率、低价格比例、高频供应商、跨省中标、高财政压力和高风险服务类别之间存在多种组合路径，单因素解释不足。",
        "第五，风险存在网络聚集特征。供应商—采购人网络揭示了核心主体、高风险采购单位和风险社群，为监管部门从单项目审查转向主体关系治理提供了依据。",
    ]
    for item in conclusions:
        add_para(doc, item)
    add_heading(doc, "9.2 政策建议", 2)
    add_table_from_df(doc, "表25 政策建议对应模型依据表", t25, max_rows=5, width_hints=[5, 6, 3])
    add_para(doc, "第一，建立异常低价自动预警机制。监管平台可实时计算中标/预算比例、节约率、类别偏离度和规则风险得分，并结合异常检测模型输出形成项目风险排序。对于多规则触发或模型得分位于高分位的项目，应进入人工复核清单。")
    add_para(doc, "第二，按采购类别设置差异化审查阈值。物业管理、绿化养护、信息化、运维维护、咨询评估检测等服务类型的成本结构差异较大，应建立类别内分位数阈值和历史价格参照库，避免用同一固定阈值判断所有项目。")
    add_para(doc, "第三，建立供应商低价中标画像机制。对供应商中标次数、低价中标次数、平均节约率、跨省中标比例和服务类别广度进行持续更新，形成供应商风险画像。对高频低价中标且网络中心性较高的供应商，应强化履约质量和报价合理性复核。")
    add_para(doc, "第四，加强高风险采购方式和高风险地区监管。对于风险率较高的采购方式以及财政压力较高地区，应提高抽查比例，关注低价中标后的合同变更、追加采购和履约评价。")
    add_para(doc, "第五，建立中标后履约跟踪机制。异常低价项目的风险不止发生在中标阶段，还可能在履约阶段表现为服务质量下降、人员配置不足或后续变更增加。因此，应将模型预警结果与履约验收、投诉质疑和信用评价衔接起来，形成监管闭环。")
    add_figure(doc, "Fig37_regulatory_closed_loop.png", "图37 政府采购异常低价风险监管闭环图")
    add_heading(doc, "9.3 研究不足与展望", 2)
    add_para(doc, "本文仍存在若干不足。第一，部分项目省份和城市字段由文本或城市映射推断，仍可能存在识别误差；第二，异常低价标签是风险标签而非执法认定，缺少履约质量、投诉处理和审计处罚等外部结果变量；第三，文本主题模型主要使用公告正文，尚未引入招标文件全文和合同履约细节；第四，关系网络以供应商—采购人为主，未来可进一步扩展到代理机构、评审专家和信用处罚信息。后续研究可结合更长时期数据和履约结果，构建动态风险预警模型。")

    # References
    add_heading(doc, "参考文献", 1)
    refs = [
        "王宏, 门博, 雷娜. K近邻算法在政府采购数据挖掘中的研究与应用[J]. 智能计算机与应用, 2019.",
        "韩利利. 中标公告文本挖掘方法及在政府采购中的应用研究[D]. 硕士学位论文, 2018.",
        "苏莹莹. 论政府采购中异常低价投标的法律规制[D]. 硕士学位论文, 2020.",
        "张怀营. 对政府采购活动中异常低价投标行为的探讨——从财政部政府采购指导性案例19号切入[J]. 法学, 2024.",
        "魏俊奎, 周顺凯, 金义. 基于大数据分析的电力供应商投标评估预测方案研究[J]. 微型电脑应用, 2019.",
        "华玉雯. 大数据下围标串标现象识别研究[D]. 学位论文.",
        "李玺, 崔永涛, 金坎明. 招投标全流程数据整合思路研究[C]. 智能电网信息化建设研讨会论文集, 2018.",
        "Jeong J, Lee H, Kim. An econometric identification of abnormally low bids in the procurement market: discriminant analysis[R]. Economic Research Institute Yonsei University, 2018.",
        "Conti P L, De Giovanni L, Naldi M. A rank-and-compare algorithm to detect abnormally low bids in procurement auctions[J]. Electronic Commerce Research and Applications.",
        "Hinojosa S, Muñoz F, Oviedo C. Abnormally low bids in PPPs: Analysis of evidence and a proposed statistical test[J].",
        "Rabuzin K, Modrušan N. Prediction of Public Procurement Corruption Indices using Machine Learning Methods[C].",
        "Lima W, Silva V, Silva J, Lira R, Paiva A. BidCorpus: A multifaceted learning dataset for public procurement[J]. Data in Brief, 2025.",
        "Fazekas M, Tóth I J, King L P. An objective corruption risk index using public procurement data[J]. European Journal on Criminal Policy and Research, 2016.",
        "Decarolis F, Giorgiantonio C. Corruption red flags in public procurement: new evidence from Italian calls for tenders[J]. EPJ Data Science, 2022.",
        "Katona E, Fazekas M. Hidden barriers to open competition: Using text mining to uncover corrupt restrictions to competition in public procurement[R]. 2024.",
        "Lyra M S, Pinheiro F L, Bação F. Public Procurement Fraud Detection: A Review Using Network Analysis[C]. 2022.",
        "Salton G, Buckley C. Term-weighting approaches in automatic text retrieval[J]. Information Processing & Management, 1988.",
        "Blei D M, Ng A Y, Jordan M I. Latent Dirichlet Allocation[J]. Journal of Machine Learning Research, 2003.",
        "Liu F T, Ting K M, Zhou Z H. Isolation Forest[C]. IEEE International Conference on Data Mining, 2008.",
        "Breunig M M, Kriegel H P, Ng R T, Sander J. LOF: Identifying density-based local outliers[C]. ACM SIGMOD, 2000.",
        "Schölkopf B, Platt J C, Shawe-Taylor J, Smola A J, Williamson R C. Estimating the support of a high-dimensional distribution[J]. Neural Computation, 2001.",
        "Breiman L. Random Forests[J]. Machine Learning, 2001.",
        "Chen T, Guestrin C. XGBoost: A scalable tree boosting system[C]. KDD, 2016.",
        "Lundberg S M, Lee S I. A unified approach to interpreting model predictions[C]. NIPS, 2017.",
        "Pappas I O, Woodside A G. Fuzzy-set Qualitative Comparative Analysis (fsQCA): Guidelines for research practice in Information Systems and marketing[J]. International Journal of Information Management, 2021.",
    ]
    for i, ref in enumerate(refs, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.74)
        p.paragraph_format.first_line_indent = Cm(-0.74)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(20)
        run = p.add_run(f"[{i}] {ref}")
        set_run_font(run, "宋体", 10)

    doc.save(DOCX_PATH)
    print(DOCX_PATH)


if __name__ == "__main__":
    build_paper()
