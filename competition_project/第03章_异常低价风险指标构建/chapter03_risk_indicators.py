# -*- coding: utf-8 -*-
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

    full = core.read_table("全样本表")
    price = core.read_table("价格有效样本表")
    service = core.read_table("服务类主样本表")

    price_calc = core.add_recalculated_rules(price)
    core.save_data(price_calc, "price_valid_sample_rule_recalculated")

    for name, table in core.make_rule_tables(price, service).items():
        core.save_table(table, name)

    core.make_basic_figures(full, price, service)


if __name__ == "__main__":
    main()
