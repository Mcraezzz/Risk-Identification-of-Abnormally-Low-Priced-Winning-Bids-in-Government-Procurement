from pathlib import Path
import pandas as pd

df = pd.read_csv(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"), encoding="utf-8-sig")
print("采购大类")
print(df["采购大类"].value_counts(dropna=False).to_string())
print("\n统一服务类别")
print(df["统一服务类别"].value_counts(dropna=False).to_string())
print("\n采购方式标准化")
print(df["采购方式标准化"].value_counts(dropna=False).to_string())
print("\nQ1 category")
print(df[df["数据来源"].eq("gov_contract_q1_2025")]["采购大类"].value_counts(dropna=False).to_string())
print("\nQ1 service")
print(df[df["数据来源"].eq("gov_contract_q1_2025")]["统一服务类别"].value_counts(dropna=False).to_string())
