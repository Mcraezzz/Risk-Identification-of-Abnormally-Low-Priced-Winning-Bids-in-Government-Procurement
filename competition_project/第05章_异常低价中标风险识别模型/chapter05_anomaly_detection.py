# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def load_service_features() -> pd.DataFrame:
    path = core.DATA_DIR / "service_main_text_features_profiles.csv"
    if path.exists():
        return pd.read_csv(path, encoding="utf-8-sig")
    service = core.read_table("服务类主样本表")
    full = core.read_table("全样本表")
    font_path = core.configure_plotting()
    service_text, _, _, _, _ = core.text_and_topic_model(service, full, font_path)
    service_text, _ = core.add_supplier_profile(service_text, "is_high_risk_low_price")
    return service_text


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    service_text = load_service_features()
    service_model, model_params, model_results = core.anomaly_detection(service_text)

    core.save_table(model_params, "Table11_anomaly_model_parameters")
    core.save_table(model_results, "Table12_anomaly_model_results")
    core.save_table(core.high_risk_descriptives(service_model), "Table13_high_risk_descriptive_statistics")
    core.make_anomaly_figures(service_model, model_results)

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
    core.save_data(service_model.sort_values("ensemble_risk_score", ascending=False), "service_main_model_results_full")
    core.save_data(service_model[result_cols].sort_values("ensemble_risk_score", ascending=False), "service_main_model_results")


if __name__ == "__main__":
    main()
