from pathlib import Path
import pandas as pd


raw = pd.read_csv(Path(r"C:\Users\22672\Downloads\ccgp_merged_supplier_credit_merged.csv"), encoding="gb18030")
final = pd.read_csv(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"), encoding="utf-8-sig")
final = final[final["数据来源"].eq("ccgp_merged")].copy()

for df in [raw, final]:
    for c in ["公告标题", "发布日期", "项目名称", "采购人名称", "预算金额", "中标金额", "服务类别"]:
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["_key"] = df[["公告标题", "发布日期", "项目名称", "采购人名称", "预算金额", "中标金额", "服务类别"]].agg("||".join, axis=1)

raw_valid = raw[pd.to_numeric(raw["预算金额"], errors="coerce").notna() & pd.to_numeric(raw["中标金额"], errors="coerce").notna() & pd.to_numeric(raw["中标金额"], errors="coerce").gt(0)].copy()
raw_counts = raw_valid["_key"].value_counts()
final_counts = final["_key"].value_counts()
missing = []
for key, n in raw_counts.items():
    diff = n - final_counts.get(key, 0)
    if diff > 0:
        missing.extend([key] * diff)
print("raw_valid", len(raw_valid), "final", len(final), "missing diff", len(missing))
if missing:
    miss_df = raw_valid[raw_valid["_key"].isin(set(missing))]
    print(miss_df[["记录ID","公告标题","发布日期","项目名称","采购人名称","预算金额","中标金额","中标/预算比例","服务类别"]].head(20).to_string())
