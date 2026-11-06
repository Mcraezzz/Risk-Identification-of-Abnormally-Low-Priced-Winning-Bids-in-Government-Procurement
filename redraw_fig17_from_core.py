from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(os.environ["CODE_ROOT"])
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


core.ensure_dirs()
core.configure_plotting()

table_path = next(ROOT.rglob("Table12_anomaly_model_results.csv"))
model_results = pd.read_csv(table_path, encoding="utf-8-sig")
counts = model_results.copy()
counts["数量"] = pd.to_numeric(counts["高风险/异常项目数量"])

core.bar_with_labels(
    counts,
    "识别方式",
    "数量",
    "图17 不同模型识别异常项目数量对比",
    "Fig17_anomaly_model_counts",
    color="#5E548E",
)

fig_dir = next(p.parent for p in ROOT.rglob("Fig17_anomaly_model_counts.png"))
print(fig_dir / "Fig17_anomaly_model_counts.png")
print(fig_dir / "Fig17_anomaly_model_counts.pdf")
