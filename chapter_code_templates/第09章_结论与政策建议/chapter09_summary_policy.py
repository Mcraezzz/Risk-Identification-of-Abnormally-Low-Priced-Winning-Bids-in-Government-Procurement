from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    full = core.read_table("全样本表")
    price = core.read_table("价格有效样本表")
    extend = core.read_table("2025Q1扩展样本表")

    model_path = core.DATA_DIR / "service_main_model_results_full.csv"
    if not model_path.exists():
        raise FileNotFoundError("请先运行第05章脚本生成 service_main_model_results_full.csv")
    service_model = pd.read_csv(model_path, encoding="utf-8-sig")

    eval_path = core.TABLE_DIR / "Table15_supervised_model_evaluation.csv"
    shap_path = core.TABLE_DIR / "Table16_shap_importance.csv"
    if eval_path.exists():
        eval_table = pd.read_csv(eval_path, encoding="utf-8-sig")
        xgb_row = eval_table[eval_table["模型"].eq("XGBoost")].iloc[0]
    else:
        xgb_row = pd.Series({"AUC": float("nan"), "F1": float("nan")})
    if shap_path.exists():
        shap_importance = pd.read_csv(shap_path, encoding="utf-8-sig")
        shap_top5 = "、".join(shap_importance["变量"].head(5).astype(str).tolist())
    else:
        shap_top5 = ""

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
    table_paths = {"Table25_policy_recommendation_evidence": core.save_table(policy_evidence, "Table25_policy_recommendation_evidence")}

    core.draw_flow_diagram(
        "Fig37_regulatory_closed_loop",
        "图37 政府采购异常低价风险监管闭环图",
        ["公告数据采集", "异常低价预警", "供应商画像", "人工复核", "履约跟踪", "风险规则更新"],
        horizontal=True,
    )

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
        "shap_top5": shap_top5,
        "extend_rule_high_rate": float(extend["is_high_risk_low_price"].mean()),
    }
    (core.OUTPUT_DIR / "analysis_key_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    for table_path in core.TABLE_DIR.glob("Table*.csv"):
        table_paths.setdefault(table_path.stem, table_path)
    core.write_report(summary, table_paths, list(core.FIG_DIR.glob("*.png")))


if __name__ == "__main__":
    main()
