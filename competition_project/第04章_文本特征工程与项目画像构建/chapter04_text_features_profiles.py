# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    font_path = core.configure_plotting()

    service = core.read_table("服务类主样本表")
    full = core.read_table("全样本表")

    service_text, keyword_table, risk_keyword_table, lda_topics, text_rules = core.text_and_topic_model(service, full, font_path)
    service_text, supplier_profile = core.add_supplier_profile(service_text, "is_high_risk_low_price")

    supplier_field_table = pd.DataFrame(
        [
            ["supplier_win_count", "同一供应商在服务类主样本中出现次数", "供应商活跃度"],
            ["supplier_low_price_count", "供应商关联规则高风险项目数量", "低价中标历史"],
            ["supplier_avg_saving_rate", "供应商项目平均节约率", "价格行为画像"],
            ["supplier_cross_province_rate", "跨省中标项目占比", "跨区域交易画像"],
            ["supplier_category_count", "涉及统一服务类别数量", "经营类别广度"],
            ["supplier_risk_score", "低价率、低价次数、中标次数、跨省比例加权", "供应商综合风险画像分"],
        ],
        columns=["字段", "构造口径", "解释"],
    )

    core.save_table(text_rules, "Table08_text_preprocessing_rules")
    core.save_table(lda_topics, "Table09_lda_topic_interpretation")
    core.save_table(supplier_field_table, "Table10_supplier_profile_fields")
    core.save_table(supplier_profile, "Table10b_supplier_profile_summary")
    core.save_table(keyword_table, "Table10c_overall_keywords")
    core.save_table(risk_keyword_table, "Table10d_risk_vs_normal_keywords")
    core.make_topic_figures(service_text, lda_topics, keyword_table)

    keep_cols = [
        "记录ID",
        "公告标题",
        "发布日期",
        "项目省份",
        "项目城市",
        "项目名称",
        "采购人名称",
        "统一供应商名称",
        "预算金额",
        "中标金额",
        "price_ratio_clean",
        "saving_rate_clean",
        "采购方式标准化",
        "统一服务类别",
        "rule_risk_score",
        "rule_risk_level",
        "is_suspicious_low_price",
        "is_high_risk_low_price",
        "是否跨省中标",
        "gdp_per_capita",
        "fiscal_pressure",
        "average_wage",
        "tertiary_industry_share",
        "urbanization_rate",
        "text_all",
        "text_length",
        "tokenized_text",
        "lda_topic",
        "supplier_win_count",
        "supplier_low_price_count",
        "supplier_low_price_rate",
        "supplier_cross_province_rate",
        "supplier_category_count",
        "supplier_risk_score",
    ]
    keep_cols.extend([c for c in service_text.columns if c.startswith("tfidf_pc") or c.startswith("lda_topic_prob_")])
    keep_cols = [c for c in keep_cols if c in service_text.columns]
    core.save_data(service_text[keep_cols], "service_main_text_features_profiles")


if __name__ == "__main__":
    main()
