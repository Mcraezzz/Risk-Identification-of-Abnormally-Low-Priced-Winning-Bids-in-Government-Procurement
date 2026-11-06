from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    model_path = core.DATA_DIR / "service_main_model_results_full.csv"
    if not model_path.exists():
        raise FileNotFoundError("请先运行第05章脚本生成 service_main_model_results_full.csv")
    service_model = pd.read_csv(model_path, encoding="utf-8-sig")
    extend = core.read_table("2025Q1扩展样本表")
    full = core.read_table("全样本表")

    ext_calc = core.add_recalculated_rules(extend)
    core.save_data(ext_calc, "extension_2025q1_rule_recalculated")

    rob, category_risk, threshold_table = core.robustness_analysis(service_model, extend, full)
    core.save_table(rob, "Table22_robustness_results")
    core.save_table(category_risk, "Table23_procurement_category_risk_comparison")
    core.save_table(threshold_table, "Table24_threshold_sensitivity")


if __name__ == "__main__":
    main()
