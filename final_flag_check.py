from pathlib import Path
import pandas as pd

df=pd.read_csv(Path(r"C:\Users\22672\Desktop\统计建模原数据\政府采购项目风险分析主表_v2.csv"), encoding="utf-8-sig")
for c in ["价格有效样本","极端价格异常标记","比例异常标记","小金额标记","valid_price_sample"]:
    print(c)
    print(df[c].value_counts(dropna=False).to_string())
