from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(os.environ["CODE_ROOT"])
table_path = next(ROOT.rglob("Table12_anomaly_model_results.csv"))
fig_dir = next(p.parent for p in ROOT.rglob("Fig17_anomaly_model_counts.png"))

font_candidates = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
]
font_path = next((p for p in font_candidates if p.exists()), None)
if font_path:
    fm.fontManager.addfont(str(font_path))
    font_name = fm.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams["font.sans-serif"] = [font_name, "Microsoft YaHei", "SimHei", "Arial"]
else:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 180
plt.rcParams["savefig.dpi"] = 420
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "#FAFBFD"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.labelcolor"] = "#111827"
plt.rcParams["axes.titlecolor"] = "#111827"
plt.rcParams["xtick.color"] = "#64748B"
plt.rcParams["ytick.color"] = "#64748B"
plt.rcParams["grid.color"] = "#E5E7EB"

counts = pd.read_csv(table_path, encoding="utf-8-sig")
counts["数量"] = pd.to_numeric(counts["高风险/异常项目数量"])

# 低饱和灰紫色，比原 #7C3AED 更沉稳，适合论文图表。
muted_academic_purple = "#5E548E"

fig, ax = plt.subplots(figsize=(9.5, 5.6))
bars = ax.bar(
    counts["识别方式"],
    counts["数量"],
    color=muted_academic_purple,
    edgecolor="white",
    linewidth=0.7,
    width=0.78,
)
for bar in bars:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.0f}",
        ha="center",
        va="bottom",
        fontsize=8.2,
        color="#111827",
    )

ax.set_title("图17 不同模型识别异常项目数量对比", loc="left", fontweight="semibold", pad=10)
ax.set_xlabel("识别方式")
ax.set_ylabel("数量")
ax.tick_params(axis="x", rotation=30)
for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")
ax.grid(axis="y", alpha=0.35, linewidth=0.8)
ax.grid(axis="x", alpha=0.18, linewidth=0.8)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
for side in ["left", "bottom"]:
    ax.spines[side].set_color("#CBD5E1")
    ax.spines[side].set_linewidth(0.8)
ax.margins(x=0.02, y=0.08)
fig.tight_layout()

png_path = fig_dir / "Fig17_anomaly_model_counts.png"
pdf_path = fig_dir / "Fig17_anomaly_model_counts.pdf"
fig.savefig(png_path, bbox_inches="tight", pad_inches=0.08, facecolor="white")
fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08, facecolor="white")
plt.close(fig)

print(png_path)
print(pdf_path)
