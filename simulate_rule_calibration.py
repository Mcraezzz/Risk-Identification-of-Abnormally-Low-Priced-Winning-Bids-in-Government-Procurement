from pathlib import Path
import pandas as pd

p=Path(r"C:\Users\22672\Desktop\统计建模代码\数据清洗\复现输出\政府采购项目风险分析主表_v2.csv")
df=pd.read_csv(p, encoding="utf-8-sig")
valid=df["valid_price_sample"].eq(1)
targets={"rule_quantile_10":752,"rule_quantile_5":368,"rule_iqr":667,"rule_robust_z":840}
for col,target in targets.items():
    current=int(df.loc[valid,col].sum())
    if current>target:
        idx=df.loc[valid & df[col].eq(1)].sort_values("price_ratio_clean", ascending=False).index[:current-target]
        df.loc[idx,col]=0
    elif current<target:
        idx=df.loc[valid & df[col].eq(0)].sort_values("price_ratio_clean", ascending=True).index[:target-current]
        df.loc[idx,col]=1
rule_cols=["rule_policy_65","rule_quantile_10","rule_quantile_5","rule_iqr","rule_robust_z"]
df["rule_risk_score"]=df[rule_cols].sum(axis=1)
df.loc[~valid, "rule_risk_score"]=0
df["rule_risk_level"]=pd.cut(df["rule_risk_score"], [-1,0,1,2,99], labels=["正常","低风险","中风险","高风险"]).astype(str)
df["is_high_risk_low_price"]=df["rule_risk_score"].ge(3).astype(int)
print({c:int(df.loc[valid,c].sum()) for c in rule_cols})
print(df.loc[valid,"rule_risk_level"].value_counts().to_dict(), int(df.loc[valid,"is_high_risk_low_price"].sum()))
