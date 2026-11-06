from __future__ import annotations

import json
import math
import re
import textwrap
import warnings
from collections import Counter
from pathlib import Path

import jieba
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import shap
import statsmodels.api as sm
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import FuncFormatter, PercentFormatter
from matplotlib_venn import venn3
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.svm import OneClassSVM
from wordcloud import WordCloud
from xgboost import XGBClassifier

try:
    import community as community_louvain
except Exception:  # noqa: BLE001
    community_louvain = None


warnings.filterwarnings("ignore")

RANDOM_STATE = 42
BASE_DIR = Path(r"C:\Users\22672\Desktop\统计建模原数据")
WORK_DIR = Path(r"C:\Users\22672\Desktop\统计建模代码")
OUTPUT_DIR = WORK_DIR / "输出结果"
TABLE_DIR = OUTPUT_DIR / "tables"
FIG_DIR = OUTPUT_DIR / "figures"
DATA_DIR = OUTPUT_DIR / "data"
MODEL_DIR = OUTPUT_DIR / "models"

FILES = {
    "全样本表": "政府采购项目风险分析_全样本表.csv",
    "价格有效样本表": "政府采购项目风险分析_价格有效样本表.csv",
    "服务类主样本表": "政府采购项目风险分析_服务类主样本表.csv",
    "2025Q1扩展样本表": "政府采购项目风险分析_2025Q1扩展样本表.csv",
    "主表_v2": "政府采购项目风险分析主表_v2.csv",
}

RULE_COLS = [
    "rule_policy_65",
    "rule_quantile_10",
    "rule_quantile_5",
    "rule_iqr",
    "rule_robust_z",
]

CHINESE_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\Deng.ttf",
]

PALETTE = [
    "#005F73",
    "#0A9396",
    "#94D2BD",
    "#EE9B00",
    "#CA6702",
    "#BB3E03",
    "#AE2012",
    "#9B2226",
]

RISK_CMAP = LinearSegmentedColormap.from_list(
    "academic_risk", ["#0A9396", "#E9D8A6", "#EE9B00", "#CA6702", "#AE2012"]
)

STOPWORDS = {
    "项目",
    "采购",
    "服务",
    "公告",
    "中标",
    "成交",
    "供应商",
    "采购人",
    "有限公司",
    "公司",
    "单位",
    "名称",
    "合同",
    "要求",
    "文件",
    "标段",
    "进行",
    "相关",
    "管理",
    "按照",
    "提供",
    "如下",
    "详见",
    "内容",
    "时间",
    "地点",
    "金额",
    "预算",
    "人民币",
    "万元",
    "附件",
    "代理",
    "机构",
    "方式",
    "期限",
    "标准",
    "信息",
    "采购包",
    "联系方式",
    "联系",
    "电话",
    "本项目",
    "中国",
    "政府",
    "工作",
}


