from pathlib import Path

import pandas as pd


BASE = Path(r"C:\Users\22672\Downloads")
FILES = [
    "ccgp_merged_supplier_credit_merged.csv",
    "government_contract_q1_2025_sample_4500.csv",
    "provincial_indicators_2024.csv",
    "provincial_indicators_2025_partial.csv",
]


def read_csv(path: Path, nrows: int | None = None) -> tuple[str, pd.DataFrame]:
    last = None
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return enc, pd.read_csv(path, encoding=enc, nrows=nrows)
        except Exception as exc:
            last = exc
    raise RuntimeError(f"Failed to read {path}: {last}")


def main() -> None:
    for file_name in FILES:
        path = BASE / file_name
        enc, df = read_csv(path, nrows=5)
        full_enc, full = read_csv(path)
        print(f"\n### {file_name}")
        print(f"encoding={enc} rows={len(full)} columns={len(full.columns)}")
        print("columns=" + "|".join(map(str, full.columns)))
        print(df.head(2).to_string(max_cols=18))
        miss = full.isna().mean().sort_values(ascending=False).head(15)
        print("top_missing=" + "; ".join(f"{k}:{v:.3f}" for k, v in miss.items()))


if __name__ == "__main__":
    main()
