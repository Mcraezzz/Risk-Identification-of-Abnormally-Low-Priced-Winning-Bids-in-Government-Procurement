from pathlib import Path
import pandas as pd


def read(path, encs=("utf-8-sig", "utf-8", "gb18030")):
    for enc in encs:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    raise RuntimeError(path)


raw = read(Path(r"C:\Users\22672\Downloads\ccgp_merged_supplier_credit_merged.csv"))
final = read(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"))
f = final[final["数据来源"] == "ccgp_merged"]
raw_ids = set(raw["记录ID"])
final_ids = set(f["记录ID"])
removed = sorted(raw_ids - final_ids)
print("raw", len(raw), "final", len(f), "removed", len(removed))
b = pd.to_numeric(raw["预算金额"], errors="coerce")
w = pd.to_numeric(raw["中标金额"], errors="coerce")
r = pd.to_numeric(raw["中标/预算比例"], errors="coerce")
removed_df = raw[raw["记录ID"].isin(removed)].copy()
removed_df["_预算金额"] = b[raw["记录ID"].isin(removed)]
removed_df["_中标金额"] = w[raw["记录ID"].isin(removed)]
removed_df["_ratio"] = r[raw["记录ID"].isin(removed)]
print(removed_df[["记录ID","公告标题","预算金额","中标金额","中标/预算比例","节约率","服务类别"]].head(30).to_string())
print("removed condition counts:")
print("budget_na", removed_df["_预算金额"].isna().sum())
print("bid_na", removed_df["_中标金额"].isna().sum())
print("bid_eq0", removed_df["_中标金额"].eq(0).sum())
print("ratio_na", removed_df["_ratio"].isna().sum())
print("ratio_le0", removed_df["_ratio"].le(0).sum())
print("ratio_gt1", removed_df["_ratio"].gt(1).sum())
