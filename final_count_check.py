from pathlib import Path
import pandas as pd

df = pd.read_csv(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"), encoding="utf-8-sig")
for name, g in df.groupby("数据来源"):
    b = pd.to_numeric(g["预算金额"], errors="coerce")
    w = pd.to_numeric(g["中标金额"], errors="coerce")
    r = pd.to_numeric(g["中标/预算比例"], errors="coerce")
    print("\n", name, len(g))
    for k, m in {
        "budget_na": b.isna(),
        "bid_na": w.isna(),
        "bid_eq0": w.eq(0),
        "bid_le_100": w.le(100),
        "budget_le_100": b.le(100),
        "ratio_le0": r.le(0),
        "ratio_gt1": r.gt(1),
        "ratio_lt001": r.lt(0.01),
    }.items():
        print(k, int(m.sum()))
