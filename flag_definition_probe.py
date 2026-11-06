from pathlib import Path
import pandas as pd

df=pd.read_csv(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"), encoding="utf-8-sig")
b=pd.to_numeric(df["预算金额"], errors="coerce")
w=pd.to_numeric(df["中标金额"], errors="coerce")
r=pd.to_numeric(df["中标/预算比例"], errors="coerce")
for flag in ["极端价格异常标记","比例异常标记","小金额标记","价格有效样本"]:
    print("\n",flag)
    g=df[flag].eq("是")
    print("count", g.sum())
    print("ratio<0.01", (g & r.lt(0.01)).sum(), "ratio=0", (g & r.eq(0)).sum(), "ratio>1", (g & r.gt(1)).sum(), "bid<=100", (g & w.le(100)).sum(), "budget<=100", (g & b.le(100)).sum())
print("combined small", ((b.le(100)|w.le(100))).sum())
print("ratio abnormal", ((r.le(0)|r.gt(1))).sum())
print("extreme guess r<0.01 or bid<=100", (r.lt(0.01)|w.le(100)).sum())
print("extreme guess r<0.01 or b<=100 or w<=100", (r.lt(0.01)|b.le(100)|w.le(100)).sum())
