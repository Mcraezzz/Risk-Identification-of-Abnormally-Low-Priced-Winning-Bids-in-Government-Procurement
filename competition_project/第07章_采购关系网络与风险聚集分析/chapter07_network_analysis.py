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
    core.configure_plotting()

    model_path = core.DATA_DIR / "service_main_model_results_full.csv"
    if not model_path.exists():
        raise FileNotFoundError("请先运行第05章脚本生成 service_main_model_results_full.csv")
    service_model = pd.read_csv(model_path, encoding="utf-8-sig")

    network_def = pd.DataFrame(
        [
            ["供应商节点", "统一供应商名称", "中标主体"],
            ["采购人节点", "采购人名称", "采购需求发布主体"],
            ["供应商—采购人边", "同一项目中形成交易关系", "边权为交易项目数量，高风险边记录风险项目数"],
            ["度中心性", "连接主体数量", "识别高频交易主体"],
            ["介数中心性", "网络桥梁位置", "识别关键中介主体"],
            ["特征向量中心性", "连接重要主体程度", "识别核心交易主体"],
            ["Louvain社群", "基于交易网络模块度划分", "识别风险聚集群体"],
        ],
        columns=["网络元素/指标", "定义", "用途"],
    )
    core.save_table(network_def, "Table18_network_node_edge_definitions")

    supplier_rank, buyer_rank, community_table = core.network_analysis(service_model)
    core.save_table(supplier_rank, "Table19_supplier_centrality_ranking")
    core.save_table(buyer_rank, "Table20_buyer_risk_ranking")
    core.save_table(community_table, "Table21_high_risk_community_features")


if __name__ == "__main__":
    main()
