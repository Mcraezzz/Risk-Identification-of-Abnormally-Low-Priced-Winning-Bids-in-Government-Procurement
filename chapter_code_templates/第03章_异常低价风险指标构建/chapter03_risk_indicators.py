from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    price = core.read_table("价格有效样本表")
    service = core.read_table("服务类主样本表")

    price_calc = core.add_recalculated_rules(price)
    core.save_data(price_calc, "price_valid_sample_rule_recalculated")

    for name, table in core.make_rule_tables(price, service).items():
        core.save_table(table, name)

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    sns.histplot(price["price_ratio_clean"].dropna().clip(0, 1.5), bins=45, kde=True, ax=ax, color="#0A9396")
    ax.axvline(0.65, color="#AE2012", lw=1.8, linestyle="--", label="政策参考阈值 0.65")
    ax.set_title("图6 中标/预算比例分布", loc="left")
    ax.set_xlabel("中标/预算比例")
    ax.set_ylabel("项目数量")
    ax.legend()
    sns.despine(ax=ax)
    core.save_fig(fig, "Fig06_price_ratio_histogram")

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    sns.histplot(price["saving_rate_clean"].dropna().clip(-0.2, 1), bins=45, kde=True, ax=ax, color="#CA6702")
    ax.axvline(0.35, color="#AE2012", lw=1.8, linestyle="--", label="节约率35%参考线")
    ax.set_title("图7 节约率分布", loc="left")
    ax.set_xlabel("节约率")
    ax.set_ylabel("项目数量")
    ax.legend()
    sns.despine(ax=ax)
    core.save_fig(fig, "Fig07_saving_rate_histogram")

    top_categories = service["统一服务类别"].value_counts().head(12).index
    box_data = service[service["统一服务类别"].isin(top_categories)].copy()
    box_data["统一服务类别短名"] = box_data["统一服务类别"].map(lambda x: core.short_label(x, 14))
    fig, ax = plt.subplots(figsize=(12, 6.4))
    sns.boxplot(
        data=box_data,
        x="统一服务类别短名",
        y="price_ratio_clean",
        ax=ax,
        palette=core.PALETTE,
        showfliers=True,
        fliersize=2.5,
        linewidth=0.8,
    )
    ax.axhline(0.65, color="#AE2012", linestyle="--", lw=1.4)
    ax.set_title("图8 不同服务类别的中标/预算比例箱线图", loc="left")
    ax.set_xlabel("统一服务类别")
    ax.set_ylabel("中标/预算比例")
    ax.tick_params(axis="x", rotation=35)
    sns.despine(ax=ax)
    core.save_fig(fig, "Fig08_service_price_ratio_boxplot")

    rule_counts = [
        ["政策阈值<0.65", int(price["rule_policy_65"].sum())],
        ["同类别10%分位", int(price["rule_quantile_10"].sum())],
        ["同类别5%分位", int(price["rule_quantile_5"].sum())],
        ["IQR离群", int(price["rule_iqr"].sum())],
        ["稳健Z分数", int(price["rule_robust_z"].sum())],
    ]
    import pandas as pd

    rule_counts = pd.DataFrame(rule_counts, columns=["规则", "异常项目数量"])
    core.bar_with_labels(rule_counts, "规则", "异常项目数量", "图9 四种规则识别异常数量对比", "Fig09_rule_detection_counts", color="#BB3E03")

    level_order = ["正常", "低风险", "中风险", "高风险"]
    level = price["rule_risk_level"].value_counts().reindex(level_order, fill_value=0).reset_index()
    level.columns = ["综合风险等级", "项目数量"]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    sns.barplot(data=level, x="综合风险等级", y="项目数量", palette=["#94D2BD", "#E9D8A6", "#EE9B00", "#AE2012"], ax=ax, edgecolor="#263238", linewidth=0.3)
    for p in ax.patches:
        ax.text(p.get_x() + p.get_width() / 2, p.get_height(), f"{p.get_height():.0f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("图10 综合风险等级分布", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("项目数量")
    sns.despine(ax=ax)
    core.save_fig(fig, "Fig10_rule_risk_level_distribution")


if __name__ == "__main__":
    main()
