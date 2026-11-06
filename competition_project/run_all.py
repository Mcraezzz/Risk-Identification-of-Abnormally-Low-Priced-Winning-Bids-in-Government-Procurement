# -*- coding: utf-8 -*-
from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

CHAPTER_SCRIPTS = [
    ROOT / "第01章_引言" / "chapter01_intro_route.py",
    ROOT / "第02章_数据来源与预处理" / "chapter02_data_preprocessing.py",
    ROOT / "第03章_异常低价风险指标构建" / "chapter03_risk_indicators.py",
    ROOT / "第04章_文本特征工程与项目画像构建" / "chapter04_text_features_profiles.py",
    ROOT / "第05章_异常低价中标风险识别模型" / "chapter05_anomaly_detection.py",
    ROOT / "第06章_风险因素解释与成因组合分析" / "chapter06_explainability_qca.py",
    ROOT / "第07章_采购关系网络与风险聚集分析" / "chapter07_network_analysis.py",
    ROOT / "第08章_稳健性检验与扩展分析" / "chapter08_robustness.py",
    ROOT / "第09章_结论与政策建议" / "chapter09_summary_policy.py",
]


def main() -> None:
    for script in CHAPTER_SCRIPTS:
        for mod_name in list(sys.modules.keys()):
            if "pipeline_core" in mod_name:
                del sys.modules[mod_name]
        print(f"\n=== Running {script.parent.name}/{script.name} ===")
        runpy.run_path(str(script), run_name="__main__")
    print(f"\n全部章节分析完成。输出目录：{ROOT / '输出结果'}")


if __name__ == "__main__":
    main()
