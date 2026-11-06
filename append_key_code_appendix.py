from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt


INPUT_DOCX = Path(
    r"C:\Users\22672\Desktop\基于文本挖掘与异常检测的政府采购异常低价中标风险识别研究_写作形式精简修订版.docx"
)
OUTPUT_DOCX = Path(
    r"C:\Users\22672\Desktop\基于文本挖掘与异常检测的政府采购异常低价中标风险识别研究_关键代码附录版.docx"
)

CODE_FONT = "Courier New"
# Word 中文字号“六号”约等于 7.5 pt。
CODE_SIZE = Pt(7.5)


APPENDIX_BLOCKS = [
    (
        "A.1 数据读取、格式统一与输出目录管理",
        r'''# 来源：00_common/pipeline_core.py
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "输出结果"
TABLE_DIR = OUT_DIR / "tables"
DATA_DIR = OUT_DIR / "data"
FIG_DIR = OUT_DIR / "figures"

def ensure_dirs() -> None:
    """创建统一输出目录，保证表格、数据和图像可以复现写入。"""
    for path in [OUT_DIR, TABLE_DIR, DATA_DIR, FIG_DIR]:
        path.mkdir(parents=True, exist_ok=True)

def read_table(name: str) -> pd.DataFrame:
    """读取清洗后的样本表，并将价格、宏观指标、规则标签转换为数值型。"""
    path = BASE_DIR / FILES[name]
    frame = pd.read_csv(path, encoding="utf-8-sig")
    numeric_cols = [
        "预算金额", "中标金额", "中标/预算比例", "节约率",
        "price_ratio_clean", "saving_rate_clean", "log_budget", "log_bid",
        "rule_risk_score", "is_suspicious_low_price", "is_high_risk_low_price",
        "gdp_per_capita", "fiscal_pressure", "average_wage",
        "tertiary_industry_share", "urbanization_rate",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in RULE_COLS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)
    return frame

def save_table(frame: pd.DataFrame, name: str) -> Path:
    """保存论文表格所需 CSV，统一使用 utf-8-sig 便于 Word 和 Excel 识别中文。"""
    path = TABLE_DIR / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path''',
    ),
    (
        "A.2 异常低价规则标签构造",
        r'''# 来源：00_common/pipeline_core.py
import numpy as np

def add_recalculated_rules(frame: pd.DataFrame, group_col: str = "统一服务类别") -> pd.DataFrame:
    """按政策阈值、类别分位数、IQR 和稳健 Z 分数生成异常低价规则标签。"""
    df = frame.copy()
    ratio = pd.to_numeric(df["price_ratio_clean"], errors="coerce")
    group = df[group_col].fillna("未识别")

    # 当某一服务类别样本量不足时，使用全样本分位数作为稳健回退值。
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
    ).replace(0, global_mad).fillna(global_mad)

    iqr_low = (q1 - 1.5 * (q3 - q1)).fillna(global_iqr_low)
    robust_z = (ratio - med) / (1.4826 * mad)

    df["calc_rule_policy_65"] = (ratio < 0.65).fillna(False).astype(int)
    df["calc_rule_quantile_10"] = (ratio <= q10).fillna(False).astype(int)
    df["calc_rule_quantile_5"] = (ratio <= q05).fillna(False).astype(int)
    df["calc_rule_iqr"] = (ratio < iqr_low).fillna(False).astype(int)
    df["calc_rule_robust_z"] = (robust_z < -3.5).fillna(False).astype(int)

    calc_cols = [
        "calc_rule_policy_65", "calc_rule_quantile_10", "calc_rule_quantile_5",
        "calc_rule_iqr", "calc_rule_robust_z",
    ]
    df["calc_rule_risk_score"] = df[calc_cols].sum(axis=1)
    df["calc_is_suspicious_low_price"] = (df["calc_rule_risk_score"] >= 1).astype(int)
    df["calc_is_high_risk_low_price"] = (df["calc_rule_risk_score"] >= 3).astype(int)
    return df''',
    ),
    (
        "A.3 文本合并、分词与主题特征提取",
        r'''# 来源：00_common/pipeline_core.py
import re
import jieba
from collections import Counter
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

def combine_text(frame: pd.DataFrame) -> pd.Series:
    """将标题、项目名称、公告正文、服务类别和采购方式拼接为统一文本字段。"""
    cols = [c for c in ["公告标题", "项目名称", "公告正文", "统一服务类别", "采购方式标准化"] if c in frame.columns]
    text_parts = []
    for col in cols:
        s = frame[col].fillna("").astype(str)
        if col == "公告正文":
            s = s.str.slice(0, 9000)  # 控制超长公告正文对分词和向量化的影响。
        text_parts.append(s)
    return pd.concat(text_parts, axis=1).agg(" ".join, axis=1)

def tokenize_cn(text: str) -> str:
    """保留中文、英文和数字，去除停用词、单字词和低信息数字串。"""
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", str(text))
    tokens = []
    for word in jieba.lcut(text):
        word = word.strip()
        if len(word) < 2 or word in STOPWORDS or word.isdigit():
            continue
        if re.fullmatch(r"[A-Za-z0-9]+", word) and len(word) < 3:
            continue
        tokens.append(word)
    return " ".join(tokens)

def text_and_topic_model(service: pd.DataFrame, full: pd.DataFrame, font_path: Path | None):
    """生成文本长度、TF-IDF 主成分、LDA 主题概率和关键词统计表。"""
    service = service.copy()
    service["text_all"] = combine_text(service)
    service["text_length"] = service["text_all"].str.len()
    service["tokenized_text"] = service["text_all"].map(tokenize_cn)

    all_tokens = " ".join(service["tokenized_text"].fillna("")).split()
    high_tokens = " ".join(
        service.loc[service["is_high_risk_low_price"] == 1, "tokenized_text"].fillna("")
    ).split()
    keyword_table = pd.DataFrame(Counter(all_tokens).most_common(80), columns=["关键词", "词频"])
    high_keyword_table = pd.DataFrame(Counter(high_tokens).most_common(80), columns=["关键词", "高风险词频"])

    tfidf = TfidfVectorizer(max_features=600, min_df=3, max_df=0.88)
    tfidf_matrix = tfidf.fit_transform(service["tokenized_text"].fillna(""))
    svd = TruncatedSVD(n_components=min(24, max(2, tfidf_matrix.shape[1] - 1)), random_state=42)
    for i, values in enumerate(svd.fit_transform(tfidf_matrix).T, start=1):
        service[f"tfidf_pc{i}"] = values

    count_vec = CountVectorizer(max_features=1000, min_df=3, max_df=0.88)
    count_matrix = count_vec.fit_transform(service["tokenized_text"].fillna(""))
    lda = LatentDirichletAllocation(n_components=6, learning_method="batch", max_iter=25, random_state=42)
    topic_dist = lda.fit_transform(count_matrix)
    service[[f"lda_topic_prob_{i+1}" for i in range(6)]] = topic_dist
    service["lda_topic"] = topic_dist.argmax(axis=1) + 1
    return service, keyword_table, high_keyword_table''',
    ),
    (
        "A.4 供应商画像特征构造",
        r'''# 来源：00_common/pipeline_core.py
from sklearn.preprocessing import MinMaxScaler

def add_supplier_profile(frame: pd.DataFrame, high_risk_col: str = "is_high_risk_low_price"):
    """按统一供应商名称汇总历史中标、低价中标、跨省中标和类别广度。"""
    df = frame.copy()
    supplier = df["统一供应商名称"].fillna("供应商缺失").astype(str).str.strip().replace("", "供应商缺失")
    df["_supplier"] = supplier
    cross = df.get("是否跨省中标", pd.Series(["否"] * len(df))).fillna("否").astype(str)
    df["_cross_province"] = cross.str.contains("是|1|true|True", regex=True).astype(int)

    supplier_profile = (
        df.groupby("_supplier", dropna=False)
        .agg(
            supplier_win_count=("记录ID", "count"),
            supplier_low_price_count=(high_risk_col, "sum"),
            supplier_suspicious_count=("is_suspicious_low_price", "sum"),
            supplier_avg_saving_rate=("saving_rate_clean", "mean"),
            supplier_avg_price_ratio=("price_ratio_clean", "mean"),
            supplier_cross_province_rate=("_cross_province", "mean"),
            supplier_category_count=("统一服务类别", "nunique"),
            supplier_province_count=("项目省份", "nunique"),
        )
        .reset_index()
        .rename(columns={"_supplier": "统一供应商名称"})
    )
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
    return df.drop(columns=["_supplier", "_cross_province"]), supplier_profile''',
    ),
    (
        "A.5 集成异常检测模型",
        r'''# 来源：00_common/pipeline_core.py
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import OneClassSVM

def anomaly_detection(service: pd.DataFrame):
    """融合价格、文本、供应商画像和宏观变量，识别异常低价高风险项目。"""
    df = service.copy()
    numeric_cols = [
        "price_ratio_clean", "saving_rate_clean", "log_budget", "log_bid", "text_length",
        "supplier_win_count", "supplier_low_price_rate", "supplier_cross_province_rate",
        "supplier_category_count", "supplier_risk_score", "gdp_per_capita",
        "fiscal_pressure", "average_wage", "tertiary_industry_share", "urbanization_rate",
    ]
    topic_cols = [c for c in df.columns if c.startswith("lda_topic_prob_")]
    tfidf_cols = [c for c in df.columns if c.startswith("tfidf_pc")]
    numeric_cols = [c for c in [*numeric_cols, *topic_cols, *tfidf_cols[:20]] if c in df.columns]
    cat_cols = [c for c in ["采购方式标准化", "统一服务类别", "项目省份", "是否跨省中标", "lda_topic"] if c in df.columns]

    X = df[numeric_cols + cat_cols].copy()
    for col in cat_cols:
        X[col] = X[col].fillna("未识别").astype(str)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_cols),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                              ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True, min_frequency=10))]), cat_cols),
        ],
        remainder="drop",
    )
    X_proc = preprocessor.fit_transform(X)
    X_model = X_proc.toarray() if sparse.issparse(X_proc) else X_proc
    contamination = float(np.clip(max(df["is_high_risk_low_price"].mean(), 0.08), 0.06, 0.12))

    iforest = IsolationForest(n_estimators=400, contamination=contamination, random_state=42, n_jobs=-1)
    lof = LocalOutlierFactor(n_neighbors=35, contamination=contamination, metric="minkowski", n_jobs=-1)
    ocsvm = OneClassSVM(nu=contamination, kernel="rbf", gamma="scale")

    df["iforest_score"] = -iforest.fit(X_model).decision_function(X_model)
    df["lof_score"] = -lof.fit_predict(X_model) * 0 + (-lof.negative_outlier_factor_)
    df["ocsvm_score"] = -ocsvm.fit(X_model).decision_function(X_model)

    score_frame = df[["iforest_score", "lof_score", "ocsvm_score"]]
    score_scaled = pd.DataFrame(MinMaxScaler().fit_transform(score_frame), columns=score_frame.columns)
    rule_scaled = df["rule_risk_score"].fillna(0) / max(float(df["rule_risk_score"].max()), 1.0)
    df["ensemble_risk_score"] = (
        0.30 * score_scaled["iforest_score"]
        + 0.25 * score_scaled["lof_score"]
        + 0.20 * score_scaled["ocsvm_score"]
        + 0.25 * rule_scaled
    )
    q90 = df["ensemble_risk_score"].quantile(0.90)
    df["final_high_risk"] = (df["ensemble_risk_score"] >= q90).astype(int)
    return df''',
    ),
    (
        "A.6 监督学习复核与变量解释",
        r'''# 来源：00_common/pipeline_core.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

def supervised_models(service: pd.DataFrame):
    """以集成模型高风险标签为目标，训练可解释的监督模型并输出评价指标。"""
    df = service.copy()
    target = "final_high_risk"
    topic_cols = [c for c in df.columns if c.startswith("lda_topic_prob_")]
    numeric_cols = [
        "price_ratio_clean", "saving_rate_clean", "log_budget", "log_bid", "text_length",
        "supplier_win_count", "supplier_low_price_rate", "supplier_cross_province_rate",
        "supplier_risk_score", "gdp_per_capita", "fiscal_pressure", *topic_cols,
    ]
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    cat_cols = [c for c in ["采购方式标准化", "统一服务类别", "项目省份", "是否跨省中标", "lda_topic"] if c in df.columns]

    X = df[numeric_cols + cat_cols].copy()
    y = df[target].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_cols),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                              ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True, min_frequency=10))]), cat_cols),
        ],
        remainder="drop",
    )
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    pos = y_train.sum()
    neg = len(y_train) - pos

    models = {
        "Logistic": LogisticRegression(max_iter=1200, class_weight="balanced", n_jobs=-1, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=500, min_samples_leaf=4,
                                                class_weight="balanced_subsample", random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=360, max_depth=3, learning_rate=0.045,
                                 subsample=0.86, colsample_bytree=0.86, reg_lambda=1.2,
                                 objective="binary:logistic", eval_metric="logloss",
                                 scale_pos_weight=max(1.0, neg / max(pos, 1)), random_state=42),
    }
    metrics = []
    for name, model in models.items():
        model.fit(X_train_proc, y_train)
        pred = model.predict(X_test_proc)
        proba = model.predict_proba(X_test_proc)[:, 1]
        metrics.append({
            "模型": name,
            "Accuracy": accuracy_score(y_test, pred),
            "Precision": precision_score(y_test, pred, zero_division=0),
            "Recall": recall_score(y_test, pred, zero_division=0),
            "F1": f1_score(y_test, pred, zero_division=0),
            "AUC": roc_auc_score(y_test, proba),
        })
    return pd.DataFrame(metrics), models''',
    ),
    (
        "A.7 QCA 成因组合分析",
        r'''# 来源：00_common/pipeline_core.py
def qca_analysis(service: pd.DataFrame) -> pd.DataFrame:
    """将连续变量校准为集合条件，筛选具有较高一致性和覆盖度的风险组合路径。"""
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

    conditions = ["高节约率", "低价格比例", "高频供应商", "跨省中标",
                  "高财政压力", "公开招标", "供应商信息缺失", "高风险服务类别"]
    truth = (
        df.groupby(conditions)
        .agg(案例数=("记录ID", "count"), 高风险案例数=("final_high_risk", "sum"))
        .reset_index()
    )
    truth["一致性"] = truth["高风险案例数"] / truth["案例数"]
    truth["覆盖度"] = truth["高风险案例数"] / max(df["final_high_risk"].sum(), 1)
    selected = truth[(truth["案例数"] >= 8) & (truth["一致性"] >= 0.45) & (truth["高风险案例数"] >= 4)].copy()

    paths = []
    for i, row in selected.sort_values(["一致性", "覆盖度"], ascending=False).head(10).iterrows():
        present = [cond for cond in conditions if row[cond] == 1]
        absent = [f"非{cond}" for cond in ["公开招标", "跨省中标"] if row[cond] == 0]
        paths.append({
            "路径编号": f"路径{len(paths)+1}",
            "风险线索组合": " × ".join([*present, *absent]),
            "案例数": int(row["案例数"]),
            "高风险案例数": int(row["高风险案例数"]),
            "一致性": row["一致性"],
            "覆盖度": row["覆盖度"],
        })
    return pd.DataFrame(paths)''',
    ),
    (
        "A.8 采购关系网络与社群风险识别",
        r'''# 来源：00_common/pipeline_core.py
import networkx as nx

def network_analysis(service: pd.DataFrame):
    """构建供应商—采购人二部网络，计算中心性和高风险社群。"""
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
        G.add_edge(row["_supplier_node"], row["_buyer_node"],
                   weight=float(row["weight"]), risk_count=float(row["risk_count"]),
                   avg_score=float(row["avg_score"]))

    degree = dict(G.degree(weight="weight"))
    degree_cent = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, k=min(220, max(10, len(G) - 1)), seed=42) if len(G) > 2 else {}
    eigen = nx.eigenvector_centrality(G, max_iter=800, weight="weight") if len(G) > 0 else {}

    centrality = pd.DataFrame({
        "node": list(G.nodes()),
        "加权度": [degree.get(n, 0) for n in G.nodes()],
        "度中心性": [degree_cent.get(n, 0) for n in G.nodes()],
        "介数中心性": [betweenness.get(n, 0) for n in G.nodes()],
        "特征向量中心性": [eigen.get(n, 0) for n in G.nodes()],
        "节点类型": [G.nodes[n].get("node_type") for n in G.nodes()],
    })
    centrality["主体名称"] = centrality["node"].str.replace(r"^[SB]\|", "", regex=True)
    return G, edge_df, centrality''',
    ),
    (
        "A.9 图表绘制与高清输出",
        r'''# 来源：00_common/pipeline_core.py
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import PercentFormatter

def configure_plotting() -> Path | None:
    """统一设置中文字体、图像分辨率、网格线和学术配色。"""
    font_path = next((Path(p) for p in CHINESE_FONT_CANDIDATES if Path(p).exists()), None)
    if font_path:
        matplotlib.font_manager.fontManager.addfont(str(font_path))
        font_name = matplotlib.font_manager.FontProperties(fname=str(font_path)).get_name()
        plt.rcParams["font.sans-serif"] = [font_name, "Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 180
    plt.rcParams["savefig.dpi"] = 420
    plt.rcParams["figure.facecolor"] = "white"
    sns.set_theme(context="paper", style="whitegrid", palette=PALETTE)
    return font_path

def save_fig(fig: plt.Figure, name: str, pdf: bool = True) -> Path:
    """所有图形同时输出 PNG 和 PDF，便于论文插图与后续矢量编辑。"""
    polish_figure(fig)
    png_path = FIG_DIR / f"{name}.png"
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    if pdf:
        fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    return png_path

def bar_with_labels(data: pd.DataFrame, x: str, y: str, title: str, name: str,
                    horizontal: bool = False, color: str = "#0A9396",
                    percent_axis: bool = False, value_fmt: str = "{:.0f}") -> Path:
    """封装带数值标签的条形图，统一用于采购类别、模型识别数量和风险率图。"""
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    if horizontal:
        plot_data = data.sort_values(x, ascending=True)
        sns.barplot(data=plot_data, x=x, y=y, ax=ax, color=color, edgecolor="white", linewidth=0.7)
        for p in ax.patches:
            width = p.get_width()
            label = f"{width:.1%}" if percent_axis else value_fmt.format(width)
            ax.text(width + ax.get_xlim()[1] * 0.01, p.get_y() + p.get_height() / 2,
                    label, va="center", fontsize=8.2)
        if percent_axis:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    else:
        sns.barplot(data=data, x=x, y=y, ax=ax, color=color, edgecolor="white", linewidth=0.7)
        for p in ax.patches:
            height = p.get_height()
            label = f"{height:.1%}" if percent_axis else value_fmt.format(height)
            ax.text(p.get_x() + p.get_width() / 2, height, label, ha="center", va="bottom", fontsize=8.2)
        if percent_axis:
            ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title(title, loc="left")
    return save_fig(fig, name)''',
    ),
    (
        "A.10 章节脚本调度方式",
        r'''# 来源：第02章至第08章各 chapter*.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "00_common"
if str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))

import pipeline_core as core

def main() -> None:
    """各章节脚本复用 pipeline_core 中的函数，保证论文图表与数据结果同步生成。"""
    core.ensure_dirs()
    font_path = core.configure_plotting()
    full = core.read_table("full")
    price = core.add_recalculated_rules(core.read_table("price"))
    service = core.add_recalculated_rules(core.read_table("service"))
    service, supplier_profile = core.add_supplier_profile(service)
    service, keyword_table, high_keyword_table = core.text_and_topic_model(service, full, font_path)
    service, model_params, model_results = core.anomaly_detection(service)
    eval_table, fitted_models = core.supervised_models(service)
    qca_paths = core.qca_analysis(service)
    supplier_rank, buyer_rank, community_table = core.network_analysis(service)

if __name__ == "__main__":
    main()''',
    ),
]


