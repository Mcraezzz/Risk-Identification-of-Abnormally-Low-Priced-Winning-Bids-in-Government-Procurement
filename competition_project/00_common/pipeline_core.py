# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import math
import re
import textwrap
import warnings
from collections import Counter
from matplotlib.gridspec import GridSpec
from matplotlib.colors import ListedColormap
from pathlib import Path

import jieba
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import shap
try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except Exception:
    sm = None
    HAS_STATSMODELS = False
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, PercentFormatter
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
BASE_DIR = Path(os.environ.get("PROCUREMENT_DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
WORK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = WORK_DIR / "输出结果"
TABLE_DIR = OUTPUT_DIR / "tables"
FIG_DIR = OUTPUT_DIR / "figures"
FIG_DIR2 = OUTPUT_DIR / "figures2"
DATA_DIR = OUTPUT_DIR / "data"
MODEL_DIR = OUTPUT_DIR / "models"

FILES = {
    "全样本表": "full_sample.csv",
    "价格有效样本表": "price_valid_sample.csv",
    "服务类主样本表": "service_main_sample.csv",
    "2025Q1扩展样本表": "extension_2025q1_sample.csv",
    "主表_v2": "full_sample.csv",
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
    "#0072B2",  # blue
    "#009E73",  # green
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#E69F00",  # orange
    "#6A3D9A",  # violet
    "#4D4D4D",  # graphite
]

ACADEMIC = {
    "ink": "#172033",
    "muted": "#5B6472",
    "grid": "#E7EBF0",
    "axis": "#9AA5B1",
    "panel": "#FBFCFE",
    "header": "#0F2E4D",
}

RISK_CMAP = LinearSegmentedColormap.from_list(
    "academic_risk", ["#009E73", "#F0E6A6", "#E69F00", "#D55E00", "#8B1A1A"]
)

STOPWORDS = {
    # 采购公告通用词
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
    # 城市与地域词（避免LDA主题被地域主导）
    "北京", "北京市", "上海", "上海市", "广州", "广州市", "深圳", "深圳市",
    "重庆", "重庆市", "天津", "天津市", "南京", "南京市", "武汉", "武汉市",
    "成都", "成都市", "西安", "西安市", "杭州", "杭州市", "苏州", "苏州市",
    "郑州", "郑州市", "长沙", "长沙市", "青岛", "青岛市", "大连", "大连市",
    "宁波", "宁波市", "厦门", "厦门市", "无锡", "无锡市", "福州", "福州市",
    "济南", "济南市", "合肥", "合肥市", "昆明", "昆明市", "哈尔滨", "哈尔滨市",
    "沈阳", "沈阳市", "长春", "长春市", "南昌", "南昌市", "贵阳", "贵阳市",
    "南宁", "南宁市", "海口", "海口市", "兰州", "兰州市", "银川", "银川市",
    "西宁", "西宁市", "乌鲁木齐", "乌鲁木齐市", "拉萨", "拉萨市", "呼和浩特",
    "呼和浩特市", "石家庄", "石家庄市", "太原", "太原市",
    "省份", "省市", "地区", "区域", "本地", "外地", "省内", "省外",
    # 日期与时间词
    "年月日", "日期", "日历", "工作日", "天", "日", "月", "年", "季度",
    "周期", "时长", "期限", "截止", "开始", "结束", "起始", "终止",
    # 联系人及地址相关
    "联系人", "联系人姓名", "联系电话", "手机号码", "邮箱", "电子邮件",
    "传真", "地址", "邮编", "邮政编码", "网址",
    # 单位名称通用机构词
    "大学", "学院", "医院", "中学", "小学", "幼儿园", "研究所", "研究中心",
    "局", "厅", "部", "委", "办", "办公室", "街道", "社区", "镇政府",
    "县政府", "市政府", "省政府", "国家级", "省级", "市级", "县级",
    "机关", "部门", "中心", "学校", "图书馆", "博物馆", "卫生院",
    # 其他低信息词
    "具体", "有关", "以及", "以上", "以下", "所述", "所述内容",
    "本次", "本项", "本项目", "此次", "该", "其", "等", "及",
}


def ensure_dirs() -> None:
    for path in [OUTPUT_DIR, TABLE_DIR, FIG_DIR, FIG_DIR2, DATA_DIR, MODEL_DIR]:
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
    plt.rcParams["figure.dpi"] = 180
    plt.rcParams["savefig.dpi"] = 420
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = ACADEMIC["panel"]
    plt.rcParams["axes.edgecolor"] = ACADEMIC["axis"]
    plt.rcParams["axes.labelcolor"] = ACADEMIC["ink"]
    plt.rcParams["axes.titlecolor"] = ACADEMIC["ink"]
    plt.rcParams["axes.titleweight"] = "semibold"
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["xtick.labelsize"] = 9
    plt.rcParams["ytick.labelsize"] = 9
    plt.rcParams["xtick.color"] = ACADEMIC["muted"]
    plt.rcParams["ytick.color"] = ACADEMIC["muted"]
    plt.rcParams["grid.color"] = ACADEMIC["grid"]
    plt.rcParams["grid.linewidth"] = 0.8
    plt.rcParams["legend.frameon"] = True
    plt.rcParams["legend.facecolor"] = "white"
    plt.rcParams["legend.edgecolor"] = ACADEMIC["grid"]
    plt.rcParams["legend.framealpha"] = 0.94
    sns.set_theme(
        context="paper",
        style="whitegrid",
        palette=PALETTE,
        font=plt.rcParams["font.sans-serif"][0],
        rc={
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "lines.linewidth": 2.0,
        },
    )
    return font_path


def polish_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(ACADEMIC["panel"])
    ax.title.set_color(ACADEMIC["ink"])
    ax.title.set_weight("semibold")
    ax.xaxis.label.set_color(ACADEMIC["ink"])
    ax.yaxis.label.set_color(ACADEMIC["ink"])
    ax.tick_params(colors=ACADEMIC["muted"], length=3, width=0.7)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(ACADEMIC["axis"])
        ax.spines[side].set_linewidth(0.8)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    grid_axis = getattr(ax, "_codex_grid_axis", "both")
    grid_style = {"color": ACADEMIC["grid"], "linewidth": 0.8, "alpha": 0.9}
    if grid_axis == "none":
        ax.grid(False, which="both", axis="both")
    elif grid_axis in {"x", "y"}:
        ax.grid(False, which="both", axis="both")
        ax.grid(True, axis=grid_axis, **grid_style)
    else:
        ax.grid(True, **grid_style)
    legend = ax.get_legend()
    if legend is not None:
        frame = legend.get_frame()
        frame.set_facecolor("white")
        frame.set_edgecolor(ACADEMIC["grid"])
        frame.set_linewidth(0.8)
        frame.set_alpha(0.94)


def polish_figure(fig: plt.Figure) -> None:
    fig.patch.set_facecolor("white")
    for ax in fig.axes:
        if ax.get_visible():
            polish_axes(ax)


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


def strip_internal_titles(fig: plt.Figure) -> None:
    """图题统一放在Word图注中，图片内部不再重复显示标题。"""
    if getattr(fig, "_suptitle", None) is not None:
        fig._suptitle.set_text("")
    for ax in fig.axes:
        ax.set_title("", loc="left")
        ax.set_title("", loc="center")
        ax.set_title("", loc="right")


def save_fig(fig: plt.Figure, name: str, pdf: bool = True) -> Path:
    strip_internal_titles(fig)
    polish_figure(fig)
    png_path = FIG_DIR / f"{name}.png"
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    fig.savefig(FIG_DIR2 / f"{name}.png", bbox_inches="tight", pad_inches=0.08, facecolor="white")
    if pdf:
        fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.08, facecolor="white")
        fig.savefig(FIG_DIR2 / f"{name}.pdf", bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    return png_path


def short_label(value: object, max_len: int = 16) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def gradient_palette(light: str, dark: str, n: int) -> list[str]:
    if n <= 0:
        return []
    return sns.blend_palette([light, dark], n_colors=n).as_hex()


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
            color = PALETTE[i % len(PALETTE)]
            box = patches.FancyBboxPatch(
                (x - 0.075, y - 0.15),
                0.15,
                0.30,
                boxstyle="round,pad=0.018,rounding_size=0.015",
                linewidth=1.1,
                edgecolor=color,
                facecolor="#FFFFFF",
            )
            ax.add_patch(box)
            ax.add_patch(patches.Circle((x - 0.058, y + 0.115), 0.022, color=color, zorder=3))
            ax.text(x - 0.058, y + 0.115, str(i + 1), ha="center", va="center", fontsize=8, color="white", weight="bold")
            ax.text(x, y, textwrap.fill(text, 12), ha="center", va="center", fontsize=10, weight="semibold", color=ACADEMIC["ink"])
            if i < len(steps) - 1:
                ax.annotate(
                    "",
                    xy=(xs[i + 1] - 0.09, y),
                    xytext=(x + 0.09, y),
                    arrowprops=dict(arrowstyle="->", lw=1.4, color=ACADEMIC["muted"]),
                )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        fig, ax = plt.subplots(figsize=(7.2, 9.2))
        ys = np.linspace(0.88, 0.12, len(steps))
        for i, (y, text) in enumerate(zip(ys, steps)):
            color = PALETTE[i % len(PALETTE)]
            box = patches.FancyBboxPatch(
                (0.18, y - 0.055),
                0.64,
                0.11,
                boxstyle="round,pad=0.018,rounding_size=0.015",
                linewidth=1.1,
                edgecolor=color,
                facecolor="#FFFFFF",
            )
            ax.add_patch(box)
            ax.add_patch(patches.Circle((0.205, y), 0.025, color=color, zorder=3))
            ax.text(0.205, y, str(i + 1), ha="center", va="center", fontsize=8.5, color="white", weight="bold")
            ax.text(0.52, y, textwrap.fill(text, 20), ha="center", va="center", fontsize=10.5, weight="semibold", color=ACADEMIC["ink"])
            if i < len(steps) - 1:
                ax.annotate(
                    "",
                    xy=(0.50, ys[i + 1] + 0.075),
                    xytext=(0.50, y - 0.075),
                    arrowprops=dict(arrowstyle="->", lw=1.4, color=ACADEMIC["muted"]),
                )
        if side_notes:
            for y, note in zip(ys, side_notes):
                ax.text(0.86, y, textwrap.fill(note, 16), ha="left", va="center", fontsize=8.8, color=ACADEMIC["muted"])
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
    color: str | list[str] = "#0A9396",
    percent_axis: bool = False,
    value_fmt: str = "{:.0f}",
) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    if horizontal:
        plot_data = data.sort_values(x, ascending=True)
        palette = color if isinstance(color, list) else None
        sns.barplot(
            data=plot_data,
            x=x,
            y=y,
            ax=ax,
            color=None if palette else color,
            palette=palette,
            edgecolor="white",
            linewidth=0.7,
        )
        if palette:
            for patch, patch_color in zip(ax.patches, palette):
                patch.set_facecolor(patch_color)
        for p in ax.patches:
            width = p.get_width()
            label = f"{width:.1%}" if percent_axis else value_fmt.format(width)
            ax.text(
                width + (ax.get_xlim()[1] * 0.01),
                p.get_y() + p.get_height() / 2,
                label,
                va="center",
                fontsize=8.2,
                color=ACADEMIC["ink"],
            )
        max_width = max((p.get_width() for p in ax.patches), default=0)
        if max_width > 0:
            ax.set_xlim(right=max(ax.get_xlim()[1], max_width * 1.12))
        if percent_axis:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    else:
        palette = color if isinstance(color, list) else None
        sns.barplot(
            data=data,
            x=x,
            y=y,
            ax=ax,
            color=None if palette else color,
            palette=palette,
            edgecolor="white",
            linewidth=0.7,
        )
        if palette:
            for patch, patch_color in zip(ax.patches, palette):
                patch.set_facecolor(patch_color)
        for p in ax.patches:
            height = p.get_height()
            label = f"{height:.1%}" if percent_axis else value_fmt.format(height)
            ax.text(
                p.get_x() + p.get_width() / 2,
                height,
                label,
                ha="center",
                va="bottom",
                fontsize=8.2,
                color=ACADEMIC["ink"],
            )
        max_height = max((p.get_height() for p in ax.patches), default=0)
        if max_height > 0:
            ax.set_ylim(top=max(ax.get_ylim()[1], max_height * 1.14))
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

    # 词云保留总体和普通项目，高风险项目改为镜像条形差异图。
    if font_path:
        for tokens, title, fname in [
            (all_tokens, "服务类政府采购公告总体关键词", "Fig11_overall_keyword_wordcloud"),
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

    keyword_compare = pd.merge(high_keyword_table, normal_keyword_table, on="关键词", how="outer").fillna(0)
    high_total = max(len(high_tokens), 1)
    normal_total = max(len(normal_tokens), 1)
    keyword_compare["高风险频率"] = keyword_compare["高风险词频"] / high_total * 1000
    keyword_compare["普通项目频率"] = keyword_compare["正常项目词频"] / normal_total * 1000
    keyword_compare["高风险突出度"] = keyword_compare["高风险频率"] - keyword_compare["普通项目频率"]

    priority_terms = ["物业管理", "评审", "运维", "联系人", "服务期限", "安保", "保洁", "人员", "单位名称", "服务项目"]
    low_info_terms = STOPWORDS | {
        "G2025",
        "JSZC",
        "pdf",
        "企业",
        "股份",
        "年度",
        "信用",
        "折扣",
        "社会",
        "投标",
        "品目",
        "江苏",
        "南京市",
        "太仓市",
        "国家级",
        "序号",
        "项目编号",
        "项目名称",
        "单位地址",
        "发布",
        "名单",
        "其他",
        "之日起",
        "事宜",
        "中华人民共和国财政部",
        "中小企业",
    }

    def keep_keyword(word: object) -> bool:
        text = str(word)
        if text in priority_terms:
            return True
        if text in low_info_terms:
            return False
        if len(text) < 2 or re.search(r"[A-Za-z0-9]", text):
            return False
        return True

    filtered = keyword_compare[keyword_compare["关键词"].map(keep_keyword)].copy()
    priority_rows = filtered[filtered["关键词"].isin(priority_terms)]
    remaining = filtered[~filtered["关键词"].isin(priority_terms)].sort_values(["高风险突出度", "高风险频率"], ascending=False)
    selected = pd.concat([priority_rows, remaining.head(max(0, 14 - len(priority_rows)))], ignore_index=True)
    selected = selected.drop_duplicates("关键词").sort_values("高风险突出度")
    if not selected.empty:
        fig, ax = plt.subplots(figsize=(10.8, 6.6))
        y = np.arange(len(selected))
        ax.barh(y, -selected["普通项目频率"], color="#4E79A7", alpha=0.82, label="普通项目")
        ax.barh(y, selected["高风险频率"], color="#D55E00", alpha=0.88, label="高风险项目")
        for yi, (_, row) in enumerate(selected.iterrows()):
            ax.text(-row["普通项目频率"] - 0.04, yi, f"{row['普通项目频率']:.2f}", ha="right", va="center", fontsize=8.2, color=ACADEMIC["muted"])
            ax.text(row["高风险频率"] + 0.04, yi, f"{row['高风险频率']:.2f}", ha="left", va="center", fontsize=8.2, color=ACADEMIC["muted"])
        limit = max(selected["普通项目频率"].max(), selected["高风险频率"].max()) * 1.28
        ax.axvline(0, color=ACADEMIC["axis"], lw=1.0)
        ax.set_xlim(-limit, limit)
        ax.set_yticks(y)
        ax.set_yticklabels(selected["关键词"])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{abs(x):.1f}"))
        ax.set_xlabel("词频（次/千词，左侧为普通项目，右侧为高风险项目）")
        ax.set_title("图8 高风险项目与普通项目关键词差异对比图", loc="left")
        ax.legend(loc="lower right", ncol=2)
        sns.despine(ax=ax, left=True)
        save_fig(fig, "Fig12_high_risk_keyword_wordcloud")

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
    bar_with_labels(category, "采购大类", "项目数量", "图3 采购大类分布", "Fig03_procurement_category_distribution", color="#2563EB")

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
        color=gradient_palette("#BEE3E5", "#005F73", len(service_dist)),
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

    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    ratio = price["price_ratio_clean"].dropna().clip(0, 1.25)
    median_ratio = ratio.median()
    group = price["统一服务类别"].fillna("未识别") if "统一服务类别" in price.columns else pd.Series("未识别", index=price.index)
    q10_by_group = price.assign(_group=group).groupby("_group")["price_ratio_clean"].transform(
        lambda x: x.quantile(0.10) if x.notna().sum() >= 10 else ratio.quantile(0.10)
    )
    q10_ref = float(q10_by_group.dropna().median()) if q10_by_group.notna().any() else float(ratio.quantile(0.10))
    sns.histplot(ratio, bins=45, kde=True, ax=ax, color="#0A9396", alpha=0.72)
    ax.axvspan(0, 0.65, color="#AE2012", alpha=0.08, label="高风险样本关注区间")
    ax.axvline(0.65, color="#AE2012", lw=1.8, linestyle="--", label="政策参考阈值0.65")
    ax.axvline(q10_ref, color="#005F73", lw=1.6, linestyle="-.", label="同类别10%分位数参考线")
    ax.axvline(median_ratio, color="#4D4D4D", lw=1.5, linestyle=":", label=f"中位数{median_ratio:.2f}")
    ax.set_title("图5 中标/预算比例分布及风险阈值图", loc="left")
    ax.set_xlabel("中标/预算比例")
    ax.set_ylabel("项目数量")
    ax.legend(loc="upper left")
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
    category_order = (
        box_data.groupby("统一服务类别")["price_ratio_clean"]
        .median()
        .sort_values()
        .index
        .tolist()
    )
    label_map = {cat: short_label(cat, 14) for cat in category_order}
    box_data["统一服务类别短名"] = box_data["统一服务类别"].map(label_map)
    order_labels = [label_map[cat] for cat in category_order]
    risk_rates = box_data.groupby("统一服务类别")["is_high_risk_low_price"].mean()
    fig, ax = plt.subplots(figsize=(10.8, 6.8))
    sns.boxplot(
        data=box_data,
        y="统一服务类别短名",
        x="price_ratio_clean",
        order=order_labels,
        ax=ax,
        palette=PALETTE,
        showfliers=True,
        fliersize=2.5,
        linewidth=0.8,
    )
    ax.axvline(0.65, color="#AE2012", linestyle="--", lw=1.4, label="政策参考阈值0.65")
    for yi, cat in enumerate(category_order):
        ax.text(1.015, yi, f"高风险{risk_rates.get(cat, 0):.1%}", va="center", ha="left", fontsize=8.4, color=ACADEMIC["muted"])
    ax.set_xlim(0, 1.22)
    ax.set_title("图6 不同服务类别价格比例排序箱线图", loc="left")
    ax.set_xlabel("中标/预算比例")
    ax.set_ylabel("")
    ax.legend(loc="lower right")
    sns.despine(ax=ax)
    save_fig(fig, "Fig08_service_price_ratio_boxplot")

    rule_counts = pd.DataFrame(
        {
            "规则": ["政策阈值<0.65", "同类别10%分位", "同类别5%分位", "IQR离群", "稳健Z分数"],
            "异常项目数量": [int(price[col].sum()) for col in RULE_COLS],
        }
    )
    rule_palette = ["#4E79A7", "#59A14F", "#76B7B2", "#3B6C8E", "#2F4B7C"]
    bar_with_labels(rule_counts, "规则", "异常项目数量", "图9 四种规则识别异常数量对比", "Fig09_rule_detection_counts", color=rule_palette)

    level_order = ["正常", "低风险", "中风险", "高风险"]
    level = price["rule_risk_level"].value_counts().reindex(level_order, fill_value=0).reset_index()
    level.columns = ["综合风险等级", "项目数量"]
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    colors = ["#94D2BD", "#E9D8A6", "#EE9B00", "#AE2012"]
    sns.barplot(data=level, x="综合风险等级", y="项目数量", palette=colors, ax=ax, edgecolor="#263238", linewidth=0.3)
    for p in ax.patches:
        ax.text(p.get_x() + p.get_width() / 2, p.get_height(), f"{p.get_height():.0f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("图10 综合风险等级分布", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("项目数量")
    ax.ticklabel_format(axis="y", style="plain")
    ax.margins(y=0.10)
    fig.subplots_adjust(left=0.14, top=0.90)
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
        color=["#6B5B95", "#B56576", "#E56B6F", "#EAAC8B", "#9A8C98", "#C97C5D"],
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
        color="#5E548E",
    )

    methods = ["Isolation Forest", "LOF", "One-Class SVM", "规则高风险"]
    upset_flags = pd.DataFrame(
        {
            "Isolation Forest": service["iforest_anomaly"].eq(1),
            "LOF": service["lof_anomaly"].eq(1),
            "One-Class SVM": service["ocsvm_anomaly"].eq(1),
            "规则高风险": service["is_high_risk_low_price"].eq(1),
        },
        index=service.index,
    )
    combo_counts = (
        upset_flags[upset_flags.any(axis=1)]
        .groupby(methods)
        .size()
        .reset_index(name="交集数量")
    )
    combo_counts["方法数量"] = combo_counts[methods].sum(axis=1)
    combo_plot = combo_counts.sort_values(["方法数量", "交集数量"], ascending=[False, False]).head(14).reset_index(drop=True)
    if not combo_plot.empty:
        fig = plt.figure(figsize=(11.4, 6.8))
        gs = GridSpec(2, 2, figure=fig, width_ratios=[1.45, 5.0], height_ratios=[3.0, 1.45], hspace=0.05, wspace=0.10)
        ax_sets = fig.add_subplot(gs[:, 0])
        ax_bars = fig.add_subplot(gs[0, 1])
        ax_matrix = fig.add_subplot(gs[1, 1], sharex=ax_bars)

        set_sizes = upset_flags.sum().reindex(methods)
        y_set = np.arange(len(methods))
        ax_sets.barh(y_set, set_sizes.values, color="#5E548E", alpha=0.88)
        set_label_offset = max(set_sizes.max() * 0.04, 1)
        for yi, value in enumerate(set_sizes.values):
            ax_sets.text(
                value - set_label_offset,
                yi,
                f"{int(value)}",
                va="center",
                ha="right",
                fontsize=8.5,
                color="white",
                weight="bold",
            )
        ax_sets.set_yticks(y_set)
        ax_sets.set_yticklabels(methods)
        ax_sets.invert_yaxis()
        ax_sets.set_xlabel("识别总数")
        ax_sets.set_xlim(0, max(set_sizes.max() * 1.08, 1))
        ax_sets.grid(axis="x", alpha=0.6)
        sns.despine(ax=ax_sets, left=True)

        x = np.arange(len(combo_plot))
        ax_bars.bar(x, combo_plot["交集数量"], color="#D55E00", alpha=0.88, width=0.66)
        for xi, value in zip(x, combo_plot["交集数量"]):
            ax_bars.text(xi, value, f"{int(value)}", ha="center", va="bottom", fontsize=8.4)
        ax_bars.set_ylabel("交集项目数", labelpad=3, fontsize=9.5)
        ax_bars.set_title("图11 不同异常检测方法识别结果UpSet图", loc="left")
        ax_bars.tick_params(axis="x", bottom=False, labelbottom=False)
        sns.despine(ax=ax_bars, bottom=True)

        for yi, method in enumerate(methods):
            ax_matrix.scatter(x, np.full_like(x, yi), s=32, facecolor="#E2E8F0", edgecolor="none", zorder=1)
            active_x = x[combo_plot[method].to_numpy(dtype=bool)]
            ax_matrix.scatter(active_x, np.full_like(active_x, yi), s=54, facecolor="#172033", edgecolor="white", linewidth=0.4, zorder=2)
        for xi, row in combo_plot.iterrows():
            ys = [i for i, method in enumerate(methods) if row[method]]
            if len(ys) > 1:
                ax_matrix.plot([xi, xi], [min(ys), max(ys)], color="#172033", lw=1.1, zorder=1)
        ax_matrix.set_yticks(y_set)
        ax_matrix.set_yticklabels([])
        ax_matrix.tick_params(axis="y", length=0)
        ax_matrix.invert_yaxis()
        ax_matrix.set_xlabel("模型组合")
        ax_matrix.set_xlim(-0.6, len(combo_plot) - 0.4)
        ax_matrix.grid(False)
        sns.despine(ax=ax_matrix, left=True, bottom=True)
        save_fig(fig, "Fig18_anomaly_model_venn")

    high = service[service["final_high_risk"] == 1]
    high_cat = (
        service.groupby("统一服务类别", dropna=False)
        .agg(项目数量=("记录ID", "count"), 高风险项目数量=("final_high_risk", "sum"))
        .reset_index()
    )
    high_cat["统一服务类别"] = high_cat["统一服务类别"].fillna("未识别")
    high_cat["高风险比例"] = high_cat["高风险项目数量"] / high_cat["项目数量"].replace(0, np.nan)
    high_cat = high_cat[high_cat["高风险项目数量"] > 0].sort_values(["高风险项目数量", "高风险比例"], ascending=False).head(15)
    if not high_cat.empty:
        fig, ax = plt.subplots(figsize=(10.6, 6.4))
        sizes = 140 + 980 * high_cat["高风险项目数量"] / max(high_cat["高风险项目数量"].max(), 1)
        sc = ax.scatter(
            high_cat["项目数量"],
            high_cat["高风险比例"],
            s=sizes,
            c=high_cat["高风险比例"],
            cmap=RISK_CMAP,
            edgecolors="white",
            linewidths=0.8,
            alpha=0.88,
        )
        for _, row in high_cat.iterrows():
            label = short_label(row["统一服务类别"], 8)
            if str(row["统一服务类别"]) == "物业管理":
                xytext = (-24, 0)
                ha = "right"
                va = "center"
            else:
                xytext = (5, 4)
                ha = "left"
                va = "baseline"
            ax.annotate(
                label,
                (row["项目数量"], row["高风险比例"]),
                xytext=xytext,
                textcoords="offset points",
                ha=ha,
                va=va,
                fontsize=8.4,
                color=ACADEMIC["ink"],
            )
        ax.axvline(high_cat["项目数量"].median(), color="#94A3B8", linestyle="--", lw=1.0)
        ax.axhline(high_cat["高风险比例"].median(), color="#94A3B8", linestyle="--", lw=1.0)
        ax.set_title("图12 服务类别风险矩阵图", loc="left")
        ax.set_xlabel("项目数量")
        ax.set_ylabel("高风险比例")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        cbar = fig.colorbar(sc, ax=ax, pad=0.015, shrink=0.82)
        cbar.set_label("高风险比例")
        ax.text(0.02, 0.02, "气泡大小表示高风险项目数量；虚线为本图类别中位数", transform=ax.transAxes, fontsize=8.5, color=ACADEMIC["muted"])
        sns.despine(ax=ax)
        save_fig(fig, "Fig19_high_risk_service_category")

    high_prov = (
        service.assign(项目省份=service["项目省份"].fillna("未识别"))
        .groupby("项目省份", dropna=False)
        .agg(项目数量=("记录ID", "count"), 高风险项目数量=("final_high_risk", "sum"))
        .reset_index()
    )
    high_prov["高风险比例"] = high_prov["高风险项目数量"] / high_prov["项目数量"].replace(0, np.nan)
    high_prov = (
        high_prov[high_prov["高风险项目数量"] > 0]
        .sort_values(["高风险比例", "项目数量"], ascending=[False, False])
        .head(15)
    )
    if not high_prov.empty:
        fig, ax = plt.subplots(figsize=(10.4, 5.6))
        x = np.arange(len(high_prov))
        bars = ax.bar(x, high_prov["高风险比例"], color="#B86B1A", width=0.62)
        ymax = max(high_prov["高风险比例"].max(), 0.01)
        ax.set_ylim(0, ymax * 1.18)
        for bar, value in zip(bars, high_prov["高风险比例"]):
            ax.annotate(
                f"{value:.1%}",
                xy=(bar.get_x() + bar.get_width() / 2, value),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.6,
                color=ACADEMIC["ink"],
            )
        ax.set_xticks(x)
        ax.set_xticklabels(high_prov["项目省份"], rotation=30, ha="right")
        ax.set_xlabel("项目省份")
        ax.set_ylabel("高风险比例")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.set_title("图13 省份高风险比例Top15条形图", loc="left")
        sns.despine(ax=ax)
        save_fig(fig, "Fig20_high_risk_province")

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
    if HAS_STATSMODELS:
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
    else:
        # Fallback: use sklearn LogisticRegression coefficients
        from sklearn.linear_model import LogisticRegression as _LogReg
        logit_cols_present = [c for c in logit_cols if c in compact.columns]
        X_logit_sk = compact[logit_cols_present].values
        y_logit_sk = compact[target].astype(int).values
        lr = _LogReg(max_iter=1200, class_weight="balanced", random_state=RANDOM_STATE)
        lr.fit(X_logit_sk, y_logit_sk)
        logistic_table = pd.DataFrame(
            {
                "变量": ["const"] + logit_cols_present,
                "系数": [lr.intercept_[0]] + list(lr.coef_[0]),
                "标准误": np.nan,
                "z值": np.nan,
                "p值": np.nan,
                "优势比OR": np.exp([lr.intercept_[0]] + list(lr.coef_[0])),
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
    model_palette = {
        "Logistic": "#4E79A7",
        "Random Forest": "#59A14F",
        "XGBoost": "#E15759",
    }
    sns.barplot(data=eval_long, x="指标", y="得分", hue="模型", palette=model_palette, ax=ax)
    ax.set_title("图22 模型评价指标对比图（注：AUC高源于风险标签结构清晰，不等同于真实违法识别能力）", loc="left")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("")
    ax.set_ylabel("得分")
    ax.legend(title="模型", loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0, frameon=True)
    fig.subplots_adjust(right=0.80)
    sns.despine(ax=ax)
    save_fig(fig, "Fig22_supervised_model_metrics")

    for table, title, fname, colors in [
        (
            rf_importance.head(15).sort_values("重要性", ascending=True),
            "图23 Random Forest变量重要性图",
            "Fig23_random_forest_importance",
            gradient_palette("#D9EEF2", "#005F73", 15),
        ),
        (
            xgb_importance.head(15).sort_values("重要性", ascending=True),
            "图24 XGBoost变量重要性图",
            "Fig24_xgboost_importance",
            gradient_palette("#E7E0F4", "#4B3F72", 15),
        ),
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
            color=colors,
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
    selected = selected.sort_values(["一致性", "覆盖度", "高风险案例数"], ascending=False).head(4)
    paths = []
    for i, row in selected.reset_index(drop=True).iterrows():
        present = [cond for cond in conditions if row[cond] == 1]
        absent = [f"非{cond}" for cond in conditions if row[cond] == 0 and cond in ["公开招标", "跨省中标"]]
        path_text = " × ".join([*present, *absent]) if present or absent else "无显著条件组合"
        paths.append(
            {
                "路径编号": f"路径{i+1}",
                "风险线索组合": path_text,
                "案例数": int(row["案例数"]),
                "高风险案例数": int(row["高风险案例数"]),
                "一致性": row["一致性"],
                "覆盖度": row["覆盖度"],
            }
        )
    qca_paths = pd.DataFrame(paths)

    heat_conditions = ["高节约率", "低价格比例", "高频供应商", "跨省中标", "高财政压力", "公开招标", "高风险服务类别"]
    matrix = selected.reset_index(drop=True)[heat_conditions].to_numpy(dtype=float)
    fig = plt.figure(figsize=(11.2, 6.2))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[4.8, 1.45], wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    ax_bar = fig.add_subplot(gs[0, 1])
    cmap = ListedColormap(["#EEF2F7", "#0A9396"])
    ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    heat_condition_labels = ["高节约率", "低价格\n比例", "高频\n供应商", "跨省\n中标", "高财政\n压力", "公开\n招标", "高风险\n服务类别"]
    ax.set_xticks(np.arange(len(heat_conditions)))
    ax.set_xticklabels(heat_condition_labels, rotation=0, ha="center", fontsize=8.8, linespacing=1.15)
    ax.tick_params(axis="x", pad=8)
    ax.set_yticks(np.arange(len(qca_paths)))
    ax.set_yticklabels(qca_paths["路径编号"])
    ax.set_title("图15 QCA风险线索组合热力矩阵图", loc="left", pad=12)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, "存在" if matrix[i, j] else "缺失", ha="center", va="center", fontsize=8.2, color="white" if matrix[i, j] else ACADEMIC["muted"])
    ax.set_xticks(np.arange(-0.5, len(heat_conditions), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(qca_paths), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    y = np.arange(len(qca_paths))
    height = 0.34
    ax_bar.barh(y - height / 2, qca_paths["一致性"], height=height, color="#D55E00", alpha=0.84, label="一致性")
    ax_bar.barh(y + height / 2, qca_paths["覆盖度"], height=height, color="#4E79A7", alpha=0.84, label="覆盖度")
    for yi, row in qca_paths.iterrows():
        ax_bar.text(row["一致性"] + 0.02, yi - height / 2, f"{row['一致性']:.2f}", va="center", fontsize=8.2)
        ax_bar.text(row["覆盖度"] + 0.02, yi + height / 2, f"{row['覆盖度']:.2f}", va="center", fontsize=8.2)
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels([])
    ax_bar.invert_yaxis()
    ax_bar.set_xlim(0, max(1.0, float(qca_paths["一致性"].max()) * 1.18))
    ax_bar.set_xlabel("指标值")
    ax_bar.legend(loc="lower right")
    sns.despine(ax=ax_bar, left=True)
    fig.subplots_adjust(bottom=0.20)
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
    supplier_rank["备注"] = supplier_rank["项目数量"].map(lambda n: "样本量较小，高风险比例仅供参考" if n < 5 else "")
    buyer_rank = (
        centrality[(centrality["节点类型"] == "采购人") & (centrality["项目数量"] >= 2)]
        .sort_values(["高风险比例", "高风险项目数量", "项目数量"], ascending=False)
        .head(50)
        [["主体名称", "项目数量", "高风险项目数量", "高风险比例", "加权度", "度中心性", "介数中心性", "特征向量中心性", "平均风险分", "主服务类别", "社群"]]
    )
    buyer_rank["备注"] = buyer_rank["项目数量"].map(lambda n: "样本量较小，高风险比例仅供参考，不构成违法认定" if n < 5 else "")

    draw_network_figures(G, centrality, edge_df, community_table)
    return supplier_rank, buyer_rank, community_table


def draw_network_figures(G: nx.Graph, centrality: pd.DataFrame, edge_df: pd.DataFrame, community_table: pd.DataFrame) -> None:
    centrality_idx = centrality.set_index("node")

    def node_rank(node: str) -> float:
        if node not in centrality_idx.index:
            return 0.0
        row = centrality_idx.loc[node]
        return (
            4.5 * float(row.get("高风险项目数量", 0) or 0)
            + 2.0 * float(row.get("特征向量中心性", 0) or 0)
            + 0.9 * math.log1p(float(row.get("加权度", 0) or 0))
            + 1.2 * float(row.get("平均风险分", 0) or 0)
        )

    def subgraph_by_nodes(nodes: list[str], max_nodes: int, max_edges: int, focus_risk: bool = False) -> nx.Graph:
        seed_nodes = set(nodes[: max_nodes * 2])
        candidates = []
        for u, v, data in G.edges(data=True):
            if u not in seed_nodes and v not in seed_nodes:
                continue
            weight = float(data.get("weight", 1) or 1)
            risk_count = float(data.get("risk_count", 0) or 0)
            avg_score = float(data.get("avg_score", 0) or 0)
            score = (
                node_rank(u)
                + node_rank(v)
                + 0.8 * math.log1p(weight)
                + (8.0 if focus_risk else 3.5) * risk_count
                + (2.0 if focus_risk else 0.8) * avg_score
            )
            candidates.append((score, u, v))
        if not candidates and G.number_of_edges() > 0:
            candidates = [
                (
                    float(data.get("risk_count", 0) or 0) * 8 + math.log1p(float(data.get("weight", 1) or 1)),
                    u,
                    v,
                )
                for u, v, data in G.edges(data=True)
            ]
        chosen_edges = [(u, v) for _, u, v in sorted(candidates, reverse=True)[:max_edges]]
        sub = G.edge_subgraph(chosen_edges).copy()
        if sub.number_of_nodes() > max_nodes:
            keep = sorted(
                sub.nodes(),
                key=lambda n: (node_rank(n), sub.degree(n, weight="weight")),
                reverse=True,
            )[:max_nodes]
            sub = sub.subgraph(keep).copy()
        sub.remove_nodes_from(list(nx.isolates(sub)))
        return sub

    top_nodes = (
        centrality.sort_values(["高风险项目数量", "特征向量中心性", "加权度"], ascending=False)["node"].head(220).tolist()
    )
    sub = subgraph_by_nodes(top_nodes, max_nodes=190, max_edges=260)
    draw_one_network(sub, "图28 采购关系网络总体图（核心节点）", "Fig28_procurement_relation_network", centrality_idx)

    draw_bipartite_risk_network(edge_df, centrality_idx, "图16 高风险供应商—采购人二部网络简化图", "Fig29_high_risk_supplier_buyer_network")

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
        "图31 采购单位高风险比例 Top 20（重点复核线索，非违法认定）",
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
        draw_community_network(comm_sub, community_table, "图31 风险社群网络图", "Fig32_risk_community_network")


def _normalise_positions(pos: dict[object, np.ndarray]) -> dict[object, np.ndarray]:
    coords = np.array(list(pos.values()), dtype=float)
    if coords.size == 0:
        return pos
    centre = coords.mean(axis=0)
    coords = coords - centre
    span = np.abs(coords).max()
    span = span if span > 0 else 1.0
    nodes = list(pos.keys())
    return {node: coords[i] / span for i, node in enumerate(nodes)}


def _component_layout(graph: nx.Graph) -> dict[str, np.ndarray]:
    components = [graph.subgraph(c).copy() for c in sorted(nx.connected_components(graph), key=len, reverse=True)]
    if not components:
        return {}
    if len(components) == 1:
        return _normalise_positions(
            nx.spring_layout(components[0], seed=RANDOM_STATE, k=0.75, iterations=260, weight="weight")
        )

    positions: dict[str, np.ndarray] = {}
    max_size = max(1, components[0].number_of_nodes())
    anchors = [(0.0, 0.0)]
    for i in range(1, len(components)):
        ring = 1 + (i - 1) // 8
        angle = 2 * math.pi * ((i - 1) % 8) / 8 + ring * 0.18
        radius = 1.45 + 0.55 * (ring - 1)
        anchors.append((radius * math.cos(angle), radius * math.sin(angle)))

    for i, comp in enumerate(components):
        if comp.number_of_nodes() == 1:
            local = {next(iter(comp.nodes())): np.array([0.0, 0.0])}
        else:
            local = _normalise_positions(
                nx.spring_layout(comp, seed=RANDOM_STATE + i, k=0.85, iterations=240, weight="weight")
            )
        scale = 0.95 * math.sqrt(comp.number_of_nodes() / max_size)
        scale = float(np.clip(scale, 0.22, 1.05))
        anchor = np.array(anchors[i])
        for node, xy in local.items():
            positions[node] = anchor + np.array(xy) * scale
    return _normalise_positions(positions)


def draw_community_network(comm_sub: nx.Graph, community_table: pd.DataFrame, title: str, fname: str) -> None:
    comm_info = community_table.set_index("社群")
    nodes_order = sorted(
        list(comm_sub.nodes()),
        key=lambda n: (
            float(comm_info.loc[n, "高风险比例"]) if n in comm_info.index and pd.notna(comm_info.loc[n, "高风险比例"]) else 0,
            float(comm_info.loc[n, "关联项目数量"]) if n in comm_info.index else 0,
        ),
        reverse=True,
    )
    if comm_sub.number_of_edges() > 0:
        pos = _normalise_positions(nx.spring_layout(comm_sub, seed=RANDOM_STATE, k=0.95, iterations=220, weight="weight"))
    else:
        pos = {}
        for i, node in enumerate(nodes_order):
            angle = i * math.radians(137.5)
            radius = 0.03 + 0.075 * math.sqrt(i)
            pos[node] = np.array([radius * math.cos(angle), radius * math.sin(angle)])

    fig, ax = plt.subplots(figsize=(10.2, 7.0))
    ax.set_facecolor("#FBFCFE")
    risk_values = [
        float(comm_info.loc[n, "高风险比例"]) if n in comm_info.index and pd.notna(comm_info.loc[n, "高风险比例"]) else 0
        for n in nodes_order
    ]
    vmax = max(1.0, np.nanmax(risk_values) if risk_values else 1.0)
    community_cmap = LinearSegmentedColormap.from_list(
        "community_blue_purple_risk", ["#DBEAFE", "#93C5FD", "#8B5CF6", "#B91C1C"]
    )
    widths = [0.65 + 0.26 * math.log1p(float(d.get("weight", 1) or 1)) for _, _, d in comm_sub.edges(data=True)]
    if comm_sub.number_of_edges() > 0:
        nx.draw_networkx_edges(comm_sub, pos, ax=ax, width=widths, edge_color="#94A3B8", alpha=0.26)
    sizes = [
        90 + 24 * math.sqrt(float(comm_info.loc[n, "节点数量"]) if n in comm_info.index else 1)
        + 3.2 * math.sqrt(float(comm_info.loc[n, "关联项目数量"]) if n in comm_info.index else 1)
        for n in nodes_order
    ]
    nx.draw_networkx_nodes(
        comm_sub,
        pos,
        nodelist=nodes_order,
        node_size=[s * 1.18 for s in sizes],
        node_color="#0F172A",
        alpha=0.08,
        linewidths=0,
        ax=ax,
    )
    drawn = nx.draw_networkx_nodes(
        comm_sub,
        pos,
        nodelist=nodes_order,
        node_size=sizes,
        node_color=risk_values,
        cmap=community_cmap,
        vmin=0,
        vmax=vmax,
        linewidths=0.9,
        edgecolors="#1E293B",
        alpha=0.94,
        ax=ax,
    )
    label_nodes = nodes_order[:12]
    labels = {n: f"C{i:02d}" for i, n in enumerate(label_nodes, start=1)}
    nx.draw_networkx_labels(
        comm_sub,
        pos,
        labels=labels,
        font_size=8.0,
        font_color=ACADEMIC["ink"],
        font_weight="semibold",
        bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "#E2E8F0", "alpha": 0.86},
        ax=ax,
    )
    cbar = fig.colorbar(drawn, ax=ax, fraction=0.030, pad=0.018, shrink=0.78)
    cbar.set_label("社群高风险比例", color=ACADEMIC["ink"])
    cbar.outline.set_edgecolor("#CBD5E1")
    ax.set_title(title, loc="left", pad=12)
    ax.text(
        0.02,
        0.02,
        "节点大小表示社群规模；C编号表示风险社群排序；颜色越深表示高风险项目占比越高",
        transform=ax.transAxes,
        fontsize=8.5,
        color=ACADEMIC["muted"],
    )
    ax.set_xlim(-0.72, 0.72)
    ax.set_ylim(-0.62, 0.62)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    save_fig(fig, fname)


def draw_bipartite_risk_network(edge_df: pd.DataFrame, centrality_idx: pd.DataFrame, title: str, fname: str) -> None:
    risk_edges = edge_df[pd.to_numeric(edge_df["risk_count"], errors="coerce").fillna(0) > 0].copy()
    if risk_edges.empty:
        return
    node_stats = centrality_idx.copy()
    node_stats["高风险项目数量"] = pd.to_numeric(node_stats["高风险项目数量"], errors="coerce").fillna(0)
    supplier_keep = (
        node_stats[node_stats["节点类型"] == "供应商"]
        .sort_values(["高风险项目数量", "项目数量"], ascending=False)
        .head(12)
        .index
        .tolist()
    )
    buyer_keep = (
        node_stats[node_stats["节点类型"] == "采购人"]
        .sort_values(["高风险项目数量", "项目数量"], ascending=False)
        .head(12)
        .index
        .tolist()
    )
    plot_edges = risk_edges[
        risk_edges["_supplier_node"].isin(supplier_keep) & risk_edges["_buyer_node"].isin(buyer_keep)
    ].copy()
    if len(plot_edges) < 5:
        plot_edges = risk_edges[
            risk_edges["_supplier_node"].isin(supplier_keep) | risk_edges["_buyer_node"].isin(buyer_keep)
        ].copy()
        supplier_keep = (
            plot_edges.groupby("_supplier_node")["risk_count"].sum().sort_values(ascending=False).head(12).index.tolist()
        )
        buyer_keep = (
            plot_edges.groupby("_buyer_node")["risk_count"].sum().sort_values(ascending=False).head(12).index.tolist()
        )
        plot_edges = plot_edges[
            plot_edges["_supplier_node"].isin(supplier_keep) & plot_edges["_buyer_node"].isin(buyer_keep)
        ].copy()
    if len(plot_edges) < 10:
        broader_edges = risk_edges.sort_values(["risk_count", "weight"], ascending=False).head(60).copy()
        supplier_keep = (
            broader_edges.groupby("_supplier_node")["risk_count"].sum().sort_values(ascending=False).head(12).index.tolist()
        )
        buyer_keep = (
            broader_edges.groupby("_buyer_node")["risk_count"].sum().sort_values(ascending=False).head(12).index.tolist()
        )
        plot_edges = broader_edges[
            broader_edges["_supplier_node"].isin(supplier_keep) & broader_edges["_buyer_node"].isin(buyer_keep)
        ].copy()
    plot_edges = plot_edges.sort_values(["risk_count", "weight"], ascending=False).head(36)
    if plot_edges.empty:
        return

    suppliers = [node for node in supplier_keep if node in set(plot_edges["_supplier_node"])]
    buyers = [node for node in buyer_keep if node in set(plot_edges["_buyer_node"])]
    suppliers = sorted(suppliers, key=lambda n: node_stats.loc[n, "高风险项目数量"] if n in node_stats.index else 0, reverse=True)
    buyers = sorted(buyers, key=lambda n: node_stats.loc[n, "高风险项目数量"] if n in node_stats.index else 0, reverse=True)

    def y_positions(nodes: list[str]) -> dict[str, float]:
        if len(nodes) == 1:
            return {nodes[0]: 0.5}
        return {node: y for node, y in zip(nodes, np.linspace(0.92, 0.08, len(nodes)))}

    pos = {node: (0.32, y) for node, y in y_positions(suppliers).items()}
    pos.update({node: (0.68, y) for node, y in y_positions(buyers).items()})
    max_node_risk = max(node_stats.loc[list(pos.keys()), "高风险项目数量"].max(), 1)
    max_edge_weight = max(float(plot_edges["weight"].max()), 1)

    fig, ax = plt.subplots(figsize=(13.2, 7.8))
    ax.set_facecolor("#FBFCFE")
    for _, row in plot_edges.iterrows():
        u, v = row["_supplier_node"], row["_buyer_node"]
        if u not in pos or v not in pos:
            continue
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        width = 0.8 + 3.1 * math.log1p(float(row["weight"])) / math.log1p(max_edge_weight)
        alpha = 0.28 + 0.34 * min(float(row["risk_count"]) / max(float(plot_edges["risk_count"].max()), 1), 1)
        ax.plot([x1, x2], [y1, y2], color="#D55E00", lw=width, alpha=alpha, solid_capstyle="round", zorder=1)

    for nodes, x, color, marker, name_x, align, label in [
        (suppliers, 0.32, "#2A9D8F", "o", 0.27, "right", "供应商"),
        (buyers, 0.68, "#F2B84B", "s", 0.72, "left", "采购人"),
    ]:
        for node in nodes:
            _, y = pos[node]
            risk_count = float(node_stats.loc[node, "高风险项目数量"]) if node in node_stats.index else 0
            size = 170 + 980 * math.sqrt(risk_count / max_node_risk)
            ax.scatter(x, y, s=size * 1.12, color="#0F172A", alpha=0.08, marker=marker, linewidth=0, zorder=2)
            ax.scatter(x, y, s=size, color=color, edgecolor="#1F2937", linewidth=0.75, marker=marker, alpha=0.94, zorder=3)
            name = str(node_stats.loc[node, "主体名称"]) if node in node_stats.index else re.sub(r"^[SB]\|", "", node)
            ax.text(name_x, y, textwrap.fill(name, 18), ha=align, va="center", fontsize=7.4, color=ACADEMIC["ink"], zorder=4, linespacing=1.15)
            ax.text(x, y, f"{int(risk_count)}", ha="center", va="center", fontsize=7.2, color="white", weight="bold", zorder=5)

    ax.text(0.32, 0.985, "高风险供应商Top 12", ha="center", va="bottom", fontsize=10, weight="bold", color=ACADEMIC["header"])
    ax.text(0.68, 0.985, "高风险采购人Top 12", ha="center", va="bottom", fontsize=10, weight="bold", color=ACADEMIC["header"])
    ax.set_title(title, loc="left", pad=12)
    ax.set_xlim(0, 1.06)
    ax.set_ylim(-0.02, 1.03)
    ax.axis("off")
    save_fig(fig, fname)


def draw_one_network(sub: nx.Graph, title: str, fname: str, centrality_idx: pd.DataFrame | None = None) -> None:
    if sub.number_of_nodes() == 0:
        return
    pos = _component_layout(sub)
    fig, ax = plt.subplots(figsize=(11.2, 8.2))
    ax.set_facecolor("#FBFCFE")
    normal_edges = [(u, v) for u, v, d in sub.edges(data=True) if float(d.get("risk_count", 0) or 0) <= 0]
    risk_edges = [(u, v) for u, v, d in sub.edges(data=True) if float(d.get("risk_count", 0) or 0) > 0]
    normal_width = [0.35 + 0.24 * math.log1p(float(sub[u][v].get("weight", 1) or 1)) for u, v in normal_edges]
    risk_width = [0.65 + 0.34 * math.log1p(float(sub[u][v].get("risk_count", 1) or 1)) for u, v in risk_edges]
    nx.draw_networkx_edges(sub, pos, edgelist=normal_edges, ax=ax, width=normal_width, edge_color="#CBD5E1", alpha=0.34)
    nx.draw_networkx_edges(sub, pos, edgelist=risk_edges, ax=ax, width=risk_width, edge_color="#E76F51", alpha=0.45)
    node_type = nx.get_node_attributes(sub, "node_type")
    for ntype, color, marker in [("供应商", "#2A9D8F", "o"), ("采购人", "#F2B84B", "s")]:
        nodes = [n for n in sub.nodes() if node_type.get(n) == ntype]
        sizes = []
        for n in nodes:
            strength = float(sub.degree(n, weight="weight") or 0)
            risk_bonus = 0.0
            if centrality_idx is not None and n in centrality_idx.index:
                risk_bonus = 36.0 * float(centrality_idx.loc[n].get("高风险比例", 0) or 0)
            sizes.append(float(np.clip(58 + 30 * math.sqrt(strength) + risk_bonus, 58, 360)))
        nx.draw_networkx_nodes(
            sub,
            pos,
            nodelist=nodes,
            node_size=[s * 1.22 for s in sizes],
            node_color="#0F172A",
            node_shape=marker,
            alpha=0.08,
            linewidths=0,
            ax=ax,
        )
        nx.draw_networkx_nodes(
            sub,
            pos,
            nodelist=nodes,
            node_size=sizes,
            node_color=color,
            node_shape=marker,
            alpha=0.92,
            linewidths=0.7,
            edgecolors="#1F2937",
            label=ntype,
            ax=ax,
        )
    def label_score(node: str) -> float:
        score = math.log1p(float(sub.degree(node, weight="weight") or 0))
        if centrality_idx is not None and node in centrality_idx.index:
            row = centrality_idx.loc[node]
            score += 5 * float(row.get("高风险项目数量", 0) or 0)
            score += 2 * float(row.get("特征向量中心性", 0) or 0)
        return score

    top_labels = sorted(sub.nodes(), key=label_score, reverse=True)[:10]
    labels = {
        n: f"{'S' if node_type.get(n) == '供应商' else 'B'}{i:02d}"
        for i, n in enumerate(top_labels, start=1)
    }
    nx.draw_networkx_labels(
        sub,
        pos,
        labels=labels,
        font_size=7.6,
        font_color=ACADEMIC["ink"],
        bbox={"boxstyle": "round,pad=0.16", "fc": "white", "ec": "#E2E8F0", "alpha": 0.84},
        ax=ax,
    )
    ax.set_title(title, loc="left", pad=12)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#2A9D8F", markeredgecolor="#1F2937", markersize=8, label="供应商"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#F2B84B", markeredgecolor="#1F2937", markersize=8, label="采购人"),
        Line2D([0], [0], color="#E76F51", lw=1.6, alpha=0.8, label="含高风险项目边"),
    ]
    ax.legend(handles=handles, loc="upper right", frameon=True, borderpad=0.8, labelspacing=0.65)
    ax.text(
        0.02,
        0.02,
        "节点大小表示交易强度；S为供应商、B为采购人；仅标注核心主体",
        transform=ax.transAxes,
        fontsize=8.5,
        color=ACADEMIC["muted"],
    )
    ax.set_xlim(-1.08, 1.08)
    ax.set_ylim(-1.08, 1.08)
    ax.set_aspect("equal", adjustable="box")
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
    sns.barplot(data=sc, x="样本类型", y="规则高风险比例", palette=["#2F5D8C", "#8F4C5C"], ax=ax)
    for p in ax.patches:
        ax.text(p.get_x() + p.get_width() / 2, p.get_height(), f"{p.get_height():.1%}", ha="center", va="bottom", fontsize=9)
    max_height = max((p.get_height() for p in ax.patches), default=0)
    if max_height > 0:
        ax.set_ylim(0, max_height * 1.16)
    ax.set_title("图32 主样本与扩展样本风险率对比图（扩展样本缺少部分供应商和代理机构字段，未复现主模型，仅用于规则与类别差异验证）", loc="left")
    ax.set_ylabel("规则高风险比例")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    sns.despine(ax=ax)
    save_fig(fig, "Fig33_main_vs_extension_risk_rate")

    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    category_plot = category_risk.sort_values("高风险比例", ascending=False).copy()
    x = np.arange(len(category_plot))
    setattr(ax, "_codex_grid_axis", "x")
    ax.set_axisbelow(True)
    ax.grid(False, axis="y")
    ax.grid(True, axis="x", color="#E5E7EB", linewidth=0.8, zorder=0)
    bars = ax.bar(x, category_plot["高风险比例"], color="#005F73", alpha=1.0, width=0.58, label="高风险比例", zorder=3)
    for bar, value in zip(bars, category_plot["高风险比例"]):
        ax.annotate(
            f"{value:.1%}",
            xy=(bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.8,
            color="#005F73",
            weight="bold",
            clip_on=False,
            zorder=5,
        )
    ax2 = ax.twinx()
    setattr(ax2, "_codex_grid_axis", "none")
    ax2.patch.set_visible(False)
    ax2.grid(False)
    ax2.plot(x, category_plot["项目数量"], color="#D55E00", marker="o", lw=2.0, label="样本量", zorder=4)
    sample_max = max(category_plot["项目数量"].max(), 1)
    ax2.set_ylim(0, sample_max * 1.18)
    for idx, (xi, value) in enumerate(zip(x, category_plot["项目数量"])):
        x_offset = -12 if idx == len(x) - 1 else 12
        text_align = "right" if idx == len(x) - 1 else "left"
        ax2.annotate(
            f"{int(value)}",
            xy=(xi, value),
            xytext=(x_offset, 9),
            textcoords="offset points",
            ha=text_align,
            va="bottom",
            fontsize=8.2,
            color="#D55E00",
            bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.75},
        )
    ax.set_xticks(x)
    ax.set_xticklabels(category_plot["采购大类"])
    ax.set_ylabel("高风险比例")
    ax2.set_ylabel("样本量")
    ax2.grid(False, which="both", axis="both")
    for gridline in ax2.get_xgridlines() + ax2.get_ygridlines():
        gridline.set_visible(False)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("图18 不同采购大类风险率与样本量对比图", loc="left")
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, loc="upper right")
    sns.despine(ax=ax)
    sns.despine(ax=ax2, right=False)
    save_fig(fig, "Fig34_category_risk_rate_comparison")

    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    fixed_counts = threshold_table[threshold_table["阈值类型"] == "固定阈值"].copy()
    quantile_counts = threshold_table[threshold_table["阈值类型"] == "同类别分位数"].copy()
    fixed_counts["顺序"] = fixed_counts["阈值设置"].str.extract(r"([0-9]+\.[0-9]+)")[0].astype(float)
    quantile_counts["顺序"] = quantile_counts["阈值设置"].str.extract(r"([0-9]+)")[0].astype(float)
    fixed_counts = fixed_counts.sort_values("顺序")
    quantile_counts = quantile_counts.sort_values("顺序")
    x = np.arange(min(len(fixed_counts), len(quantile_counts)))
    ax.axvspan(0.75, 1.25, color="#F0E6A6", alpha=0.35, label="推荐阈值区域")
    ax.plot(x, fixed_counts["识别数量"].iloc[: len(x)], marker="o", lw=2.2, color="#AE2012", label="固定阈值规则")
    ax.plot(x, quantile_counts["识别数量"].iloc[: len(x)], marker="s", lw=2.2, color="#005F73", label="类别分位数规则")
    for xi, value in zip(x, fixed_counts["识别数量"].iloc[: len(x)]):
        ax.text(xi, value, f"{int(value)}", ha="center", va="bottom", fontsize=8.4, color="#AE2012")
    for xi, value in zip(x, quantile_counts["识别数量"].iloc[: len(x)]):
        ax.text(xi, value, f"{int(value)}", ha="center", va="bottom", fontsize=8.4, color="#005F73")
    labels = []
    for _, fixed_row in fixed_counts.iloc[: len(x)].iterrows():
        q_row = quantile_counts.iloc[len(labels)]
        labels.append(f"{fixed_row['阈值设置'].replace('price_ratio < ', '')}\n{q_row['阈值设置']}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("图19 异常低价阈值敏感性曲线图", loc="left")
    ax.set_xlabel("阈值设置（上：固定阈值；下：类别分位数）")
    ax.set_ylabel("识别数量")
    ax.legend(loc="upper left")
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
        color=gradient_palette("#F1D7B5", "#9A5B12", len(ext_high)),
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
        f"- XGBoost 测试集 AUC：{summary['xgb_auc']:.3f}；F1：{summary['xgb_f1']:.3f}。（注：目标变量来源于规则风险与异常检测标签，AUC高说明模型能学习风险标签结构，不等同于真实违法识别能力。）",
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
