from pathlib import Path

import pandas as pd


BASE = Path(r"C:\Users\22672\Desktop\统计建模原数据")

FILES = [
    "政府采购项目风险分析_全样本表.csv",
    "政府采购项目风险分析_价格有效样本表.csv",
    "政府采购项目风险分析_服务类主样本表.csv",
    "政府采购项目风险分析_2025Q1扩展样本表.csv",
    "政府采购项目风险分析主表_v2.csv",
]


def read_head(path: Path) -> tuple[str, pd.DataFrame]:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return encoding, pd.read_csv(path, nrows=5, encoding=encoding)
        except Exception as exc:  # noqa: BLE001 - inspection script reports all failures.
            last_error = exc
    raise RuntimeError(f"Could not read {path}: {last_error}")


def main() -> None:
    for file_name in FILES:
        path = BASE / file_name
        print(f"\n### {file_name}")
        print(f"exists={path.exists()} size={path.stat().st_size if path.exists() else 'NA'}")
        encoding, head = read_head(path)
        frame = pd.read_csv(path, encoding=encoding)
        print(f"encoding={encoding} rows={len(frame)} columns={len(frame.columns)}")
        print("columns=" + "|".join(map(str, frame.columns)))
        key_cols = [
            "采购大类",
            "统一服务类别",
            "采购方式标准化",
            "项目省份",
            "预算金额",
            "中标金额",
            "price_ratio_clean",
            "saving_rate_clean",
            "rule_risk_score",
            "is_high_risk_low_price",
            "统一供应商名称",
            "采购人名称",
        ]
        available = [col for col in key_cols if col in frame.columns]
        if available:
            miss = frame[available].isna().mean().sort_values(ascending=False)
            print("missing_rate=" + "; ".join(f"{k}:{v:.3f}" for k, v in miss.items()))
        print("dtypes=" + "; ".join(f"{k}:{v}" for k, v in frame.dtypes.astype(str).items()))
        print("head_titles=" + " || ".join(map(str, head.get("公告标题", pd.Series([], dtype=str)).head(2).tolist())))


if __name__ == "__main__":
    main()
