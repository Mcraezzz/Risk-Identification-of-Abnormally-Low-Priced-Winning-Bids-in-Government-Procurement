from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


TABLE_DIR = Path(r"C:\Users\22672\Desktop\统计建模代码\输出结果\tables")
DATA_DIR = Path(r"C:\Users\22672\Desktop\统计建模代码\输出结果\data")
OUT = Path(r"C:\Users\22672\Desktop\统计建模代码\输出结果\paper_numeric_inputs.json")

KEY_TABLES = [
    "Table01_data_sources.csv",
    "Table02_field_structure.csv",
    "Table03_sample_split.csv",
    "Table04_procurement_category_distribution.csv",
    "Table06_rule_detection_comparison.csv",
    "Table07_service_category_risk_rate.csv",
    "Table07b_procurement_method_risk_rate.csv",
    "Table07c_province_risk_rate.csv",
    "Table09_lda_topic_interpretation.csv",
    "Table12_anomaly_model_results.csv",
    "Table14_logistic_regression_results.csv",
    "Table15_supervised_model_evaluation.csv",
    "Table16_shap_importance.csv",
    "Table17_qca_causal_paths.csv",
    "Table19_supplier_centrality_ranking.csv",
    "Table20_buyer_risk_ranking.csv",
    "Table22_robustness_results.csv",
    "Table23_procurement_category_risk_comparison.csv",
    "Table24_threshold_sensitivity.csv",
    "Table25_policy_recommendation_evidence.csv",
]


def records(path: Path, n: int = 12):
    df = pd.read_csv(path, encoding="utf-8-sig")
    return df.head(n).where(pd.notna(df), "").to_dict(orient="records")


def main() -> None:
    obj = {}
    for name in KEY_TABLES:
        obj[name] = records(TABLE_DIR / name, n=15)
    model = pd.read_csv(DATA_DIR / "service_main_model_results.csv", encoding="utf-8-sig")
    obj["high_risk_top10"] = model.head(10).where(pd.notna(model), "").to_dict(orient="records")
    OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