def apply_code_format(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.right_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    for run in paragraph.runs:
        run.font.name = CODE_FONT
        run.font.size = CODE_SIZE
        run._element.rPr.rFonts.set(qn("w:eastAsia"), CODE_FONT)


def append_code_paragraph(doc: Document, line: str = "") -> None:
    p = doc.add_paragraph()
    run = p.add_run(line)
    apply_code_format(p)


def append_block(doc: Document, heading: str, code: str) -> None:
    append_code_paragraph(doc, "")
    h = doc.add_paragraph()
    r = h.add_run(heading)
    r.bold = True
    apply_code_format(h)
    h.paragraph_format.space_before = Pt(3)
    h.paragraph_format.space_after = Pt(1)
    for line in code.splitlines():
        append_code_paragraph(doc, line)


def main() -> None:
    doc = Document(INPUT_DOCX)
    breaker = doc.add_paragraph()
    breaker.add_run().add_break(WD_BREAK.PAGE)

    title = doc.add_paragraph()
    run = title.add_run("附录：数据处理、建模与绘图关键代码")
    run.bold = True
    apply_code_format(title)
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.space_after = Pt(4)

    note = (
        "# 说明：以下代码摘取并压缩自“统计建模代码”目录中的核心脚本，"
        "保留数据处理、风险标签构造、文本特征、异常检测、监督复核、QCA、网络分析和绘图输出等关键步骤。"
    )
    append_code_paragraph(doc, note)

    for heading, code in APPENDIX_BLOCKS:
        append_block(doc, heading, code)

    doc.save(OUTPUT_DOCX)
    print(OUTPUT_DOCX)


if __name__ == "__main__":
    main()