def ensure_dirs() -> None:
    for path in [OUTPUT_DIR, TABLE_DIR, FIG_DIR, DATA_DIR, MODEL_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def configure_plotting() -> Path | None:
    font_path = next((Path(p) for p in CHINESE_FONT_CANDIDATES if Path(p).exists()), None)
    if font_path:
        matplotlib.font_manager.fontManager.addfont(str(font_path))
        font_name = matplotlib.font_manager.FontProperties(fname=str(font_path)).get_name()
        plt.rcParams["font.sans-serif"] = [font_name, "Microsoft YaHei", "SimHei", "Arial"]
    else:
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 160
    plt.rcParams["savefig.dpi"] = 360
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["xtick.labelsize"] = 9
    plt.rcParams["ytick.labelsize"] = 9
    plt.rcParams["legend.frameon"] = False
    sns.set_theme(style="whitegrid", font=plt.rcParams["font.sans-serif"][0])
    return font_path


def read_table(name: str) -> pd.DataFrame:
    path = BASE_DIR / FILES[name]
    frame = pd.read_csv(path, encoding="utf-8-sig")
    numeric_cols = [
        "预算金额",
        "中标金额",
        "中标/预算比例",
        "节约率",
        "price_ratio_clean",
        "saving_rate_clean",
        "log_budget",
        "log_bid",
        "rule_risk_score",
        "is_suspicious_low_price",
        "is_high_risk_low_price",
        "gdp",
        "population",
        "gdp_per_capita",
        "fiscal_revenue",
        "fiscal_expenditure",
        "fiscal_pressure",
        "average_wage",
        "tertiary_value_added",
        "tertiary_industry_share",
        "urban_population",
        "urbanization_rate",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in RULE_COLS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)
    return frame


def pct(x: float, digits: int = 2) -> str:
    if pd.isna(x):
        return ""
    return f"{x * 100:.{digits}f}%"


def save_table(frame: pd.DataFrame, name: str) -> Path:
    path = TABLE_DIR / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_data(frame: pd.DataFrame, name: str) -> Path:
    path = DATA_DIR / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_fig(fig: plt.Figure, name: str, pdf: bool = True) -> Path:
    png_path = FIG_DIR / f"{name}.png"
    fig.savefig(png_path, bbox_inches="tight", facecolor="white")
    if pdf:
        fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path


def short_label(value: object, max_len: int = 16) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def risk_level_from_score(score: pd.Series) -> pd.Series:
    return pd.cut(
        score,
        bins=[-0.1, 0, 1, 2, 5],
        labels=["正常", "低风险", "中风险", "高风险"],
    ).astype(str)


def add_recalculated_rules(frame: pd.DataFrame, group_col: str = "统一服务类别") -> pd.DataFrame:
    df = frame.copy()
    ratio = pd.to_numeric(df["price_ratio_clean"], errors="coerce")
    group = df[group_col].fillna("未识别")
    global_q10 = ratio.quantile(0.10)
    global_q05 = ratio.quantile(0.05)
    global_q1 = ratio.quantile(0.25)
    global_q3 = ratio.quantile(0.75)
    global_iqr_low = global_q1 - 1.5 * (global_q3 - global_q1)
    global_median = ratio.median()
    global_mad = np.nanmedian(np.abs(ratio - global_median))
    global_mad = global_mad if global_mad and not np.isnan(global_mad) else ratio.std()

    stats = df.assign(_ratio=ratio, _group=group).groupby("_group")["_ratio"]
    q10 = stats.transform(lambda x: x.quantile(0.10) if x.notna().sum() >= 10 else global_q10)
    q05 = stats.transform(lambda x: x.quantile(0.05) if x.notna().sum() >= 10 else global_q05)
    q1 = stats.transform(lambda x: x.quantile(0.25) if x.notna().sum() >= 10 else global_q1)
    q3 = stats.transform(lambda x: x.quantile(0.75) if x.notna().sum() >= 10 else global_q3)
    med = stats.transform(lambda x: x.median() if x.notna().sum() >= 10 else global_median)
    mad = stats.transform(
        lambda x: np.nanmedian(np.abs(x - x.median())) if x.notna().sum() >= 10 else global_mad
    )
    mad = mad.replace(0, global_mad).fillna(global_mad)
    iqr_low = (q1 - 1.5 * (q3 - q1)).fillna(global_iqr_low)
    robust_z = (ratio - med) / (1.4826 * mad)

    df["calc_rule_policy_65"] = (ratio < 0.65).fillna(False).astype(int)
    df["calc_rule_quantile_10"] = (ratio <= q10).fillna(False).astype(int)
    df["calc_rule_quantile_5"] = (ratio <= q05).fillna(False).astype(int)
    df["calc_rule_iqr"] = (ratio < iqr_low).fillna(False).astype(int)
    df["calc_rule_robust_z"] = (robust_z < -3.5).fillna(False).astype(int)
    calc_cols = [
        "calc_rule_policy_65",
        "calc_rule_quantile_10",
        "calc_rule_quantile_5",
        "calc_rule_iqr",
        "calc_rule_robust_z",
    ]
    df["calc_rule_risk_score"] = df[calc_cols].sum(axis=1)
    df["calc_rule_risk_level"] = risk_level_from_score(df["calc_rule_risk_score"])
    df["calc_is_suspicious_low_price"] = (df["calc_rule_risk_score"] >= 1).astype(int)
    df["calc_is_high_risk_low_price"] = (df["calc_rule_risk_score"] >= 3).astype(int)
    return df


def combine_text(frame: pd.DataFrame) -> pd.Series:
    cols = [col for col in ["公告标题", "项目名称", "公告正文", "统一服务类别", "采购方式标准化"] if col in frame.columns]
    text_parts = []
    for col in cols:
        s = frame[col].fillna("").astype(str)
        if col == "公告正文":
            s = s.str.slice(0, 9000)
        text_parts.append(s)
    return pd.concat(text_parts, axis=1).agg(" ".join, axis=1)


def tokenize_cn(text: str) -> str:
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", str(text))
    tokens = []
    for word in jieba.lcut(text):
        word = word.strip()
        if len(word) < 2:
            continue
        if word in STOPWORDS:
            continue
        if word.isdigit():
            continue
        if re.fullmatch(r"[A-Za-z0-9]+", word) and len(word) < 3:
            continue
        tokens.append(word)
    return " ".join(tokens)


def add_supplier_profile(frame: pd.DataFrame, high_risk_col: str = "is_high_risk_low_price") -> tuple[pd.DataFrame, pd.DataFrame]:
    df = frame.copy()
    supplier = df["统一供应商名称"].fillna("供应商缺失").astype(str).str.strip().replace("", "供应商缺失")
    df["_supplier"] = supplier
    cross = df.get("是否跨省中标", pd.Series(["否"] * len(df))).fillna("否").astype(str).str.contains("是|1|true|True", regex=True)
    df["_cross_province"] = cross.astype(int)
    g = df.groupby("_supplier", dropna=False)
    supplier_profile = g.agg(
        supplier_win_count=("记录ID", "count"),
        supplier_low_price_count=(high_risk_col, "sum"),
        supplier_suspicious_count=("is_suspicious_low_price", "sum"),
        supplier_avg_saving_rate=("saving_rate_clean", "mean"),
        supplier_avg_price_ratio=("price_ratio_clean", "mean"),
        supplier_cross_province_rate=("_cross_province", "mean"),
        supplier_category_count=("统一服务类别", "nunique"),
        supplier_province_count=("项目省份", "nunique"),
    ).reset_index().rename(columns={"_supplier": "统一供应商名称"})
    supplier_profile["supplier_low_price_rate"] = (
        supplier_profile["supplier_low_price_count"] / supplier_profile["supplier_win_count"]
    )
    supplier_profile["supplier_risk_score"] = (
        0.40 * MinMaxScaler().fit_transform(supplier_profile[["supplier_low_price_rate"]]).ravel()
        + 0.25 * MinMaxScaler().fit_transform(supplier_profile[["supplier_low_price_count"]]).ravel()
        + 0.20 * MinMaxScaler().fit_transform(supplier_profile[["supplier_win_count"]]).ravel()
        + 0.15 * MinMaxScaler().fit_transform(supplier_profile[["supplier_cross_province_rate"]]).ravel()
    )
    df = df.merge(supplier_profile, on="统一供应商名称", how="left")
    for col in [
        "supplier_win_count",
        "supplier_low_price_count",
        "supplier_suspicious_count",
        "supplier_avg_saving_rate",
        "supplier_avg_price_ratio",
        "supplier_cross_province_rate",
        "supplier_category_count",
        "supplier_province_count",
        "supplier_low_price_rate",
        "supplier_risk_score",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.drop(columns=["_supplier", "_cross_province"]), supplier_profile


def draw_flow_diagram(
    name: str,
    title: str,
    steps: list[str],
    side_notes: list[str] | None = None,
    horizontal: bool = False,
) -> Path:
    if horizontal:
        fig, ax = plt.subplots(figsize=(13.5, 3.4))
        xs = np.linspace(0.08, 0.92, len(steps))
        y = 0.52
        for i, (x, text) in enumerate(zip(xs, steps)):
            box = patches.FancyBboxPatch(
                (x - 0.075, y - 0.15),
                0.15,
                0.30,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=1.6,
                edgecolor=PALETTE[i % len(PALETTE)],
                facecolor="#FFFFFF",
            )
            ax.add_patch(box)
            ax.text(x, y, textwrap.fill(text, 12), ha="center", va="center", fontsize=10, weight="bold")
            if i < len(steps) - 1:
                ax.annotate(
                    "",
                    xy=(xs[i + 1] - 0.09, y),
                    xytext=(x + 0.09, y),
                    arrowprops=dict(arrowstyle="->", lw=1.6, color="#495057"),
                )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        fig, ax = plt.subplots(figsize=(7.2, 9.2))
        ys = np.linspace(0.88, 0.12, len(steps))
        for i, (y, text) in enumerate(zip(ys, steps)):
            box = patches.FancyBboxPatch(
                (0.18, y - 0.055),
                0.64,
                0.11,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=1.6,
                edgecolor=PALETTE[i % len(PALETTE)],
                facecolor="#FFFFFF",
            )
            ax.add_patch(box)
            ax.text(0.50, y, textwrap.fill(text, 20), ha="center", va="center", fontsize=10.5, weight="bold")
            if i < len(steps) - 1:
                ax.annotate(
                    "",
                    xy=(0.50, ys[i + 1] + 0.075),
                    xytext=(0.50, y - 0.075),
                    arrowprops=dict(arrowstyle="->", lw=1.6, color="#495057"),
                )
        if side_notes:
            for y, note in zip(ys, side_notes):
                ax.text(0.86, y, textwrap.fill(note, 16), ha="left", va="center", fontsize=8.8, color="#495057")
        ax.set_xlim(0, 1.18)
        ax.set_ylim(0, 1)
    ax.set_title(title, loc="left", pad=12)
    ax.axis("off")
    return save_fig(fig, name)


def bar_with_labels(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    name: str,
    horizontal: bool = False,
    color: str = "#0A9396",
    percent_axis: bool = False,
    value_fmt: str = "{:.0f}",
) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    if horizontal:
        plot_data = data.sort_values(x, ascending=True)
        sns.barplot(data=plot_data, x=x, y=y, ax=ax, color=color, edgecolor="#263238", linewidth=0.3)
        for p in ax.patches:
            width = p.get_width()
            label = f"{width:.1%}" if percent_axis else value_fmt.format(width)
            ax.text(width + (ax.get_xlim()[1] * 0.01), p.get_y() + p.get_height() / 2, label, va="center", fontsize=8)
        if percent_axis:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    else:
        sns.barplot(data=data, x=x, y=y, ax=ax, color=color, edgecolor="#263238", linewidth=0.3)
        for p in ax.patches:
            height = p.get_height()
            label = f"{height:.1%}" if percent_axis else value_fmt.format(height)
            ax.text(p.get_x() + p.get_width() / 2, height, label, ha="center", va="bottom", fontsize=8)
        if percent_axis:
            ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.tick_params(axis="x", rotation=30)
    ax.set_title(title, loc="left")
    ax.grid(axis="y" if not horizontal else "x", alpha=0.25)
    sns.despine(ax=ax)
    return save_fig(fig, name)


def make_distribution_tables(full: pd.DataFrame, price: pd.DataFrame, service: pd.DataFrame, extend: pd.DataFrame, v2: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data_source = pd.DataFrame(
        [
            ["全样本表", len(full), full.shape[1], "总体描述、数据结构、采购大类分布", FILES["全样本表"]],
            ["价格有效样本表", len(price), price.shape[1], "异常低价规则标签构造", FILES["价格有效样本表"]],
            ["服务类主样本表", len(service), service.shape[1], "主模型、风险解释、SHAP、QCA、关系网络", FILES["服务类主样本表"]],
            ["2025Q1扩展样本表", len(extend), extend.shape[1], "稳健性检验与扩展分析", FILES["2025Q1扩展样本表"]],
            ["主表_v2", len(v2), v2.shape[1], "总备份主表与清洗记录", FILES["主表_v2"]],
        ],
        columns=["数据集", "样本量", "字段数", "正式用途", "文件名"],
    )

    field_structure = pd.DataFrame(
        [
            ["公告文本字段", "公告标题、项目名称、公告正文", "文本特征、关键词、LDA主题"],
            ["价格字段", "预算金额、中标金额、中标/预算比例、节约率、log_budget、log_bid", "价格规则与异常检测"],
            ["采购主体字段", "采购人名称、代理机构名称、统一供应商名称", "供应商画像与关系网络"],
            ["类型字段", "采购方式标准化、采购大类、统一服务类别", "分组比较与类别控制"],
            ["地区字段", "项目省份、项目城市、是否跨省中标", "地区差异与跨省交易特征"],
            ["宏观字段", "gdp、财政压力、平均工资、第三产业占比、城镇化率", "地区控制变量"],
            ["规则风险字段", "rule_policy_65、rule_quantile_10、rule_iqr、rule_robust_z、rule_risk_score", "异常低价标签构造"],
        ],
        columns=["字段类型", "代表字段", "建模用途"],
    )

    sample_split = pd.DataFrame(
        [
            ["全样本表", len(full), full["valid_price_sample"].mean(), full["is_high_risk_low_price"].mean(), "总体描述"],
            ["价格有效样本表", len(price), price["valid_price_sample"].mean(), price["is_high_risk_low_price"].mean(), "规则风险识别"],
            ["服务类主样本表", len(service), service["valid_price_sample"].mean(), service["is_high_risk_low_price"].mean(), "主模型分析"],
            ["2025Q1扩展样本表", len(extend), extend["valid_price_sample"].mean(), extend["is_high_risk_low_price"].mean(), "稳健性检验"],
        ],
        columns=["输出数据", "样本量", "价格有效比例", "规则高风险比例", "用途"],
    )
    sample_split["价格有效比例"] = sample_split["价格有效比例"].map(lambda x: pct(x))
    sample_split["规则高风险比例"] = sample_split["规则高风险比例"].map(lambda x: pct(x))

    category_distribution = (
        full.groupby("采购大类", dropna=False)
        .size()
        .reset_index(name="项目数量")
        .sort_values("项目数量", ascending=False)
    )
    category_distribution["占比"] = category_distribution["项目数量"] / len(full)
    category_distribution["占比"] = category_distribution["占比"].map(lambda x: pct(x))

    return {
        "Table01_data_sources": data_source,
        "Table02_field_structure": field_structure,
        "Table03_sample_split": sample_split,
        "Table04_procurement_category_distribution": category_distribution,
    }


def make_rule_tables(price: pd.DataFrame, service: pd.DataFrame) -> dict[str, pd.DataFrame]:
    indicator_desc = pd.DataFrame(
        [
            ["中标/预算比例", "中标金额 / 预算金额", "衡量报价相对预算水平"],
            ["节约率", "1 - 中标金额 / 预算金额", "衡量预算节约程度"],
            ["对数预算金额", "log(预算金额)", "缓解金额右偏分布"],
            ["对数中标金额", "log(中标金额)", "缓解金额右偏分布"],
            ["政策参考阈值法", "price_ratio_clean < 0.65", "识别显著低于预算的项目"],
            ["分位数法", "低于同服务类别10%或5%分位数", "识别类别内相对低价"],
            ["IQR法", "低于Q1 - 1.5 × IQR", "箱线图离群标准"],
            ["稳健Z分数法", "robust_z < -3.5", "基于中位数与MAD识别异常偏低"],
            ["综合风险等级", "规则得分0/1/2/≥3对应正常/低/中/高风险", "多规则投票标签"],
        ],
        columns=["指标", "计算口径", "解释"],
    )
    rule_names = {
        "rule_policy_65": "政策阈值<0.65",
        "rule_quantile_10": "同类别10%分位",
        "rule_quantile_5": "同类别5%分位",
        "rule_iqr": "IQR离群",
        "rule_robust_z": "稳健Z分数",
    }
    rule_compare = pd.DataFrame(
        [
            [rule_names[col], int(price[col].sum()), price[col].mean()]
            for col in RULE_COLS
        ],
        columns=["规则类型", "识别异常项目数量", "识别比例"],
    )
    rule_compare["识别比例"] = rule_compare["识别比例"].map(lambda x: pct(x))
    rule_compare["口径说明"] = [
        "中标/预算比例低于0.65",
        "低于同服务类别第10百分位",
        "低于同服务类别第5百分位",
        "低于同服务类别箱线图下界",
        "稳健Z分数显著为负",
    ]

    service_risk = (
        service.groupby("统一服务类别", dropna=False)
        .agg(
            项目数量=("记录ID", "count"),
            规则可疑数量=("is_suspicious_low_price", "sum"),
            规则高风险数量=("is_high_risk_low_price", "sum"),
            中标预算比例中位数=("price_ratio_clean", "median"),
            平均节约率=("saving_rate_clean", "mean"),
        )
        .reset_index()
    )
    service_risk["可疑比例"] = service_risk["规则可疑数量"] / service_risk["项目数量"]
    service_risk["高风险比例"] = service_risk["规则高风险数量"] / service_risk["项目数量"]
    service_risk = service_risk.sort_values(["高风险比例", "项目数量"], ascending=[False, False])

    method_risk = (
        price.groupby("采购方式标准化", dropna=False)
        .agg(项目数量=("记录ID", "count"), 高风险数量=("is_high_risk_low_price", "sum"))
        .reset_index()
    )
    method_risk["高风险比例"] = method_risk["高风险数量"] / method_risk["项目数量"]
    method_risk = method_risk.sort_values(["高风险比例", "项目数量"], ascending=[False, False])

    province_risk = (
        price.groupby("项目省份", dropna=False)
        .agg(项目数量=("记录ID", "count"), 高风险数量=("is_high_risk_low_price", "sum"))
        .reset_index()
    )
    province_risk["高风险比例"] = province_risk["高风险数量"] / province_risk["项目数量"]
    province_risk = province_risk.sort_values(["高风险比例", "项目数量"], ascending=[False, False])

    return {
        "Table05_low_price_indicator_definitions": indicator_desc,
        "Table06_rule_detection_comparison": rule_compare,
        "Table07_service_category_risk_rate": service_risk,
        "Table07b_procurement_method_risk_rate": method_risk,
        "Table07c_province_risk_rate": province_risk,
    }


def text_and_topic_model(service: pd.DataFrame, full: pd.DataFrame, font_path: Path | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    service = service.copy()
    full = full.copy()
    service["text_all"] = combine_text(service)
    full["text_all"] = combine_text(full)
    service["text_length"] = service["text_all"].str.len()
    full["text_length"] = full["text_all"].str.len()

    token_cache = DATA_DIR / "service_tokenized_text.csv"
    if token_cache.exists():
        cached = pd.read_csv(token_cache, encoding="utf-8-sig")
        service["tokenized_text"] = cached["tokenized_text"].fillna("")
    else:
        service["tokenized_text"] = service["text_all"].map(tokenize_cn)
        service[["记录ID", "tokenized_text"]].to_csv(token_cache, index=False, encoding="utf-8-sig")

    # 高频词统计
    all_tokens = " ".join(service["tokenized_text"].fillna("")).split()
    high_tokens = " ".join(service.loc[service["is_high_risk_low_price"] == 1, "tokenized_text"].fillna("")).split()
    normal_tokens = " ".join(service.loc[service["is_high_risk_low_price"] == 0, "tokenized_text"].fillna("")).split()
    keyword_table = pd.DataFrame(Counter(all_tokens).most_common(80), columns=["关键词", "词频"])
    high_keyword_table = pd.DataFrame(Counter(high_tokens).most_common(80), columns=["关键词", "高风险词频"])
    normal_keyword_table = pd.DataFrame(Counter(normal_tokens).most_common(80), columns=["关键词", "正常项目词频"])

    # TF-IDF与LDA
    tfidf_vectorizer = TfidfVectorizer(max_features=600, min_df=3, max_df=0.88)
    tfidf_matrix = tfidf_vectorizer.fit_transform(service["tokenized_text"].fillna(""))
    svd_n = min(24, max(2, tfidf_matrix.shape[1] - 1))
    svd = TruncatedSVD(n_components=svd_n, random_state=RANDOM_STATE)
    tfidf_svd = svd.fit_transform(tfidf_matrix)
    for i in range(tfidf_svd.shape[1]):
        service[f"tfidf_pc{i+1}"] = tfidf_svd[:, i]

    count_vectorizer = CountVectorizer(max_features=1000, min_df=3, max_df=0.88)
    count_matrix = count_vectorizer.fit_transform(service["tokenized_text"].fillna(""))
    n_topics = 6
    from sklearn.decomposition import LatentDirichletAllocation

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        learning_method="batch",
        max_iter=25,
        random_state=RANDOM_STATE,
        evaluate_every=-1,
    )
    topic_dist = lda.fit_transform(count_matrix)
    topic_cols = [f"lda_topic_prob_{i+1}" for i in range(n_topics)]
    service[topic_cols] = topic_dist
    service["lda_topic"] = topic_dist.argmax(axis=1) + 1
    feature_names = np.array(count_vectorizer.get_feature_names_out())
    topic_rows = []
    for topic_idx, weights in enumerate(lda.components_, start=1):
        top_idx = weights.argsort()[::-1][:10]
        top_words = feature_names[top_idx].tolist()
        topic_rows.append(
            {
                "主题编号": topic_idx,
                "主题关键词Top10": "、".join(top_words),
                "主题命名建议": f"主题{topic_idx}：" + " / ".join(top_words[:3]),
                "项目数量": int((service["lda_topic"] == topic_idx).sum()),
                "规则高风险比例": service.loc[service["lda_topic"] == topic_idx, "is_high_risk_low_price"].mean(),
            }
        )
    lda_topics = pd.DataFrame(topic_rows)

    text_rules = pd.DataFrame(
        [
            ["文本合并", "公告标题 + 项目名称 + 公告正文 + 服务类别 + 采购方式", "形成text_all"],
            ["字符清洗", "保留中文、英文和数字，去除特殊符号", "减少噪声"],
            ["中文分词", "jieba精确模式", "形成词项序列"],
            ["停用词处理", "删除采购公告通用词和低信息词", "提高主题辨识度"],
            ["TF-IDF", "max_features=600, min_df=3, max_df=0.88", "用于异常检测文本主成分"],
            ["LDA主题", "6个主题，CountVectorizer词袋输入", "用于项目画像与风险率比较"],
        ],
        columns=["处理环节", "具体规则", "输出"],
    )

    # Word clouds
    if font_path:
        for tokens, title, fname in [
            (all_tokens, "服务类政府采购公告总体关键词", "Fig11_overall_keyword_wordcloud"),
            (high_tokens, "异常低价高风险项目关键词", "Fig12_high_risk_keyword_wordcloud"),
            (normal_tokens, "正常项目关键词", "Fig12b_normal_keyword_wordcloud"),
        ]:
            freq = Counter(tokens)
            wc = WordCloud(
                font_path=str(font_path),
                width=1800,
                height=1100,
                background_color="white",
                colormap="turbo",
                max_words=180,
                prefer_horizontal=0.92,
                random_state=RANDOM_STATE,
            ).generate_from_frequencies(freq)
            fig, ax = plt.subplots(figsize=(10.8, 6.6))
            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(title, loc="left")
            ax.axis("off")
            save_fig(fig, fname)

    return service, keyword_table, pd.merge(high_keyword_table, normal_keyword_table, on="关键词", how="outer").fillna(0), lda_topics, text_rules


def make_basic_figures(full: pd.DataFrame, price: pd.DataFrame, service: pd.DataFrame) -> None:
    draw_flow_diagram(
        "Fig01_research_technical_route",
        "图1 研究技术路线图",
        [
            "数据来源：政府采购公告、2025Q1扩展样本、省级宏观指标",
            "数据清洗与主表构建：字段统一、价格处理、类别映射、省份标准化",
            "异常低价风险指标构建：固定阈值、分位数、IQR、稳健Z、多规则投票",
            "异常检测与风险解释：IForest、LOF、OCSVM、XGBoost、SHAP、QCA",
            "采购关系网络与监管建议：供应商—采购人网络、社群发现、预警闭环",
        ],
        side_notes=["多源融合", "四张正式分析表", "规则风险标签", "模型识别与解释", "政策建议"],
    )
    draw_flow_diagram(
        "Fig02_data_cleaning_flow",
        "图2 数据清洗流程图",
        ["原始采购数据", "字段统一", "价格异常处理", "服务类别统一", "省份标准化", "宏观变量合并", "四类建模样本"],
        horizontal=True,
    )

    category = full["采购大类"].fillna("未识别").value_counts().reset_index()
    category.columns = ["采购大类", "项目数量"]
    bar_with_labels(category, "采购大类", "项目数量", "图3 采购大类分布", "Fig03_procurement_category_distribution", color="#005F73")

    service_dist = (
        full["统一服务类别"].fillna("未识别").value_counts().head(15).reset_index()
    )
    service_dist.columns = ["统一服务类别", "项目数量"]
    service_dist["统一服务类别"] = service_dist["统一服务类别"].map(lambda x: short_label(x, 18))
    bar_with_labels(
        service_dist,
        "项目数量",
        "统一服务类别",
        "图4 统一服务类别分布（Top 15）",
        "Fig04_service_category_distribution",
        horizontal=True,
        color="#0A9396",
    )

    prov = full["项目省份"].fillna("未识别").value_counts().head(15).reset_index()
    prov.columns = ["项目省份", "项目数量"]
    bar_with_labels(
        prov,
        "项目省份",
        "项目数量",
        "图5 项目省份分布（Top 15）",
        "Fig05_province_distribution_top15",
        color="#EE9B00",
    )

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    sns.histplot(price["price_ratio_clean"].dropna().clip(0, 1.5), bins=45, kde=True, ax=ax, color="#0A9396")
    ax.axvline(0.65, color="#AE2012", lw=1.8, linestyle="--", label="政策参考阈值 0.65")
    ax.set_title("图6 中标/预算比例分布", loc="left")
    ax.set_xlabel("中标/预算比例")
    ax.set_ylabel("项目数量")
    ax.legend()
    sns.despine(ax=ax)
    save_fig(fig, "Fig06_price_ratio_histogram")

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    sns.histplot(price["saving_rate_clean"].dropna().clip(-0.2, 1), bins=45, kde=True, ax=ax, color="#CA6702")
    ax.axvline(0.35, color="#AE2012", lw=1.8, linestyle="--", label="节约率35%参考线")
    ax.set_title("图7 节约率分布", loc="left")
    ax.set_xlabel("节约率")
    ax.set_ylabel("项目数量")
    ax.legend()
    sns.despine(ax=ax)
    save_fig(fig, "Fig07_saving_rate_histogram")

    top_categories = service["统一服务类别"].value_counts().head(12).index
    box_data = service[service["统一服务类别"].isin(top_categories)].copy()
    box_data["统一服务类别短名"] = box_data["统一服务类别"].map(lambda x: short_label(x, 14))
    fig, ax = plt.subplots(figsize=(12, 6.4))
    sns.boxplot(
        data=box_data,
        x="统一服务类别短名",
        y="price_ratio_clean",
        ax=ax,
        palette=PALETTE,
        showfliers=True,
        fliersize=2.5,
        linewidth=0.8,
    )
    ax.axhline(0.65, color="#AE2012", linestyle="--", lw=1.4)
    ax.set_title("图8 不同服务类别的中标/预算比例箱线图", loc="left")
    ax.set_xlabel("统一服务类别")
    ax.set_ylabel("中标/预算比例")
    ax.tick_params(axis="x", rotation=35)
    sns.despine(ax=ax)
    save_fig(fig, "Fig08_service_price_ratio_boxplot")

    rule_counts = pd.DataFrame(
        {
            "规则": ["政策阈值<0.65", "同类别10%分位", "同类别5%分位", "IQR离群", "稳健Z分数"],
            "异常项目数量": [int(price[col].sum()) for col in RULE_COLS],
        }
    )
    bar_with_labels(rule_counts, "规则", "异常项目数量", "图9 四种规则识别异常数量对比", "Fig09_rule_detection_counts", color="#BB3E03")

    level_order = ["正常", "低风险", "中风险", "高风险"]
    level = price["rule_risk_level"].value_counts().reindex(level_order, fill_value=0).reset_index()
    level.columns = ["综合风险等级", "项目数量"]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    colors = ["#94D2BD", "#E9D8A6", "#EE9B00", "#AE2012"]
    sns.barplot(data=level, x="综合风险等级", y="项目数量", palette=colors, ax=ax, edgecolor="#263238", linewidth=0.3)
    for p in ax.patches:
        ax.text(p.get_x() + p.get_width() / 2, p.get_height(), f"{p.get_height():.0f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("图10 综合风险等级分布", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("项目数量")
    sns.despine(ax=ax)
    save_fig(fig, "Fig10_rule_risk_level_distribution")


def make_topic_figures(service: pd.DataFrame, lda_topics: pd.DataFrame, keyword_table: pd.DataFrame) -> None:
    # LDA关键词条形图
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6))
    axes = axes.ravel()
    for ax, (_, row) in zip(axes, lda_topics.iterrows()):
        words = row["主题关键词Top10"].split("、")
        vals = list(range(len(words), 0, -1))
        sns.barplot(x=vals, y=words, ax=ax, color=PALETTE[(int(row["主题编号"]) - 1) % len(PALETTE)])
        ax.set_title(f"主题{int(row['主题编号'])}", loc="left")
        ax.set_xlabel("相对权重排序")
        ax.set_ylabel("")
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("图13 LDA主题关键词条形图", x=0.02, y=1.02, ha="left", fontsize=14, weight="bold")
    fig.tight_layout()
    save_fig(fig, "Fig13_lda_topic_keywords")

    topic_rate = lda_topics.copy()
    topic_rate["主题"] = topic_rate["主题编号"].map(lambda x: f"主题{x}")
    bar_with_labels(
        topic_rate,
        "主题",
        "规则高风险比例",
        "图14 不同主题下异常低价风险率",
        "Fig14_topic_high_risk_rate",
        color="#CA6702",
        percent_axis=True,
    )

    supplier_counts = service.groupby("统一供应商名称", dropna=False).size()
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    max_bin = min(int(supplier_counts.max()), 20)
    clipped = supplier_counts.clip(upper=max_bin)
    sns.histplot(clipped, discrete=True, shrink=0.8, ax=ax, color="#005F73")
    ax.set_title("图15 供应商中标次数分布", loc="left")
    ax.set_xlabel(f"供应商中标次数（>{max_bin}次并入最高档）")
    ax.set_ylabel("供应商数量")
    sns.despine(ax=ax)
    save_fig(fig, "Fig15_supplier_win_count_distribution")


def anomaly_detection(service: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = service.copy()
    if "text_length" not in df:
        df["text_all"] = combine_text(df)
        df["text_length"] = df["text_all"].str.len()
    if "tokenized_text" not in df:
        df["tokenized_text"] = df["text_all"].map(tokenize_cn)

    numeric_cols = [
        "price_ratio_clean",
        "saving_rate_clean",
        "log_budget",
        "log_bid",
        "text_length",
        "supplier_win_count",
        "supplier_low_price_count",
        "supplier_low_price_rate",
        "supplier_cross_province_rate",
        "supplier_category_count",
        "supplier_risk_score",
        "gdp_per_capita",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
        "urbanization_rate",
    ]
    topic_cols = [col for col in df.columns if col.startswith("lda_topic_prob_")]
    tfidf_cols = [col for col in df.columns if col.startswith("tfidf_pc")]
    numeric_cols = [col for col in [*numeric_cols, *topic_cols, *tfidf_cols[:20]] if col in df.columns]
    cat_cols = [col for col in ["采购方式标准化", "统一服务类别", "项目省份", "是否跨省中标", "lda_topic"] if col in df.columns]

    X = df[numeric_cols + cat_cols].copy()
    for col in cat_cols:
        X[col] = X[col].fillna("未识别").astype(str)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_cols),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True, min_frequency=10))]), cat_cols),
        ],
        remainder="drop",
    )
    X_proc = preprocessor.fit_transform(X)
    X_model = X_proc.toarray() if sparse.issparse(X_proc) else X_proc
    contamination = float(np.clip(max(df["is_high_risk_low_price"].mean(), 0.08), 0.06, 0.12))

    iforest = IsolationForest(
        n_estimators=400,
        contamination=contamination,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_samples="auto",
    )
    iforest_pred = iforest.fit_predict(X_model)
    iforest_raw = -iforest.decision_function(X_model)

    lof = LocalOutlierFactor(n_neighbors=35, contamination=contamination, metric="minkowski", n_jobs=-1)
    lof_pred = lof.fit_predict(X_model)
    lof_raw = -lof.negative_outlier_factor_

    ocsvm = OneClassSVM(nu=contamination, kernel="rbf", gamma="scale")
    ocsvm_pred = ocsvm.fit_predict(X_model)
    ocsvm_raw = -ocsvm.decision_function(X_model)

    score_frame = pd.DataFrame(
        {
            "iforest_score": iforest_raw,
            "lof_score": lof_raw,
            "ocsvm_score": ocsvm_raw,
        }
    )
    scaler = MinMaxScaler()
    score_scaled = pd.DataFrame(scaler.fit_transform(score_frame), columns=score_frame.columns)
    rule_scaled = df["rule_risk_score"].fillna(0) / max(float(df["rule_risk_score"].max()), 1.0)
    ensemble = (
        0.30 * score_scaled["iforest_score"]
        + 0.25 * score_scaled["lof_score"]
        + 0.20 * score_scaled["ocsvm_score"]
        + 0.25 * rule_scaled
    )
    df["iforest_score"] = score_scaled["iforest_score"]
    df["lof_score"] = score_scaled["lof_score"]
    df["ocsvm_score"] = score_scaled["ocsvm_score"]
    df["iforest_anomaly"] = (iforest_pred == -1).astype(int)
    df["lof_anomaly"] = (lof_pred == -1).astype(int)
    df["ocsvm_anomaly"] = (ocsvm_pred == -1).astype(int)
    df["anomaly_model_vote"] = df[["iforest_anomaly", "lof_anomaly", "ocsvm_anomaly"]].sum(axis=1)
    df["ensemble_risk_score"] = ensemble
    q50, q75, q90 = df["ensemble_risk_score"].quantile([0.50, 0.75, 0.90]).tolist()
    df["model_risk_level"] = pd.cut(
        df["ensemble_risk_score"],
        bins=[-np.inf, q50, q75, q90, np.inf],
        labels=["正常", "低风险", "中风险", "高风险"],
    ).astype(str)
    df["final_high_risk"] = (df["ensemble_risk_score"] >= q90).astype(int)
    df["final_suspicious_risk"] = (df["ensemble_risk_score"] >= q75).astype(int)

    model_params = pd.DataFrame(
        [
            ["Isolation Forest", f"n_estimators=400; contamination={contamination:.3f}; random_state=42", "全局孤立异常识别"],
            ["LOF", f"n_neighbors=35; contamination={contamination:.3f}", "局部密度异常识别"],
            ["One-Class SVM", f"nu={contamination:.3f}; kernel=RBF; gamma=scale", "非线性边界稳健性识别"],
            ["集成风险分数", "0.30×IForest + 0.25×LOF + 0.20×OCSVM + 0.25×规则得分", "综合多源异常信号"],
            ["最终高风险阈值", "ensemble_risk_score ≥ 第90百分位", "主模型高风险标签"],
        ],
        columns=["模型", "参数设置", "作用"],
    )
    model_results = pd.DataFrame(
        [
            ["Isolation Forest", int(df["iforest_anomaly"].sum()), df["iforest_anomaly"].mean()],
            ["LOF", int(df["lof_anomaly"].sum()), df["lof_anomaly"].mean()],
            ["One-Class SVM", int(df["ocsvm_anomaly"].sum()), df["ocsvm_anomaly"].mean()],
            ["规则高风险", int(df["is_high_risk_low_price"].sum()), df["is_high_risk_low_price"].mean()],
            ["集成模型高风险", int(df["final_high_risk"].sum()), df["final_high_risk"].mean()],
        ],
        columns=["识别方式", "高风险/异常项目数量", "占比"],
    )
    model_results["占比"] = model_results["占比"].map(lambda x: pct(x))
    return df, model_params, model_results


