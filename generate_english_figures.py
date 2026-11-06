from __future__ import annotations

import math
import os
import re
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.ticker import PercentFormatter
from matplotlib_venn import venn3
from sklearn.decomposition import PCA
from wordcloud import WordCloud


ROOT = Path(os.environ["CODE_ROOT"])
FIG_SRC = next(p.parent for p in ROOT.rglob("Fig01_research_technical_route.png"))
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
INK = "#111827"
MUTED = "#64748B"
GRID = "#E5E7EB"
AXIS = "#CBD5E1"
PANEL = "#FAFBFD"
BLUE = "#2563A6"
TEAL = "#0F766E"
PURPLE = "#5E548E"
ORANGE = "#B45309"
RED = "#9F2A2A"
GREEN = "#2E7D64"
PALETTE = [BLUE, PURPLE, TEAL, ORANGE, RED, GREEN, "#4B5563", "#8B6F47"]


PROC_CAT = {"服务类": "Services", "货物类": "Goods", "工程类": "Works", "其他": "Other"}
METHOD = {
    "公开招标": "Open Tender",
    "竞争性磋商": "Competitive Consultation",
    "框架协议": "Framework Agreement",
    "竞争性谈判": "Competitive Negotiation",
    "询价": "Inquiry",
    "单一来源": "Single Source",
    "电子卖场": "E-Marketplace",
    "定点采购": "Designated Procurement",
    "其他": "Other",
}
SERVICE = {
    "物业管理": "Property Mgmt.",
    "运维维护": "O&M Service",
    "保洁服务": "Cleaning",
    "信息化服务": "IT Service",
    "绿化养护": "Landscaping",
    "安保服务": "Security",
    "车辆服务": "Vehicle Service",
    "餐饮与食材供应": "Catering & Food",
    "宣传印刷": "Publicity & Printing",
    "咨询评估检测": "Consulting & Testing",
    "教育培训": "Training",
    "医疗卫生服务": "Healthcare Service",
    "保险服务": "Insurance",
    "会议会展": "Conference Service",
    "后勤服务": "Logistics",
    "其他服务": "Other Service",
    "未识别": "Unidentified",
}
PROVINCE = {
    "北京": "Beijing",
    "天津": "Tianjin",
    "河北": "Hebei",
    "山西": "Shanxi",
    "内蒙古": "Inner Mongolia",
    "辽宁": "Liaoning",
    "吉林": "Jilin",
    "黑龙江": "Heilongjiang",
    "上海": "Shanghai",
    "江苏": "Jiangsu",
    "浙江": "Zhejiang",
    "安徽": "Anhui",
    "福建": "Fujian",
    "江西": "Jiangxi",
    "山东": "Shandong",
    "河南": "Henan",
    "湖北": "Hubei",
    "湖南": "Hunan",
    "广东": "Guangdong",
    "广西": "Guangxi",
    "海南": "Hainan",
    "重庆": "Chongqing",
    "四川": "Sichuan",
    "贵州": "Guizhou",
    "云南": "Yunnan",
    "西藏": "Tibet",
    "陕西": "Shaanxi",
    "甘肃": "Gansu",
    "青海": "Qinghai",
    "宁夏": "Ningxia",
    "新疆": "Xinjiang",
}
RISK_LEVEL = {"正常": "Normal", "低风险": "Low Risk", "中风险": "Medium Risk", "高风险": "High Risk"}
MODEL_NAME = {"规则高风险": "Rule High Risk", "集成模型高风险": "Ensemble High Risk"}
QCA = {
    "高节约率": "High Saving",
    "低价格比例": "Low Price Ratio",
    "高频供应商": "Frequent Supplier",
    "跨省中标": "Cross-province Win",
    "高财政压力": "High Fiscal Pressure",
    "公开招标": "Open Tender",
    "供应商信息缺失": "Supplier Missing",
    "高风险服务类别": "High-risk Service",
    "非跨省中标": "Non-cross-province",
    "非公开招标": "Non-open Tender",
}
KEYWORD = {
    "地址": "address",
    "联系人": "contact",
    "物业管理": "property mgmt",
    "招标": "tender",
    "标的": "target",
    "主要": "main",
    "评审": "review",
    "投标": "bid",
    "采购": "procurement",
    "服务": "service",
    "项目": "project",
    "公告": "notice",
    "合同": "contract",
    "车辆": "vehicle",
    "绿化": "landscaping",
    "养护": "maintenance",
    "运维": "O&M",
    "系统": "system",
    "资格": "qualification",
    "专家": "expert",
    "单位": "agency",
    "联系电话": "phone",
    "单位名称": "agency name",
    "中小企业": "SME",
    "质疑": "challenge",
    "结果": "result",
    "街道": "subdistrict",
    "日期": "date",
    "签订": "signing",
    "履约": "performance",
    "数量": "quantity",
    "甲方": "party A",
    "单价": "unit price",
    "规格型号": "specification",
    "乙方": "party B",
    "编号": "number",
}
VAR = {
    "price_ratio_clean": "Price Ratio",
    "saving_rate_clean": "Saving Rate",
    "supplier_risk_score": "Supplier Risk Score",
    "supplier_low_price_rate": "Supplier Low-price Rate",
    "supplier_win_count": "Supplier Win Count",
    "supplier_cross_province_rate": "Cross-province Rate",
    "supplier_category_count": "Supplier Category Count",
    "text_length": "Text Length",
    "fiscal_pressure": "Fiscal Pressure",
    "gdp_per_capita": "GDP per Capita",
    "average_wage": "Average Wage",
    "tertiary_industry_share": "Tertiary Share",
    "urbanization_rate": "Urbanization Rate",
    "log_budget": "Log Budget",
    "log_bid": "Log Winning Bid",
}


