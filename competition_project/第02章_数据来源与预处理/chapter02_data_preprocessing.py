# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()

    full = core.read_table("全样本表")
    price = core.read_table("价格有效样本表")
    service = core.read_table("服务类主样本表")
    extend = core.read_table("2025Q1扩展样本表")
    v2 = core.read_table("主表_v2")

    for name, table in core.make_distribution_tables(full, price, service, extend, v2).items():
        core.save_table(table, name)

    core.draw_flow_diagram(
        "Fig02_data_cleaning_flow",
        "图2 数据清洗流程图",
        ["原始采购数据", "字段统一", "价格异常处理", "服务类别统一", "省份标准化", "宏观变量合并", "四类建模样本"],
        horizontal=True,
    )

    category = full["采购大类"].fillna("未识别").value_counts().reset_index()
    category.columns = ["采购大类", "项目数量"]
    core.bar_with_labels(category, "采购大类", "项目数量", "图3 采购大类分布", "Fig03_procurement_category_distribution", color="#2563EB")

    service_dist = full["统一服务类别"].fillna("未识别").value_counts().head(15).reset_index()
    service_dist.columns = ["统一服务类别", "项目数量"]
    service_dist["统一服务类别"] = service_dist["统一服务类别"].map(lambda x: core.short_label(x, 18))
    core.bar_with_labels(
        service_dist,
        "项目数量",
        "统一服务类别",
        "图4 统一服务类别分布（Top 15）",
        "Fig04_service_category_distribution",
        horizontal=True,
        color="#0A9396",
    )

    prov = full["项目省份"].fillna("未识别").value_counts().head(15).reset_index()
    prov.columns = ["项目省份", "项目数量"]
    core.bar_with_labels(
        prov,
        "项目省份",
        "项目数量",
        "图5 项目省份分布（Top 15）",
        "Fig05_province_distribution_top15",
        color="#EE9B00",
    )


if __name__ == "__main__":
    main()