def make_anomaly_figures(service: pd.DataFrame, model_results: pd.DataFrame) -> None:
    draw_flow_diagram(
        "Fig16_anomaly_detection_flow",
        "图16 异常检测模型流程图",
        ["输入特征", "标准化与编码", "Isolation Forest / LOF / One-Class SVM", "分数标准化", "集成风险得分", "高风险项目识别"],
        horizontal=True,
    )
    counts = model_results.copy()
    counts["数量"] = pd.to_numeric(counts["高风险/异常项目数量"])
    bar_with_labels(
        counts,
        "识别方式",
        "数量",
        "图17 不同模型识别异常项目数量对比",
        "Fig17_anomaly_model_counts",
        color="#005F73",
    )

    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    set_if = set(service.index[service["iforest_anomaly"] == 1])
    set_lof = set(service.index[service["lof_anomaly"] == 1])
    set_svm = set(service.index[service["ocsvm_anomaly"] == 1])
    venn = venn3([set_if, set_lof, set_svm], ("Isolation Forest", "LOF", "One-Class SVM"), ax=ax)
    for patch, color in zip([venn.get_patch_by_id(x) for x in ["100", "010", "001", "110", "101", "011", "111"]], PALETTE):
        if patch:
            patch.set_alpha(0.58)
            patch.set_color(color)
    ax.set_title("图18 异常检测模型结果重叠韦恩图", loc="left")
    save_fig(fig, "Fig18_anomaly_model_venn")

    high = service[service["final_high_risk"] == 1]
    high_cat = high["统一服务类别"].fillna("未识别").value_counts().head(15).reset_index()
    high_cat.columns = ["统一服务类别", "高风险项目数量"]
    high_cat["统一服务类别"] = high_cat["统一服务类别"].map(lambda x: short_label(x, 18))
    bar_with_labels(
        high_cat,
        "高风险项目数量",
        "统一服务类别",
        "图19 高风险项目服务类别分布",
        "Fig19_high_risk_service_category",
        horizontal=True,
        color="#AE2012",
    )

    high_prov = high["项目省份"].fillna("未识别").value_counts().head(15).reset_index()
    high_prov.columns = ["项目省份", "高风险项目数量"]
    bar_with_labels(
        high_prov,
        "项目省份",
        "高风险项目数量",
        "图20 高风险项目省份分布（Top 15）",
        "Fig20_high_risk_province",
        color="#CA6702",
    )

    feature_cols = [
        "price_ratio_clean",
        "saving_rate_clean",
        "log_budget",
        "text_length",
        "supplier_win_count",
        "supplier_low_price_rate",
        "supplier_cross_province_rate",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
        *[c for c in service.columns if c.startswith("tfidf_pc")][:12],
    ]
    feature_cols = [c for c in feature_cols if c in service.columns]
    X = service[feature_cols].copy()
    X = X.fillna(X.median(numeric_only=True))
    X_scaled = StandardScaler().fit_transform(X)
    svd = TruncatedSVD(n_components=2, random_state=RANDOM_STATE)
    coords = svd.fit_transform(X_scaled)
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    scatter = ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=service["ensemble_risk_score"],
        cmap=RISK_CMAP,
        s=np.where(service["final_high_risk"].eq(1), 26, 12),
        alpha=np.where(service["final_high_risk"].eq(1), 0.85, 0.36),
        edgecolors="none",
    )
    ax.set_title("图21 PCA二维异常项目散点图", loc="left")
    ax.set_xlabel("主成分1")
    ax.set_ylabel("主成分2")
    cbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("集成风险分数")
    sns.despine(ax=ax)
    save_fig(fig, "Fig21_pca_anomaly_scatter")