def path(name: str) -> Path:
    matches = list(ROOT.rglob(name))
    if not matches:
        raise FileNotFoundError(name)
    return matches[0]


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(path(name), encoding="utf-8-sig")


def out(name: str) -> Path:
    return OUT_DIR / name.replace(".png", "_en.png")


def en(value, mapping=None, prefix="Item") -> str:
    if pd.isna(value):
        return "Unknown"
    s = str(value).strip()
    if mapping and s in mapping:
        return mapping[s]
    if s in VAR:
        return VAR[s]
    if s in METHOD:
        return METHOD[s]
    if s in SERVICE:
        return SERVICE[s]
    if s in PROC_CAT:
        return PROC_CAT[s]
    if s in PROVINCE:
        return PROVINCE[s]
    if s in MODEL_NAME:
        return MODEL_NAME[s]
    if re.fullmatch(r"[A-Za-z0-9_ .:/()%+-]+", s):
        return s
    if s.startswith("主题"):
        return "Topic " + re.sub(r"\D+", "", s)
    if s.startswith("路径"):
        return "Path " + re.sub(r"\D+", "", s)
    return f"{prefix} {abs(hash(s)) % 1000:03d}"


def short(s: str, n=22) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."


def title_without_number(text: str) -> str:
    return re.sub(r"^\s*Fig\.?\s*\d+[A-Za-z]?\s+", "", text or "").strip()


def style(ax):
    for loc in ["left", "center", "right"]:
        title = ax.get_title(loc=loc)
        cleaned = title_without_number(title)
        if title != cleaned:
            ax.set_title(cleaned, loc=loc)
    ax.set_facecolor(PANEL)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=3, width=0.7)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.title.set_color(INK)
    ax.title.set_weight("semibold")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.grid(True, color=GRID, linewidth=0.65, alpha=0.45, zorder=0)


def save(fig, name):
    fig.patch.set_facecolor("white")
    if getattr(fig, "_suptitle", None) is not None:
        fig._suptitle.set_text(title_without_number(fig._suptitle.get_text()))
    for ax in fig.axes:
        if ax.get_visible():
            style(ax)
    fig.savefig(out(name), bbox_inches="tight", pad_inches=0.08, facecolor="white", dpi=420)
    plt.close(fig)


