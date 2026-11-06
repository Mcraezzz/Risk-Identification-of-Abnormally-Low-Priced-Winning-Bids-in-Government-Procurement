from pathlib import Path

import pandas as pd


def read(path):
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    raise RuntimeError(path)


base = Path(r"C:\Users\22672\Downloads")
ccgp = read(base / "ccgp_merged_supplier_credit_merged.csv")
q1 = read(base / "government_contract_q1_2025_sample_4500.csv")
for name, df in [("ccgp", ccgp), ("q1", q1)]:
    b = pd.to_numeric(df["预算金额"], errors="coerce")
    w = pd.to_numeric(df["中标金额"], errors="coerce")
    r = pd.to_numeric(df["中标/预算比例"], errors="coerce")
    print("\n", name, len(df))
    masks = {
        "budget_na": b.isna(),
        "bid_na": w.isna(),
        "ratio_na": r.isna(),
        "bid_eq_0": w.eq(0),
        "budget_eq_0": b.eq(0),
        "budget_le_100": b.le(100),
        "bid_le_100": w.le(100),
        "ratio_le_0": r.le(0),
        "ratio_gt_1": r.gt(1),
        "ratio_lt_001": r.lt(0.01),
    }
    for k, m in masks.items():
        print(k, int(m.sum()))
    keep = b.notna() & w.notna() & w.gt(0)
    print("keep_notna_bid_gt0", int(keep.sum()))
    print("removed", int((~keep).sum()))
    print("service counts", df["服务类别"].fillna("").value_counts().head(15).to_dict())