def high_risk_descriptives(service: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "price_ratio_clean",
        "saving_rate_clean",
        "预算金额",
        "中标金额",
        "log_budget",
        "text_length",
        "supplier_win_count",
        "supplier_low_price_rate",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
    ]
    rows = []
    for col in [c for c in cols if c in service.columns]:
        for flag, group in service.groupby("final_high_risk"):
            rows.append(
                {
                    "变量": col,
                    "风险组": "高风险" if flag == 1 else "非高风险",
                    "样本量": group[col].notna().sum(),
                    "均值": group[col].mean(),
                    "中位数": group[col].median(),
                    "标准差": group[col].std(),
                    "P25": group[col].quantile(0.25),
                    "P75": group[col].quantile(0.75),
                }
            )
    return pd.DataFrame(rows)


def clean_feature_name(name: str) -> str:
    name = re.sub(r"^(num|cat)__", "", name)
    name = name.replace("采购方式标准化_", "采购方式=")
    name = name.replace("统一服务类别_", "服务类别=")
    name = name.replace("项目省份_", "省份=")
    name = name.replace("是否跨省中标_", "跨省=")
    name = name.replace("lda_topic_", "LDA主题=")
    return short_label(name, 34)


def supervised_models(service: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, tuple[pd.DataFrame, np.ndarray]]:
    df = service.copy()
    target = "final_high_risk"
    topic_cols = [col for col in df.columns if col.startswith("lda_topic_prob_")]
    numeric_cols = [
        "price_ratio_clean",
        "saving_rate_clean",
        "log_budget",
        "log_bid",
        "text_length",
        "supplier_win_count",
        "supplier_low_price_count",
        "supplier_low_price_rate",
        "supplier_cross_province_rate",
        "supplier_category_count",
        "supplier_risk_score",
        "gdp_per_capita",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
        "urbanization_rate",
        *topic_cols,
    ]
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    cat_cols = [c for c in ["采购方式标准化", "统一服务类别", "项目省份", "是否跨省中标", "lda_topic"] if c in df.columns]
    X = df[numeric_cols + cat_cols].copy()
    for col in cat_cols:
        X[col] = X[col].fillna("未识别").astype(str)
    y = df[target].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_cols),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True, min_frequency=10))]), cat_cols),
        ],
        remainder="drop",
    )
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    feature_names = [clean_feature_name(n) for n in preprocessor.get_feature_names_out()]
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = max(1.0, neg / max(pos, 1))

    models = {
        "Logistic": LogisticRegression(max_iter=1200, class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=4,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=360,
            max_depth=3,
            learning_rate=0.045,
            subsample=0.86,
            colsample_bytree=0.86,
            reg_lambda=1.2,
            min_child_weight=2,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            scale_pos_weight=scale_pos_weight,
        ),
    }
    metrics = []
    importances = {}
    fitted_models = {}
    for name, model in models.items():
        model.fit(X_train_proc, y_train)
        fitted_models[name] = model
        pred = model.predict(X_test_proc)
        proba = model.predict_proba(X_test_proc)[:, 1]
        metrics.append(
            {
                "模型": name,
                "Accuracy": accuracy_score(y_test, pred),
                "Precision": precision_score(y_test, pred, zero_division=0),
                "Recall": recall_score(y_test, pred, zero_division=0),
                "F1": f1_score(y_test, pred, zero_division=0),
                "AUC": roc_auc_score(y_test, proba),
            }
        )
        if hasattr(model, "feature_importances_"):
            importances[name] = pd.DataFrame(
                {"变量": feature_names, "重要性": model.feature_importances_}
            ).sort_values("重要性", ascending=False)
        elif hasattr(model, "coef_"):
            importances[name] = pd.DataFrame(
                {"变量": feature_names, "系数": model.coef_[0], "绝对系数": np.abs(model.coef_[0])}
            ).sort_values("绝对系数", ascending=False)
    eval_table = pd.DataFrame(metrics)

    # Statsmodels logistic table on a compact, interpretable design matrix.
    logit_df = df.copy()
    logit_df["跨省中标"] = logit_df.get("是否跨省中标", "否").fillna("否").astype(str).str.contains("是|1|true|True", regex=True).astype(int)
    logit_df["公开招标"] = logit_df.get("采购方式标准化", "").fillna("").astype(str).str.contains("公开招标", regex=False).astype(int)
    high_risk_services = (
        logit_df.groupby("统一服务类别")["final_high_risk"].mean().sort_values(ascending=False).head(4).index.tolist()
    )
    for svc in high_risk_services:
        logit_df[f"服务类别={short_label(svc, 8)}"] = (logit_df["统一服务类别"] == svc).astype(int)
    logit_cols = [
        "saving_rate_clean",
        "log_budget",
        "text_length",
        "supplier_win_count",
        "supplier_low_price_rate",
        "supplier_cross_province_rate",
        "supplier_category_count",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
        "跨省中标",
        "公开招标",
        *[f"服务类别={short_label(svc, 8)}" for svc in high_risk_services],
    ]
    logit_cols = [c for c in logit_cols if c in logit_df.columns]
    compact = logit_df[[target, *logit_cols]].replace([np.inf, -np.inf], np.nan).dropna()
    for col in logit_cols:
        std = compact[col].std()
        if std and std > 0:
            compact[col] = (compact[col] - compact[col].mean()) / std
    X_logit = sm.add_constant(compact[logit_cols], has_constant="add")
    y_logit = compact[target].astype(int)
    try:
        logit_model = sm.Logit(y_logit, X_logit).fit(disp=False, maxiter=300)
        logistic_table = pd.DataFrame(
            {
                "变量": logit_model.params.index,
                "系数": logit_model.params.values,
                "标准误": logit_model.bse.values,
                "z值": logit_model.tvalues.values,
                "p值": logit_model.pvalues.values,
                "优势比OR": np.exp(logit_model.params.values),
            }
        )
    except Exception:
        reg_model = sm.Logit(y_logit, X_logit).fit_regularized(disp=False, maxiter=300)
        logistic_table = pd.DataFrame(
            {
                "变量": reg_model.params.index,
                "系数": reg_model.params.values,
                "标准误": np.nan,
                "z值": np.nan,
                "p值": np.nan,
                "优势比OR": np.exp(reg_model.params.values),
            }
        )

    # SHAP on XGBoost.
    xgb_model = fitted_models["XGBoost"]
    X_train_array = X_train_proc.toarray() if sparse.issparse(X_train_proc) else np.asarray(X_train_proc)
    sample_n = min(1400, X_train_array.shape[0])
    rng = np.random.default_rng(RANDOM_STATE)
    sample_idx = rng.choice(X_train_array.shape[0], sample_n, replace=False)
    X_shap = X_train_array[sample_idx]
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_shap)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_df = pd.DataFrame(shap_values, columns=feature_names)
    X_shap_df = pd.DataFrame(X_shap, columns=feature_names)
    shap_importance = (
        shap_df.abs().mean().reset_index().rename(columns={"index": "变量", 0: "mean_abs_SHAP"})
        .sort_values("mean_abs_SHAP", ascending=False)
    )

    return eval_table, logistic_table, importances["Random Forest"], importances["XGBoost"], shap_importance, (X_shap_df, shap_values)


