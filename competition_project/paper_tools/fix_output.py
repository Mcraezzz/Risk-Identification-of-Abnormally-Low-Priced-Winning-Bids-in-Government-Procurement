# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(r"C:\Users\22672\Desktop\统计建模比赛\统计建模代码\输出结果\tables")

# Fix Table17
qca = pd.read_csv(base / "Table17_qca_causal_paths.csv", encoding="utf-8-sig")
if "成因组合" in qca.columns:
    qca = qca.rename(columns={"成因组合": "风险线索组合"})
    qca.to_csv(base / "Table17_qca_causal_paths.csv", index=False, encoding="utf-8-sig")
    print("Fixed Table17 column name")

# Fix Table19 supplier rank if needed
for fname in ["Table19_supplier_centrality_ranking.csv", "Table20_buyer_risk_ranking.csv"]:
    path = base / fname
    if path.exists():
        df = pd.read_csv(path, encoding="utf-8-sig")
        # Add notes if missing
        if "备注" not in df.columns:
            df["备注"] = df.get("项目数量", pd.Series([0]*len(df))).map(
                lambda n: "样本量较小，高风险比例仅供参考，不构成违法认定" if pd.notna(n) and n < 5 else ""
            )
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"Fixed {fname} with notes")

print("Done")