def bar(data, x, y, title, name, xlabel="", ylabel="", horizontal=False, color=BLUE, percent=False, sort=False):
    df = data.copy()
    if sort:
        df = df.sort_values(y if not horizontal else x, ascending=horizontal)
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    if horizontal:
        ax.barh(df[y], df[x], color=color, edgecolor="white", linewidth=0.7, zorder=3)
        for yi, val in enumerate(df[x]):
            label = f"{val:.1%}" if percent else f"{val:.0f}"
            ax.text(val + max(df[x].max(), 1) * 0.01, yi, label, va="center", fontsize=8.2, color=INK, zorder=4)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if percent:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    else:
        ax.bar(df[x], df[y], color=color, edgecolor="white", linewidth=0.7, zorder=3)
        for xi, val in enumerate(df[y]):
            label = f"{val:.1%}" if percent else f"{val:.0f}"
            ax.text(xi, val, label, ha="center", va="bottom", fontsize=8.2, color=INK, zorder=4)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=30)
        if percent:
            ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title(title, loc="left")
    save(fig, name)


def flow(name, title, steps, horizontal=True, colors=None):
    colors = colors or [BLUE, TEAL, PURPLE, ORANGE, RED, GREEN]
    fig, ax = plt.subplots(figsize=(11, 5.6 if horizontal else 7))
    ax.axis("off")
    ax.set_title(title, loc="left", pad=12)
    if horizontal:
        xs = np.linspace(0.08, 0.92, len(steps))
        y = 0.52
        for i, (x, text) in enumerate(zip(xs, steps)):
            box = patches.FancyBboxPatch(
                (x - 0.065, y - 0.075),
                0.13,
                0.15,
                boxstyle="round,pad=0.018,rounding_size=0.012",
                facecolor="white",
                edgecolor=colors[i % len(colors)],
                linewidth=1.6,
            )
            ax.add_patch(box)
            ax.text(x, y, "\n".join(textwrap.wrap(text, 16)), ha="center", va="center", fontsize=9)
            if i < len(xs) - 1:
                ax.annotate("", xy=(xs[i + 1] - 0.08, y), xytext=(x + 0.08, y), arrowprops=dict(arrowstyle="->", lw=1.2, color=MUTED))
    else:
        ys = np.linspace(0.85, 0.16, len(steps))
        x = 0.5
        for i, (y, text) in enumerate(zip(ys, steps)):
            box = patches.FancyBboxPatch(
                (x - 0.16, y - 0.045),
                0.32,
                0.09,
                boxstyle="round,pad=0.018,rounding_size=0.012",
                facecolor="white",
                edgecolor=colors[i % len(colors)],
                linewidth=1.6,
            )
            ax.add_patch(box)
            ax.text(x, y, "\n".join(textwrap.wrap(text, 28)), ha="center", va="center", fontsize=9)
            if i < len(ys) - 1:
                ax.annotate("", xy=(x, ys[i + 1] + 0.06), xytext=(x, y - 0.06), arrowprops=dict(arrowstyle="->", lw=1.2, color=MUTED))
    save(fig, name)


def parse_pct(s):
    if isinstance(s, str) and s.endswith("%"):
        return float(s[:-1]) / 100
    return pd.to_numeric(s, errors="coerce")


