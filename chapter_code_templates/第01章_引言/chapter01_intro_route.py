from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "00_common"))

import pipeline_core as core  # noqa: E402


def main() -> None:
    core.ensure_dirs()
    core.configure_plotting()
    core.draw_flow_diagram(
        "Fig01_research_technical_route",
        "图1 研究技术路线图",
        [
            "数据来源：政府采购公告、2025Q1扩展样本、省级宏观指标",
            "数据清洗与主表构建：字段统一、价格处理、类别映射、省份标准化",
            "异常低价风险指标构建：固定阈值、分位数、IQR、稳健Z、多规则投票",
            "异常检测与风险解释：IForest、LOF、OCSVM、XGBoost、SHAP、QCA",
            "采购关系网络与监管建议：供应商—采购人网络、社群发现、预警闭环",
        ],
        side_notes=["多源融合", "四张正式分析表", "规则风险标签", "模型识别与解释", "政策建议"],
    )


if __name__ == "__main__":
    main()