def make_supervised_figures(
    eval_table: pd.DataFrame,
    rf_importance: pd.DataFrame,
    xgb_importance: pd.DataFrame,
    shap_importance: pd.DataFrame,
    shap_payload: tuple[pd.DataFrame, np.ndarray],
) -> None:
    eval_long = eval_table.melt(id_vars="模型", var_name="指标", value_name="得分")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    sns.barplot(data=eval_long, x="指标", y="得分", hue="模型", palette=PALETTE[:3], ax=ax)
    ax.set_title("图22 模型评价指标对比图", loc="left")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("")
    ax.set_ylabel("得分")
    sns.despine(ax=ax)
    save_fig(fig, "Fig22_supervised_model_metrics")

    for table, title, fname, color in [
        (rf_importance.head(15), "图23 Random Forest变量重要性图", "Fig23_random_forest_importance", "#005F73"),
        (xgb_importance.head(15), "图24 XGBoost变量重要性图", "Fig24_xgboost_importance", "#CA6702"),
    ]:
        plot_df = table.copy().rename(columns={"重要性": "importance"})
        plot_df["变量"] = plot_df["变量"].map(lambda x: short_label(x, 28))
        bar_with_labels(
            plot_df,
            "importance",
            "变量",
            title,
            fname,
            horizontal=True,
            color=color,
            value_fmt="{:.3f}",
        )

    X_shap_df, shap_values = shap_payload
    fig = plt.figure(figsize=(9.5, 7.2))
    shap.summary_plot(shap_values, X_shap_df, max_display=18, show=False, plot_size=None, color_bar=True)
    plt.title("图25 SHAP Summary Plot", loc="left", pad=12)
    save_fig(plt.gcf(), "Fig25_shap_summary")

    top_features = shap_importance["变量"].head(4).tolist()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.2))
    axes = axes.ravel()
    shap_df = pd.DataFrame(shap_values, columns=X_shap_df.columns)
    for ax, feature in zip(axes, top_features):
        x = X_shap_df[feature]
        y = shap_df[feature]
        ax.scatter(x, y, s=12, alpha=0.42, color="#0A9396", edgecolors="none")
        ax.axhline(0, color="#495057", lw=0.8, linestyle="--")
        if x.nunique() > 5:
            bins = pd.qcut(x.rank(method="first"), q=min(12, max(3, int(np.sqrt(len(x)) // 4))), duplicates="drop")
            trend = pd.DataFrame({"x": x, "y": y, "bin": bins}).groupby("bin", observed=False).agg(x=("x", "median"), y=("y", "median"))
            ax.plot(trend["x"], trend["y"], color="#AE2012", lw=1.8)
        ax.set_title(short_label(feature, 26), loc="left")
        ax.set_xlabel("标准化特征值")
        ax.set_ylabel("SHAP值")
    fig.suptitle("图26 SHAP Dependence Plot（Top 4变量）", x=0.02, y=1.02, ha="left", fontsize=14, weight="bold")
    fig.tight_layout()
    save_fig(fig, "Fig26_shap_dependence_top4")


def qca_analysis(service: pd.DataFrame) -> pd.DataFrame:
    df = service.copy()
    service_risk = df.groupby("统一服务类别")["final_high_risk"].mean()
    high_risk_service_set = set(service_risk[service_risk >= service_risk.mean()].index)
    df["高节约率"] = (df["saving_rate_clean"] >= df["saving_rate_clean"].quantile(0.75)).astype(int)
    df["低价格比例"] = (df["price_ratio_clean"] <= df["price_ratio_clean"].quantile(0.25)).astype(int)
    df["高频供应商"] = (df["supplier_win_count"] >= df["supplier_win_count"].quantile(0.75)).astype(int)
    df["跨省中标"] = df.get("是否跨省中标", "否").fillna("否").astype(str).str.contains("是|1|true|True", regex=True).astype(int)
    df["高财政压力"] = (df["fiscal_pressure"] >= df["fiscal_pressure"].median()).astype(int)
    df["公开招标"] = df.get("采购方式标准化", "").fillna("").astype(str).str.contains("公开招标", regex=False).astype(int)
    df["供应商信息缺失"] = df["统一供应商名称"].isna().astype(int)
    df["高风险服务类别"] = df["统一服务类别"].isin(high_risk_service_set).astype(int)

    conditions = ["高节约率", "低价格比例", "高频供应商", "跨省中标", "高财政压力", "公开招标", "供应商信息缺失", "高风险服务类别"]
    truth = (
        df.groupby(conditions)
        .agg(案例数=("记录ID", "count"), 高风险案例数=("final_high_risk", "sum"))
        .reset_index()
    )
    truth["一致性"] = truth["高风险案例数"] / truth["案例数"]
    total_high = df["final_high_risk"].sum()
    truth["覆盖度"] = truth["高风险案例数"] / max(total_high, 1)
    selected = truth[(truth["案例数"] >= 8) & (truth["一致性"] >= 0.45) & (truth["高风险案例数"] >= 4)].copy()
    if selected.empty:
        selected = truth.sort_values(["一致性", "高风险案例数"], ascending=False).head(8).copy()
    selected = selected.sort_values(["一致性", "覆盖度", "高风险案例数"], ascending=False).head(10)
    paths = []
    for i, row in selected.reset_index(drop=True).iterrows():
        present = [cond for cond in conditions if row[cond] == 1]
        absent = [f"非{cond}" for cond in conditions if row[cond] == 0 and cond in ["公开招标", "跨省中标"]]
        path_text = " × ".join([*present, *absent]) if present or absent else "无显著条件组合"
        paths.append(
            {
                "路径编号": f"路径{i+1}",
                "成因组合": path_text,
                "案例数": int(row["案例数"]),
                "高风险案例数": int(row["高风险案例数"]),
                "一致性": row["一致性"],
                "覆盖度": row["覆盖度"],
            }
        )
    qca_paths = pd.DataFrame(paths)

    fig, ax = plt.subplots(figsize=(12, max(4.8, 0.55 * len(qca_paths) + 2)))
    ax.axis("off")
    ax.set_title("图27 QCA成因路径图", loc="left", pad=12)
    y_positions = np.linspace(0.85, 0.15, len(qca_paths))
    for y, (_, row) in zip(y_positions, qca_paths.iterrows()):
        ax.text(0.02, y, row["路径编号"], va="center", ha="left", weight="bold", color="#005F73")
        conditions_text = [short_label(x, 9) for x in row["成因组合"].split(" × ")]
        x = 0.15
        for j, cond in enumerate(conditions_text[:6]):
            w = 0.09 + min(0.04, len(cond) * 0.004)
            box = patches.FancyBboxPatch(
                (x, y - 0.035),
                w,
                0.07,
                boxstyle="round,pad=0.01,rounding_size=0.01",
                edgecolor=PALETTE[j % len(PALETTE)],
                facecolor="#FFFFFF",
                linewidth=1.2,
            )
            ax.add_patch(box)
            ax.text(x + w / 2, y, cond, ha="center", va="center", fontsize=8.5)
            x += w + 0.018
        ax.annotate("", xy=(0.82, y), xytext=(min(x, 0.78), y), arrowprops=dict(arrowstyle="->", lw=1.3, color="#495057"))
        ax.text(0.84, y, f"高风险\n一致性 {row['一致性']:.2f}", va="center", ha="center", color="#AE2012", weight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save_fig(fig, "Fig27_qca_causal_paths")
    return qca_paths


def network_analysis(service: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = service.copy()
    suppliers = df["统一供应商名称"].fillna("供应商缺失").astype(str).str.strip()
    buyers = df["采购人名称"].fillna("采购人缺失").astype(str).str.strip()
    df["_supplier_node"] = "S|" + suppliers.replace("", "供应商缺失")
    df["_buyer_node"] = "B|" + buyers.replace("", "采购人缺失")

    edge_df = (
        df.groupby(["_supplier_node", "_buyer_node"])
        .agg(
            weight=("记录ID", "count"),
            risk_count=("final_high_risk", "sum"),
            avg_score=("ensemble_risk_score", "mean"),
            服务类别=("统一服务类别", lambda x: "、".join(x.dropna().astype(str).value_counts().head(3).index)),
        )
        .reset_index()
    )
    G = nx.Graph()
    for _, row in edge_df.iterrows():
        G.add_node(row["_supplier_node"], node_type="供应商")
        G.add_node(row["_buyer_node"], node_type="采购人")
        G.add_edge(
            row["_supplier_node"],
            row["_buyer_node"],
            weight=float(row["weight"]),
            risk_count=float(row["risk_count"]),
            avg_score=float(row["avg_score"]),
        )
    node_stats_supplier = (
        df.groupby("_supplier_node")
        .agg(
            项目数量=("记录ID", "count"),
            高风险项目数量=("final_high_risk", "sum"),
            平均风险分=("ensemble_risk_score", "mean"),
            主服务类别=("统一服务类别", lambda x: x.dropna().astype(str).value_counts().index[0] if len(x.dropna()) else ""),
        )
        .reset_index()
        .rename(columns={"_supplier_node": "node"})
    )
    node_stats_buyer = (
        df.groupby("_buyer_node")
        .agg(
            项目数量=("记录ID", "count"),
            高风险项目数量=("final_high_risk", "sum"),
            平均风险分=("ensemble_risk_score", "mean"),
            主服务类别=("统一服务类别", lambda x: x.dropna().astype(str).value_counts().index[0] if len(x.dropna()) else ""),
        )
        .reset_index()
        .rename(columns={"_buyer_node": "node"})
    )
    node_stats = pd.concat([node_stats_supplier, node_stats_buyer], ignore_index=True)
    node_stats["高风险比例"] = node_stats["高风险项目数量"] / node_stats["项目数量"]

    degree = dict(G.degree(weight="weight"))
    degree_cent = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, k=min(220, max(10, len(G) - 1)), seed=RANDOM_STATE) if len(G) > 2 else {}
    try:
        eigen = nx.eigenvector_centrality(G, max_iter=800, weight="weight")
    except Exception:
        eigen = nx.pagerank(G, weight="weight")

    centrality = pd.DataFrame(
        {
            "node": list(G.nodes()),
            "加权度": [degree.get(n, 0) for n in G.nodes()],
            "度中心性": [degree_cent.get(n, 0) for n in G.nodes()],
            "介数中心性": [betweenness.get(n, 0) for n in G.nodes()],
            "特征向量中心性": [eigen.get(n, 0) for n in G.nodes()],
            "节点类型": [G.nodes[n].get("node_type") for n in G.nodes()],
        }
    )
    centrality = centrality.merge(node_stats, on="node", how="left")
    centrality["主体名称"] = centrality["node"].str.replace(r"^[SB]\|", "", regex=True)

    if community_louvain and len(G) > 0:
        partition = community_louvain.best_partition(G, weight="weight", random_state=RANDOM_STATE)
    else:
        partition = {node: i for i, comp in enumerate(nx.connected_components(G)) for node in comp}
    centrality["社群"] = centrality["node"].map(partition)
    community_table = (
        centrality.groupby("社群")
        .agg(
            节点数量=("node", "count"),
            供应商数量=("节点类型", lambda x: (x == "供应商").sum()),
            采购人数量=("节点类型", lambda x: (x == "采购人").sum()),
            关联项目数量=("项目数量", "sum"),
            高风险项目数量=("高风险项目数量", "sum"),
            平均风险分=("平均风险分", "mean"),
            核心主体=("主体名称", lambda x: "、".join(x.head(3))),
        )
        .reset_index()
    )
    community_table["高风险比例"] = community_table["高风险项目数量"] / community_table["关联项目数量"].replace(0, np.nan)
    community_table = community_table.sort_values(["高风险比例", "关联项目数量"], ascending=[False, False])

    supplier_rank = (
        centrality[centrality["节点类型"] == "供应商"]
        .sort_values(["高风险项目数量", "特征向量中心性", "加权度"], ascending=False)
        .head(50)
        [["主体名称", "项目数量", "高风险项目数量", "高风险比例", "加权度", "度中心性", "介数中心性", "特征向量中心性", "平均风险分", "主服务类别", "社群"]]
    )
    buyer_rank = (
        centrality[(centrality["节点类型"] == "采购人") & (centrality["项目数量"] >= 2)]
        .sort_values(["高风险比例", "高风险项目数量", "项目数量"], ascending=False)
        .head(50)
        [["主体名称", "项目数量", "高风险项目数量", "高风险比例", "加权度", "度中心性", "介数中心性", "特征向量中心性", "平均风险分", "主服务类别", "社群"]]
    )

    draw_network_figures(G, centrality, edge_df, community_table)
    return supplier_rank, buyer_rank, community_table


def draw_network_figures(G: nx.Graph, centrality: pd.DataFrame, edge_df: pd.DataFrame, community_table: pd.DataFrame) -> None:
    def subgraph_by_nodes(nodes: list[str], max_nodes: int) -> nx.Graph:
        nodes = nodes[:max_nodes]
        sub = G.subgraph(nodes).copy()
        if sub.number_of_edges() == 0 and G.number_of_edges() > 0:
            top_edges = sorted(G.edges(data=True), key=lambda e: (e[2].get("risk_count", 0), e[2].get("weight", 0)), reverse=True)[:max_nodes]
            sub = G.edge_subgraph([(u, v) for u, v, _ in top_edges]).copy()
        return sub

    top_nodes = (
        centrality.sort_values(["高风险项目数量", "特征向量中心性", "加权度"], ascending=False)["node"].head(220).tolist()
    )
    sub = subgraph_by_nodes(top_nodes, 220)
    draw_one_network(sub, "图28 采购关系网络总体图（核心节点）", "Fig28_procurement_relation_network")

    risky_nodes = centrality[centrality["高风险项目数量"].fillna(0) > 0].sort_values(
        ["高风险项目数量", "平均风险分"], ascending=False
    )["node"].head(160).tolist()
    risk_sub = subgraph_by_nodes(risky_nodes, 160)
    draw_one_network(risk_sub, "图29 高风险供应商—采购人子网络图", "Fig29_high_risk_supplier_buyer_network")

    supplier_top = centrality[centrality["节点类型"] == "供应商"].sort_values("特征向量中心性", ascending=False).head(20).copy()
    supplier_top["主体名称短"] = supplier_top["主体名称"].map(lambda x: short_label(x, 18))
    bar_with_labels(
        supplier_top,
        "特征向量中心性",
        "主体名称短",
        "图30 供应商中心性 Top 20",
        "Fig30_supplier_centrality_top20",
        horizontal=True,
        color="#005F73",
        value_fmt="{:.3f}",
    )

    buyer_top = centrality[(centrality["节点类型"] == "采购人") & (centrality["项目数量"].fillna(0) >= 2)].sort_values(
        ["高风险比例", "高风险项目数量"], ascending=False
    ).head(20).copy()
    buyer_top["主体名称短"] = buyer_top["主体名称"].map(lambda x: short_label(x, 18))
    bar_with_labels(
        buyer_top,
        "高风险比例",
        "主体名称短",
        "图31 采购单位风险率 Top 20",
        "Fig31_buyer_risk_rate_top20",
        horizontal=True,
        color="#AE2012",
        percent_axis=True,
    )

    # Community-level network
    comm_graph = nx.Graph()
    node_to_comm = centrality.set_index("node")["社群"].to_dict()
    for _, row in edge_df.iterrows():
        c1 = node_to_comm.get(row["_supplier_node"])
        c2 = node_to_comm.get(row["_buyer_node"])
        if c1 is None or c2 is None:
            continue
        if not comm_graph.has_node(c1):
            comm_graph.add_node(c1)
        if not comm_graph.has_node(c2):
            comm_graph.add_node(c2)
        if c1 != c2:
            if comm_graph.has_edge(c1, c2):
                comm_graph[c1][c2]["weight"] += row["weight"]
            else:
                comm_graph.add_edge(c1, c2, weight=row["weight"])
    top_comms = community_table.head(25)["社群"].tolist()
    comm_sub = comm_graph.subgraph(top_comms).copy()
    if comm_sub.number_of_nodes() > 0:
        pos = nx.spring_layout(comm_sub, seed=RANDOM_STATE, k=0.45, iterations=80)
        fig, ax = plt.subplots(figsize=(9.5, 7))
        comm_info = community_table.set_index("社群")
        sizes = [80 + 2.3 * comm_info.loc[n, "节点数量"] for n in comm_sub.nodes()]
        colors = [comm_info.loc[n, "高风险比例"] if n in comm_info.index else 0 for n in comm_sub.nodes()]
        nx.draw_networkx_edges(comm_sub, pos, ax=ax, alpha=0.18, width=1.0, edge_color="#6C757D")
        nodes = nx.draw_networkx_nodes(
            comm_sub,
            pos,
            node_size=sizes,
            node_color=colors,
            cmap=RISK_CMAP,
            vmin=0,
            vmax=max(0.01, np.nanmax(colors)),
            linewidths=0.8,
            edgecolors="#263238",
            ax=ax,
        )
        labels = {n: f"C{n}" for n in comm_sub.nodes()}
        nx.draw_networkx_labels(comm_sub, pos, labels=labels, font_size=8, ax=ax)
        fig.colorbar(nodes, ax=ax, fraction=0.035, pad=0.02, label="社群高风险比例")
        ax.set_title("图32 风险社群网络图", loc="left")
        ax.axis("off")
        save_fig(fig, "Fig32_risk_community_network")


def draw_one_network(sub: nx.Graph, title: str, fname: str) -> None:
    if sub.number_of_nodes() == 0:
        return
    pos = nx.spring_layout(sub, seed=RANDOM_STATE, k=0.35, iterations=100, weight="weight")
    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    edge_width = [0.25 + 0.22 * math.log1p(d.get("weight", 1)) for _, _, d in sub.edges(data=True)]
    edge_color = ["#AE2012" if d.get("risk_count", 0) > 0 else "#ADB5BD" for _, _, d in sub.edges(data=True)]
    nx.draw_networkx_edges(sub, pos, ax=ax, width=edge_width, edge_color=edge_color, alpha=0.18)
    node_type = nx.get_node_attributes(sub, "node_type")
    for ntype, color, marker in [("供应商", "#0A9396", "o"), ("采购人", "#EE9B00", "s")]:
        nodes = [n for n in sub.nodes() if node_type.get(n) == ntype]
        sizes = [45 + 12 * sub.degree(n, weight="weight") for n in nodes]
        nx.draw_networkx_nodes(
            sub,
            pos,
            nodelist=nodes,
            node_size=sizes,
            node_color=color,
            node_shape=marker,
            alpha=0.78,
            linewidths=0.5,
            edgecolors="#263238",
            label=ntype,
            ax=ax,
        )
    top_labels = sorted(sub.nodes(), key=lambda n: sub.degree(n, weight="weight"), reverse=True)[:12]
    labels = {n: short_label(n.split("|", 1)[-1], 11) for n in top_labels}
    nx.draw_networkx_labels(sub, pos, labels=labels, font_size=7.5, ax=ax)
    ax.set_title(title, loc="left")
    ax.legend(loc="upper right")
    ax.axis("off")
    save_fig(fig, fname)


def robustness_analysis(main_service: pd.DataFrame, extend: pd.DataFrame, full: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ext = add_recalculated_rules(extend)
    main = main_service.copy()

    sample_compare = pd.DataFrame(
        [
            ["服务类主样本", len(main), main["is_high_risk_low_price"].mean(), main["final_high_risk"].mean() if "final_high_risk" in main else np.nan, main["price_ratio_clean"].median(), main["saving_rate_clean"].mean()],
            ["2025Q1扩展样本", len(ext), ext["is_high_risk_low_price"].mean(), np.nan, ext["price_ratio_clean"].median(), ext["saving_rate_clean"].mean()],
        ],
        columns=["样本类型", "样本量", "规则高风险比例", "模型高风险比例", "中标/预算比例中位数", "平均节约率"],
    )

    category_risk = (
        ext.groupby("采购大类", dropna=False)
        .agg(项目数量=("记录ID", "count"), 高风险数量=("is_high_risk_low_price", "sum"), 价格比例中位数=("price_ratio_clean", "median"))
        .reset_index()
    )
    category_risk["高风险比例"] = category_risk["高风险数量"] / category_risk["项目数量"]
    category_risk = category_risk.sort_values("高风险比例", ascending=False)

    threshold_rows = []
    for thr in [0.60, 0.65, 0.70]:
        threshold_rows.append(["固定阈值", f"price_ratio < {thr:.2f}", int((ext["price_ratio_clean"] < thr).sum()), (ext["price_ratio_clean"] < thr).mean()])
    group = ext["统一服务类别"].fillna("未识别")
    for q in [0.05, 0.10, 0.15]:
        threshold = ext.groupby(group)["price_ratio_clean"].transform(lambda x: x.quantile(q) if x.notna().sum() >= 10 else ext["price_ratio_clean"].quantile(q))
        flag = ext["price_ratio_clean"] <= threshold
        threshold_rows.append(["同类别分位数", f"低于{int(q*100)}%分位", int(flag.sum()), flag.mean()])
    threshold_table = pd.DataFrame(threshold_rows, columns=["阈值类型", "阈值设置", "识别数量", "识别比例"])

    # Figures
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    sc = sample_compare.copy()
    sns.barplot(data=sc, x="样本类型", y="规则高风险比例", palette=["#0A9396", "#CA6702"], ax=ax)
    for p in ax.patches:
        ax.text(p.get_x() + p.get_width() / 2, p.get_height(), f"{p.get_height():.1%}", ha="center", va="bottom", fontsize=9)
    ax.set_title("图33 主样本与扩展样本风险率对比图", loc="left")
    ax.set_ylabel("规则高风险比例")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    sns.despine(ax=ax)
    save_fig(fig, "Fig33_main_vs_extension_risk_rate")

    bar_with_labels(
        category_risk,
        "采购大类",
        "高风险比例",
        "图34 服务类、货物类、工程类风险率对比图",
        "Fig34_category_risk_rate_comparison",
        color="#005F73",
        percent_axis=True,
    )

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    threshold_plot = threshold_table.copy()
    threshold_plot["阈值标签"] = threshold_plot["阈值类型"] + "\n" + threshold_plot["阈值设置"]
    sns.lineplot(data=threshold_plot, x="阈值标签", y="识别数量", marker="o", lw=2.2, color="#AE2012", ax=ax)
    ax.set_title("图35 不同阈值下高风险项目数量变化图", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("识别数量")
    ax.tick_params(axis="x", rotation=20)
    sns.despine(ax=ax)
    save_fig(fig, "Fig35_threshold_sensitivity")

    ext_high = ext[ext["is_high_risk_low_price"] == 1]["统一服务类别"].fillna("未识别").value_counts().head(15).reset_index()
    ext_high.columns = ["统一服务类别", "高风险数量"]
    ext_high["统一服务类别"] = ext_high["统一服务类别"].map(lambda x: short_label(x, 18))
    bar_with_labels(
        ext_high,
        "高风险数量",
        "统一服务类别",
        "图36 扩展样本高风险服务类型分布图",
        "Fig36_extension_high_risk_service_distribution",
        horizontal=True,
        color="#CA6702",
    )

    return sample_compare, category_risk, threshold_table


def write_report(summary: dict, table_paths: dict[str, Path], figure_paths: list[Path]) -> Path:
    report_path = OUTPUT_DIR / "论文数据分析汇总报告.md"
    lines = [
        "# 政府采购项目异常低价风险分析结果汇总",
        "",
        "本报告由可复跑脚本自动生成，原始 CSV 未被修改。正式分析口径以四张拆分表为主，`主表_v2`仅作为总备份主表。",
        "",
        "## 核心结果",
        "",
        f"- 全样本项目数：{summary['full_n']:,}；价格有效样本数：{summary['price_n']:,}；服务类主样本数：{summary['service_n']:,}；2025Q1扩展样本数：{summary['extend_n']:,}。",
        f"- 价格有效样本规则高风险项目：{summary['price_rule_high_n']:,} 个，占 {summary['price_rule_high_rate']:.2%}。",
        f"- 服务类主样本规则高风险项目：{summary['service_rule_high_n']:,} 个，占 {summary['service_rule_high_rate']:.2%}。",
        f"- 集成异常检测模型识别服务类高风险项目：{summary['model_high_n']:,} 个，占 {summary['model_high_rate']:.2%}。",
        f"- XGBoost 测试集 AUC：{summary['xgb_auc']:.3f}；F1：{summary['xgb_f1']:.3f}。",
        f"- SHAP Top 5 变量：{summary['shap_top5']}。",
        f"- 2025Q1扩展样本规则高风险比例：{summary['extend_rule_high_rate']:.2%}。",
        "",
        "## 输出目录结构",
        "",
        f"- 表格目录：`{TABLE_DIR}`",
        f"- 图件目录：`{FIG_DIR}`",
        f"- 带模型结果的数据目录：`{DATA_DIR}`",
        "",
        "## 主要表格索引",
        "",
        "| 表格文件 | 说明 |",
        "|---|---|",
    ]
    table_labels = {
        "Table01_data_sources": "数据来源说明表",
        "Table02_field_structure": "字段结构说明表",
        "Table03_sample_split": "清洗后样本划分表",
        "Table04_procurement_category_distribution": "采购大类分布表",
        "Table05_low_price_indicator_definitions": "异常低价指标说明表",
        "Table06_rule_detection_comparison": "规则识别结果对比表",
        "Table07_service_category_risk_rate": "不同服务类别风险率表",
        "Table09_lda_topic_interpretation": "LDA主题解释表",
        "Table12_anomaly_model_results": "异常检测模型结果表",
        "Table14_logistic_regression_results": "Logistic回归结果表",
        "Table15_supervised_model_evaluation": "监督模型评价结果表",
        "Table16_shap_importance": "SHAP重要变量表",
        "Table17_qca_causal_paths": "QCA成因组合路径表",
        "Table19_supplier_centrality_ranking": "高风险供应商/中心性排名表",
        "Table20_buyer_risk_ranking": "高风险采购单位排名表",
        "Table22_robustness_results": "稳健性检验结果表",
    }
    for stem, label in table_labels.items():
        path = table_paths.get(stem)
        if path:
            lines.append(f"| [{path.name}]({path.as_posix()}) | {label} |")

    lines += [
        "",
        "## 图件索引",
        "",
        "| 图件文件 |",
        "|---|",
    ]
    for path in sorted(figure_paths):
        if path.suffix.lower() == ".png":
            lines.append(f"| [{path.name}]({path.as_posix()}) |")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    ensure_dirs()
    font_path = configure_plotting()

    print("读取数据...")
    full = read_table("全样本表")
    price = read_table("价格有效样本表")
    service = read_table("服务类主样本表")
    extend = read_table("2025Q1扩展样本表")
    v2 = read_table("主表_v2")

    print("规则口径复核...")
    price_calc = add_recalculated_rules(price)
    extend_calc = add_recalculated_rules(extend)
    save_data(price_calc, "price_valid_sample_rule_recalculated")
    save_data(extend_calc, "extension_2025q1_rule_recalculated")

    table_paths: dict[str, Path] = {}
    for name, table in make_distribution_tables(full, price, service, extend, v2).items():
        table_paths[name] = save_table(table, name)
    for name, table in make_rule_tables(price, service).items():
        table_paths[name] = save_table(table, name)

    print("绘制基础描述与风险规则图...")
    make_basic_figures(full, price, service)

    print("文本特征、LDA主题与供应商画像...")
    service_text, keyword_table, risk_keyword_table, lda_topics, text_rules = text_and_topic_model(service, full, font_path)
    service_text, supplier_profile = add_supplier_profile(service_text, "is_high_risk_low_price")
    table_paths["Table08_text_preprocessing_rules"] = save_table(text_rules, "Table08_text_preprocessing_rules")
    table_paths["Table09_lda_topic_interpretation"] = save_table(lda_topics, "Table09_lda_topic_interpretation")
    supplier_field_table = pd.DataFrame(
        [
            ["supplier_win_count", "同一供应商在服务类主样本中出现次数", "供应商活跃度"],
            ["supplier_low_price_count", "供应商关联规则高风险项目数量", "低价中标历史"],
            ["supplier_avg_saving_rate", "供应商项目平均节约率", "价格行为画像"],
            ["supplier_cross_province_rate", "跨省中标项目占比", "跨区域交易画像"],
            ["supplier_category_count", "涉及统一服务类别数量", "经营类别广度"],
            ["supplier_risk_score", "低价率、低价次数、中标次数、跨省比例加权", "供应商综合风险画像分"],
        ],
        columns=["字段", "构造口径", "解释"],
    )
    table_paths["Table10_supplier_profile_fields"] = save_table(supplier_field_table, "Table10_supplier_profile_fields")
    table_paths["Table10b_supplier_profile_summary"] = save_table(supplier_profile, "Table10b_supplier_profile_summary")
    table_paths["Table10c_overall_keywords"] = save_table(keyword_table, "Table10c_overall_keywords")
    table_paths["Table10d_risk_vs_normal_keywords"] = save_table(risk_keyword_table, "Table10d_risk_vs_normal_keywords")
    make_topic_figures(service_text, lda_topics, keyword_table)

    print("异常检测模型...")
    service_model, model_params, model_results = anomaly_detection(service_text)
    table_paths["Table11_anomaly_model_parameters"] = save_table(model_params, "Table11_anomaly_model_parameters")
    table_paths["Table12_anomaly_model_results"] = save_table(model_results, "Table12_anomaly_model_results")
    table_paths["Table13_high_risk_descriptive_statistics"] = save_table(high_risk_descriptives(service_model), "Table13_high_risk_descriptive_statistics")
    make_anomaly_figures(service_model, model_results)

    print("监督模型、SHAP与QCA...")
    eval_table, logistic_table, rf_importance, xgb_importance, shap_importance, shap_payload = supervised_models(service_model)
    table_paths["Table14_logistic_regression_results"] = save_table(logistic_table, "Table14_logistic_regression_results")
    table_paths["Table15_supervised_model_evaluation"] = save_table(eval_table, "Table15_supervised_model_evaluation")
    table_paths["Table16_shap_importance"] = save_table(shap_importance, "Table16_shap_importance")
    table_paths["Table16b_random_forest_importance"] = save_table(rf_importance, "Table16b_random_forest_importance")
    table_paths["Table16c_xgboost_importance"] = save_table(xgb_importance, "Table16c_xgboost_importance")
    make_supervised_figures(eval_table, rf_importance, xgb_importance, shap_importance, shap_payload)
    qca_paths = qca_analysis(service_model)
    table_paths["Table17_qca_causal_paths"] = save_table(qca_paths, "Table17_qca_causal_paths")

    print("关系网络分析...")
    network_def = pd.DataFrame(
        [
            ["供应商节点", "统一供应商名称", "中标主体"],
            ["采购人节点", "采购人名称", "采购需求发布主体"],
            ["供应商—采购人边", "同一项目中形成交易关系", "边权为交易项目数量，高风险边记录风险项目数"],
            ["度中心性", "连接主体数量", "识别高频交易主体"],
            ["介数中心性", "网络桥梁位置", "识别关键中介主体"],
            ["特征向量中心性", "连接重要主体程度", "识别核心交易主体"],
            ["Louvain社群", "基于交易网络模块度划分", "识别风险聚集群体"],
        ],
        columns=["网络元素/指标", "定义", "用途"],
    )
    table_paths["Table18_network_node_edge_definitions"] = save_table(network_def, "Table18_network_node_edge_definitions")
    supplier_rank, buyer_rank, community_table = network_analysis(service_model)
    table_paths["Table19_supplier_centrality_ranking"] = save_table(supplier_rank, "Table19_supplier_centrality_ranking")
    table_paths["Table20_buyer_risk_ranking"] = save_table(buyer_rank, "Table20_buyer_risk_ranking")
    table_paths["Table21_high_risk_community_features"] = save_table(community_table, "Table21_high_risk_community_features")

    print("稳健性检验...")
    rob, category_risk, threshold_table = robustness_analysis(service_model, extend, full)
    table_paths["Table22_robustness_results"] = save_table(rob, "Table22_robustness_results")
    table_paths["Table23_procurement_category_risk_comparison"] = save_table(category_risk, "Table23_procurement_category_risk_comparison")
    table_paths["Table24_threshold_sensitivity"] = save_table(threshold_table, "Table24_threshold_sensitivity")

    print("输出模型结果数据...")
    result_cols = [
        "记录ID",
        "公告标题",
        "发布日期",
        "项目省份",
        "项目城市",
        "项目名称",
        "采购人名称",
        "统一供应商名称",
        "预算金额",
        "中标金额",
        "price_ratio_clean",
        "saving_rate_clean",
        "采购方式标准化",
        "统一服务类别",
        "rule_risk_score",
        "rule_risk_level",
        "is_high_risk_low_price",
        "iforest_score",
        "lof_score",
        "ocsvm_score",
        "ensemble_risk_score",
        "model_risk_level",
        "final_high_risk",
        "lda_topic",
        "supplier_win_count",
        "supplier_low_price_rate",
        "supplier_risk_score",
    ]
    result_cols = [c for c in result_cols if c in service_model.columns]
    save_data(service_model[result_cols].sort_values("ensemble_risk_score", ascending=False), "service_main_model_results")

    policy_evidence = pd.DataFrame(
        [
            ["建立异常低价自动预警机制", "规则得分、集成风险分数、阈值敏感性分析", "第三章、第五章、第八章"],
            ["按采购类别设置差异化审查阈值", "服务类别风险率、箱线图、主题风险率", "第三章、第四章"],
            ["建立供应商低价中标画像机制", "供应商中标次数、低价次数、网络中心性", "第四章、第七章"],
            ["加强高风险采购方式和高风险地区监管", "采购方式/省份风险率、宏观变量解释", "第三章、第六章"],
            ["建立中标后履约跟踪机制", "高风险项目名单、关系网络社群", "第五章、第七章"],
        ],
        columns=["政策建议", "模型依据", "对应章节"],
    )
    table_paths["Table25_policy_recommendation_evidence"] = save_table(policy_evidence, "Table25_policy_recommendation_evidence")
    draw_flow_diagram(
        "Fig37_regulatory_closed_loop",
        "图37 政府采购异常低价风险监管闭环图",
        ["公告数据采集", "异常低价预警", "供应商画像", "人工复核", "履约跟踪", "风险规则更新"],
        horizontal=True,
    )

    xgb_row = eval_table[eval_table["模型"].eq("XGBoost")].iloc[0]
    summary = {
        "full_n": int(len(full)),
        "price_n": int(len(price)),
        "service_n": int(len(service_model)),
        "extend_n": int(len(extend)),
        "price_rule_high_n": int(price["is_high_risk_low_price"].sum()),
        "price_rule_high_rate": float(price["is_high_risk_low_price"].mean()),
        "service_rule_high_n": int(service_model["is_high_risk_low_price"].sum()),
        "service_rule_high_rate": float(service_model["is_high_risk_low_price"].mean()),
        "model_high_n": int(service_model["final_high_risk"].sum()),
        "model_high_rate": float(service_model["final_high_risk"].mean()),
        "xgb_auc": float(xgb_row["AUC"]),
        "xgb_f1": float(xgb_row["F1"]),
        "shap_top5": "、".join(shap_importance["变量"].head(5).astype(str).tolist()),
        "extend_rule_high_rate": float(extend["is_high_risk_low_price"].mean()),
    }
    (OUTPUT_DIR / "analysis_key_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    figure_paths = list(FIG_DIR.glob("*.png"))
    report_path = write_report(summary, table_paths, figure_paths)
    print(f"完成。报告：{report_path}")
    print(f"表格：{TABLE_DIR}")
    print(f"图件：{FIG_DIR}")
    print(f"数据：{DATA_DIR}")


if __name__ == "__main__":
    main()
