from pathlib import Path
import pandas as pd

raw = pd.read_csv(Path(r"C:\Users\22672\Downloads\ccgp_merged_supplier_credit_merged.csv"), encoding="gb18030")
b = pd.to_numeric(raw["预算金额"], errors="coerce")
w = pd.to_numeric(raw["中标金额"], errors="coerce")
r = pd.to_numeric(raw["中标/预算比例"], errors="coerce")
conds = {
    "b_notna_w_notna_wgt0": b.notna() & w.notna() & w.gt(0),
    "b_w_r_notna_wgt0": b.notna() & w.notna() & r.notna() & w.gt(0),
    "b_w_r_notna_wgt0_bgt0": b.notna() & w.notna() & r.notna() & w.gt(0) & b.gt(0),
    "b_w_r_notna_wgt0_rge0": b.notna() & w.notna() & r.notna() & w.gt(0) & r.ge(0),
    "b_w_r_notna_wgt0_rgt0": b.notna() & w.notna() & r.notna() & w.gt(0) & r.gt(0),
}
for k, m in conds.items():
    print(k, int(m.sum()), "removed", int((~m).sum()))
print(raw[(b.notna() & w.notna() & w.gt(0) & r.isna())][["记录ID", "公告标题", "预算金额", "中标金额", "中标/预算比例"]].head().to_string())
