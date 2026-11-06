from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def load_model_results() -> pd.DataFrame:
    path = core.DATA_DIR / "service_main_model_results_full.csv"
    if path.exists():
        return pd.read_csv(path, encoding="utf-8-sig")
    raise FileNotFoundError("请先运行第05章脚本生成 service_main_model_results_full.csv")


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    service_model = load_model_results()
    eval_table, logistic_table, rf_importance, xgb_importance, shap_importance, shap_payload = core.supervised_models(service_model)

    core.save_table(logistic_table, "Table14_logistic_regression_results")
    core.save_table(eval_table, "Table15_supervised_model_evaluation")
    core.save_table(shap_importance, "Table16_shap_importance")
    core.save_table(rf_importance, "Table16b_random_forest_importance")
    core.save_table(xgb_importance, "Table16c_xgboost_importance")
    core.make_supervised_figures(eval_table, rf_importance, xgb_importance, shap_importance, shap_payload)

    qca_paths = core.qca_analysis(service_model)
    core.save_table(qca_paths, "Table17_qca_causal_paths")


if __name__ == "__main__":
    main()
