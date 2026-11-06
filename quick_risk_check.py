from pathlib import Path

import pandas as pd


BASE = Path(r"C:\Users\22672\Desktop\统计建模原数据")
TARGETS = [
    "政府采购项目风险分析_价格有效样本表.csv",
    "政府采购项目风险分析_服务类主样本表.csv",
    "政府采购项目风险分析_2025Q1扩展样本表.csv",
]


def main() -> None:
    rule_cols = [
        "rule_policy_65",
        "rule_quantile_10",
        "rule_quantile_5",
        "rule_iqr",
        "rule_robust_z",
    ]
    for target in TARGETS:
        frame = pd.read_csv(BASE / target, encoding="utf-8-sig")
        print(f"\n{target} n={len(frame)}")
        for col in [*rule_cols, "rule_risk_score", "rule_risk_level", "is_suspicious_low_price", "is_high_risk_low_price"]:
            print(col, frame[col].value_counts(dropna=False).sort_index().to_dict())
        print("score_eq_sum5", (frame["rule_risk_score"] == frame[rule_cols].sum(axis=1)).mean())
        print("score_eq_sum4_no_q5", (frame["rule_risk_score"] == frame[[c for c in rule_cols if c != "rule_quantile_5"]].sum(axis=1)).mean())


if __name__ == "__main__":
    main()