def generate():
    full = read_csv("price_valid_sample_rule_recalculated.csv")
    service = read_csv("service_main_model_results_full.csv")
    ext = read_csv("extension_2025q1_rule_recalculated.csv")

    flow("Fig01_research_technical_route.png", "Fig. 1 Research Technical Route", ["Data acquisition", "Data cleaning", "Rule-based labels", "Anomaly detection", "Explainability", "Network analysis", "Policy implications"])
    flow("Fig02_data_cleaning_flow.png", "Fig. 2 Data Cleaning Workflow", ["Raw notices", "Field standardization", "Price validation", "Category mapping", "Supplier normalization", "Macro merge", "Model-ready tables"], horizontal=False)

    t4 = read_csv("Table04_procurement_category_distribution.csv")
    t4["Category"] = t4["采购大类"].map(lambda x: en(x, PROC_CAT))
    bar(t4, "Category", "项目数量", "Fig. 3 Procurement Category Distribution", "Fig03_procurement_category_distribution.png", "Procurement Category", "Number of Projects", color=BLUE)

    svc_counts = service["统一服务类别"].map(lambda x: en(x, SERVICE)).value_counts().head(15).reset_index()
    svc_counts.columns = ["Category", "Projects"]
    bar(svc_counts, "Projects", "Category", "Fig. 4 Service Category Distribution", "Fig04_service_category_distribution.png", "Number of Projects", "Service Category", horizontal=True, color=ORANGE, sort=True)

    prov = full["项目省份"].map(lambda x: en(x, PROVINCE)).value_counts().head(15).reset_index()
    prov.columns = ["Province", "Projects"]
    bar(prov, "Projects", "Province", "Fig. 5 Top 15 Provincial Distribution", "Fig05_province_distribution_top15.png", "Number of Projects", "Province", horizontal=True, color=TEAL, sort=True)

    for col, title, fname, xlabel, color in [
        ("price_ratio_clean", "Fig. 6 Distribution of Winning Bid/Budget Ratio", "Fig06_price_ratio_histogram.png", "Winning Bid / Budget Ratio", BLUE),
        ("saving_rate_clean", "Fig. 7 Distribution of Saving Rate", "Fig07_saving_rate_histogram.png", "Saving Rate", ORANGE),
    ]:
        fig, ax = plt.subplots(figsize=(9.5, 5.6))
        vals = pd.to_numeric(full[col], errors="coerce").dropna()
        ax.hist(vals, bins=45, color=color, alpha=0.78, edgecolor="white")
        ax.axvline(vals.median(), color=RED, linestyle="--", lw=1.2, label="Median")
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Frequency")
        ax.legend()
        save(fig, fname)

    fig, ax = plt.subplots(figsize=(11, 5.8))
    top_services = service["统一服务类别"].value_counts().head(10).index
    box_data = [service.loc[service["统一服务类别"] == c, "price_ratio_clean"].dropna() for c in top_services]
    ax.boxplot(box_data, labels=[en(c, SERVICE) for c in top_services], patch_artist=True, boxprops=dict(facecolor="#DBEAFE", color=BLUE), medianprops=dict(color=RED))
    ax.set_title("Fig. 8 Price Ratio by Service Category", loc="left")
    ax.set_xlabel("Service Category")
    ax.set_ylabel("Winning Bid / Budget Ratio")
    ax.tick_params(axis="x", rotation=30)
    save(fig, "Fig08_service_price_ratio_boxplot.png")

    rules = read_csv("Table06_rule_detection_comparison.csv")
    rules["Rule"] = ["Policy < 0.65", "Within-category P10", "Within-category P5", "IQR Outlier", "Robust Z"]
    bar(rules, "Rule", "识别异常项目数量", "Fig. 9 Rule-based Detection Counts", "Fig09_rule_detection_counts.png", "Rule Type", "Detected Projects", color=PURPLE)

    risk_level = full["rule_risk_level"].map(lambda x: en(x, RISK_LEVEL)).value_counts().reindex(["Normal", "Low Risk", "Medium Risk", "High Risk"]).dropna().reset_index()
    risk_level.columns = ["Risk Level", "Projects"]
    bar(risk_level, "Risk Level", "Projects", "Fig. 10 Rule Risk Level Distribution", "Fig10_rule_risk_level_distribution.png", "Risk Level", "Projects", color=GREEN)

    def wordcloud_from_table(df, word_col, freq_col, title, fname, color):
        freq = {}
        for _, r in df.head(80).iterrows():
            w = KEYWORD.get(str(r[word_col]), en(r[word_col], prefix="KW"))
            freq[w] = max(float(r[freq_col] or 0), 1.0)
        wc = WordCloud(width=1800, height=1100, background_color="white", colormap=color, max_words=120, random_state=RANDOM_STATE).generate_from_frequencies(freq)
        fig, ax = plt.subplots(figsize=(10.8, 6.6))
        ax.imshow(wc, interpolation="bilinear")
        ax.set_title(title, loc="left")
        ax.axis("off")
        save(fig, fname)

    wordcloud_from_table(read_csv("Table10c_overall_keywords.csv"), "关键词", "词频", "Fig. 11 Overall Notice Keywords", "Fig11_overall_keyword_wordcloud.png", "viridis")
    risk_kw = read_csv("Table10d_risk_vs_normal_keywords.csv")
    wordcloud_from_table(risk_kw.sort_values("高风险词频", ascending=False), "关键词", "高风险词频", "Fig. 12 High-risk Project Keywords", "Fig12_high_risk_keyword_wordcloud.png", "plasma")
    wordcloud_from_table(risk_kw.sort_values("正常项目词频", ascending=False), "关键词", "正常项目词频", "Fig. 12b Normal Project Keywords", "Fig12b_normal_keyword_wordcloud.png", "cividis")

    topics = read_csv("Table09_lda_topic_interpretation.csv")
    fig, ax = plt.subplots(figsize=(11, 5.8))
    y = np.arange(len(topics))
    ax.barh(y, topics["项目数量"], color=BLUE, zorder=3)
    labels = []
    for _, r in topics.iterrows():
        words = [KEYWORD.get(w.strip(), en(w.strip(), prefix="Term")) for w in str(r["主题关键词Top10"]).split("、")[:4]]
        labels.append(f"Topic {int(r['主题编号'])}: " + ", ".join(words))
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_title("Fig. 13 LDA Topic Keywords", loc="left")
    ax.set_xlabel("Number of Projects")
    save(fig, "Fig13_lda_topic_keywords.png")
    topics["Topic"] = topics["主题编号"].map(lambda x: f"Topic {int(x)}")
    bar(topics, "Topic", "规则高风险比例", "Fig. 14 High-risk Rate by Topic", "Fig14_topic_high_risk_rate.png", "LDA Topic", "High-risk Rate", color=RED, percent=True)

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.hist(service["supplier_win_count"].dropna(), bins=40, color=TEAL, alpha=0.78, edgecolor="white")
    ax.set_title("Fig. 15 Supplier Win Count Distribution", loc="left")
    ax.set_xlabel("Supplier Win Count")
    ax.set_ylabel("Frequency")
    save(fig, "Fig15_supplier_win_count_distribution.png")
    flow("Fig16_anomaly_detection_flow.png", "Fig. 16 Anomaly Detection Workflow", ["Input features", "Scaling & encoding", "Isolation Forest / LOF / One-Class SVM", "Score normalization", "Ensemble risk score", "High-risk identification"])

    model = read_csv("Table12_anomaly_model_results.csv")
    model["Method"] = model["识别方式"].map(lambda x: en(x))
    bar(model, "Method", "高风险/异常项目数量", "Fig. 17 Anomaly Counts by Model", "Fig17_anomaly_model_counts.png", "Detection Method", "Count", color=PURPLE)

    set_if = set(service.index[service["iforest_anomaly"] == 1])
    set_lof = set(service.index[service["lof_anomaly"] == 1])
    set_svm = set(service.index[service["ocsvm_anomaly"] == 1])
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    venn3([set_if, set_lof, set_svm], ("Isolation Forest", "LOF", "One-Class SVM"), ax=ax)
    ax.set_title("Fig. 18 Overlap among Anomaly Models", loc="left")
    save(fig, "Fig18_anomaly_model_venn.png")

    high_svc = service[service["final_high_risk"] == 1]["统一服务类别"].map(lambda x: en(x, SERVICE)).value_counts().head(15).reset_index()
    high_svc.columns = ["Service", "Count"]
    bar(high_svc, "Count", "Service", "Fig. 19 High-risk Service Categories", "Fig19_high_risk_service_category.png", "High-risk Count", "Service Category", horizontal=True, color=RED, sort=True)
    high_prov = service[service["final_high_risk"] == 1]["项目省份"].map(lambda x: en(x, PROVINCE)).value_counts().head(15).reset_index()
    high_prov.columns = ["Province", "Count"]
    bar(high_prov, "Count", "Province", "Fig. 20 High-risk Projects by Province", "Fig20_high_risk_province.png", "High-risk Count", "Province", horizontal=True, color=ORANGE, sort=True)

    feature_cols = [c for c in ["price_ratio_clean", "saving_rate_clean", "supplier_risk_score", "fiscal_pressure", "gdp_per_capita", "text_length", "supplier_win_count", "supplier_low_price_rate"] if c in service.columns]
    pca_data = service[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(service[feature_cols].median(numeric_only=True))
    pca = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform((pca_data - pca_data.mean()) / pca_data.std(ddof=0).replace(0, 1))
    fig, ax = plt.subplots(figsize=(7.8, 6.2))
    colors = np.where(service["final_high_risk"] == 1, RED, BLUE)
    ax.scatter(pca[:, 0], pca[:, 1], c=colors, s=18, alpha=0.65, edgecolor="white", linewidth=0.2, zorder=3)
    ax.set_title("Fig. 21 PCA Projection of Anomaly Risk", loc="left")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    save(fig, "Fig21_pca_anomaly_scatter.png")

    eval_t = read_csv("Table15_supervised_model_evaluation.csv")
    metrics = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    x = np.arange(len(eval_t))
    width = 0.15
    for i, m in enumerate(metrics):
        ax.bar(x + (i - 2) * width, eval_t[m], width, label=m, color=PALETTE[i], zorder=3)
    ax.set_xticks(x, eval_t["模型"])
    ax.set_ylim(0, 1.05)
    ax.set_title("Fig. 22 Supervised Model Metrics", loc="left")
    ax.set_ylabel("Score")
    ax.legend(ncol=3, fontsize=8)
    save(fig, "Fig22_supervised_model_metrics.png")

    for fname, title, outname, valcol, color in [
        ("Table16b_random_forest_importance.csv", "Fig. 23 Random Forest Feature Importance", "Fig23_random_forest_importance.png", "重要性", BLUE),
        ("Table16c_xgboost_importance.csv", "Fig. 24 XGBoost Feature Importance", "Fig24_xgboost_importance.png", "重要性", PURPLE),
        ("Table16_shap_importance.csv", "Fig. 25 SHAP Mean Absolute Importance", "Fig25_shap_summary.png", "mean_abs_SHAP", RED),
    ]:
        df = read_csv(fname).head(15).copy()
        df["Feature"] = df["变量"].map(en).map(lambda s: short(s, 26))
        bar(df.sort_values(valcol), valcol, "Feature", title, outname, "Importance", "Feature", horizontal=True, color=color)

    shap_top = read_csv("Table16_shap_importance.csv").head(4)["变量"].tolist()
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    for ax, col in zip(axes.ravel(), shap_top):
        if col in service.columns:
            x = pd.to_numeric(service[col], errors="coerce")
        else:
            x = pd.Series(np.arange(len(service)), index=service.index)
        yv = service["ensemble_risk_score"]
        ax.scatter(x, yv, s=9, alpha=0.35, color=PURPLE, zorder=3)
        ax.set_title(en(col), loc="left", fontsize=10)
        ax.set_xlabel(en(col))
        ax.set_ylabel("Ensemble Risk Score")
    fig.suptitle("Fig. 26 Dependence of Key Features", x=0.02, ha="left", fontweight="semibold")
    fig.tight_layout()
    save(fig, "Fig26_shap_dependence_top4.png")

    qca = read_csv("Table17_qca_causal_paths.csv")
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.axis("off")
    ax.set_title("Fig. 27 QCA Exploratory Risk Paths", loc="left")
    ys = np.linspace(0.82, 0.18, len(qca))
    for y, (_, r) in zip(ys, qca.iterrows()):
        ax.text(0.02, y, en(r["路径编号"]), va="center", weight="bold", color=BLUE)
        conditions = [QCA.get(c.strip(), c.strip()) for c in str(r["风险线索组合"]).split(" × ")]
        text = " + ".join(conditions[:5]) + (" ..." if len(conditions) > 5 else "")
        ax.text(0.16, y, text, va="center", fontsize=9)
        ax.annotate("", xy=(0.82, y), xytext=(0.70, y), arrowprops=dict(arrowstyle="->", color=MUTED))
        ax.text(0.88, y, f"Consistency\n{r['一致性']:.2f}", ha="center", va="center", color=RED, weight="bold")
    save(fig, "Fig27_qca_causal_paths.png")

    # Network figures using anonymized English labels.
    edges = (
        service.dropna(subset=["统一供应商名称", "采购人名称"])
        .groupby(["统一供应商名称", "采购人名称"])
        .agg(weight=("记录ID", "count"), risk=("final_high_risk", "sum"), score=("ensemble_risk_score", "mean"))
        .reset_index()
    )
    G = nx.Graph()
    for _, r in edges.iterrows():
        s = "S" + str(abs(hash(r["统一供应商名称"])) % 10000)
        b = "B" + str(abs(hash(r["采购人名称"])) % 10000)
        G.add_node(s, kind="Supplier")
        G.add_node(b, kind="Buyer")
        G.add_edge(s, b, weight=float(r["weight"]), risk=float(r["risk"]), score=float(r["score"]))

    def draw_net(nodes, title, fname, focus_risk=False, max_edges=180):
        cand = []
        seed = set(nodes)
        for u, v, d in G.edges(data=True):
            if u in seed or v in seed:
                cand.append((d.get("risk", 0) * (8 if focus_risk else 3) + d.get("weight", 1), u, v))
        sub = G.edge_subgraph([(u, v) for _, u, v in sorted(cand, reverse=True)[:max_edges]]).copy()
        if sub.number_of_nodes() == 0:
            sub = G.subgraph(list(G.nodes())[:80]).copy()
        pos = nx.spring_layout(sub, seed=RANDOM_STATE, k=0.45)
        fig, ax = plt.subplots(figsize=(10.8, 7.2))
        node_colors = [TEAL if sub.nodes[n].get("kind") == "Supplier" else ORANGE for n in sub.nodes()]
        sizes = [35 + 10 * sub.degree(n) for n in sub.nodes()]
        edge_widths = [0.4 + 0.25 * sub[u][v].get("weight", 1) for u, v in sub.edges()]
        nx.draw_networkx_edges(sub, pos, ax=ax, edge_color="#94A3B8", width=edge_widths, alpha=0.35)
        nx.draw_networkx_nodes(sub, pos, ax=ax, node_color=node_colors, node_size=sizes, edgecolors="white", linewidths=0.4, alpha=0.9)
        ax.set_title(title, loc="left")
        ax.axis("off")
        save(fig, fname)

    deg_nodes = sorted(G.nodes(), key=lambda n: G.degree(n, weight="weight"), reverse=True)[:160]
    risk_nodes = sorted(G.nodes(), key=lambda n: sum(G[n][m].get("risk", 0) for m in G.neighbors(n)), reverse=True)[:140]
    draw_net(deg_nodes, "Fig. 28 Procurement Relation Network (Core Nodes)", "Fig28_procurement_relation_network.png")
    draw_net(risk_nodes, "Fig. 29 High-risk Supplier-Buyer Subnetwork", "Fig29_high_risk_supplier_buyer_network.png", True)

    sup = read_csv("Table19_supplier_centrality_ranking.csv").head(20).copy()
    sup["Entity"] = [f"Supplier {i+1}" for i in range(len(sup))]
    bar(sup.sort_values("特征向量中心性"), "特征向量中心性", "Entity", "Fig. 30 Supplier Eigenvector Centrality Top 20", "Fig30_supplier_centrality_top20.png", "Eigenvector Centrality", "Supplier", horizontal=True, color=BLUE)
    buyer = read_csv("Table20_buyer_risk_ranking.csv").head(20).copy()
    buyer["Entity"] = [f"Buyer {i+1}" for i in range(len(buyer))]
    bar(buyer.sort_values("高风险比例"), "高风险比例", "Entity", "Fig. 31 Buyer High-risk Rate Top 20", "Fig31_buyer_risk_rate_top20.png", "High-risk Rate", "Buyer", horizontal=True, color=RED, percent=True)

    comm = read_csv("Table21_high_risk_community_features.csv").head(25).copy()
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    sizes = np.sqrt(comm["关联项目数量"].astype(float)) * 90
    sc = ax.scatter(comm["节点数量"], comm["高风险比例"], s=sizes, c=comm["高风险项目数量"], cmap="magma", alpha=0.75, edgecolor="white", linewidth=0.5, zorder=3)
    ax.set_title("Fig. 32 Risk Community Network Summary", loc="left")
    ax.set_xlabel("Number of Nodes")
    ax.set_ylabel("High-risk Rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    fig.colorbar(sc, ax=ax, label="High-risk Projects")
    save(fig, "Fig32_risk_community_network.png")

    rb = read_csv("Table22_robustness_results.csv")
    rb["Sample"] = ["Main Service Sample", "2025Q1 Extension Sample"]
    bar(rb, "Sample", "规则高风险比例", "Fig. 33 Main vs Extension Risk Rate", "Fig33_main_vs_extension_risk_rate.png", "Sample", "Rule High-risk Rate", color=TEAL, percent=True)
    cat = read_csv("Table23_procurement_category_risk_comparison.csv")
    cat["Category"] = cat["采购大类"].map(lambda x: en(x, PROC_CAT))
    bar(cat, "Category", "高风险比例", "Fig. 34 Category Risk Rate Comparison", "Fig34_category_risk_rate_comparison.png", "Procurement Category", "High-risk Rate", color=BLUE, percent=True)
    th = read_csv("Table24_threshold_sensitivity.csv")
    th["Threshold"] = ["Fixed <0.60", "Fixed <0.65", "Fixed <0.70", "Within-cat. P5", "Within-cat. P10", "Within-cat. P15"]
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.plot(th["Threshold"], th["识别数量"], marker="o", lw=2.2, color=RED, zorder=3)
    for x, yv in zip(th["Threshold"], th["识别数量"]):
        ax.text(x, yv, f"{int(yv)}", ha="center", va="bottom", fontsize=8.2)
    ax.set_title("Fig. 35 High-risk Counts under Different Thresholds", loc="left")
    ax.set_xlabel("Threshold Setting")
    ax.set_ylabel("Detected Count")
    ax.tick_params(axis="x", rotation=20)
    save(fig, "Fig35_threshold_sensitivity.png")
    ext_high = ext[ext["is_high_risk_low_price"] == 1]["统一服务类别"].map(lambda x: en(x, SERVICE)).value_counts().head(15).reset_index()
    ext_high.columns = ["Service", "Count"]
    bar(ext_high, "Count", "Service", "Fig. 36 Extension Sample High-risk Service Types", "Fig36_extension_high_risk_service_distribution.png", "High-risk Count", "Service Category", horizontal=True, color=ORANGE, sort=True)
    flow("Fig37_regulatory_closed_loop.png", "Fig. 37 Regulatory Closed-loop for Abnormally Low Bids", ["Data ingestion", "Automatic warning", "Manual review", "Contract performance tracking", "Feedback and model calibration"], horizontal=True)


if __name__ == "__main__":
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "figure.dpi": 180,
        "savefig.dpi": 420,
        "figure.facecolor": "white",
    })
    generate()
    generated = sorted(OUT_DIR.glob("*_en.png"))
    print(f"Generated {len(generated)} English PNG files in {OUT_DIR}")
