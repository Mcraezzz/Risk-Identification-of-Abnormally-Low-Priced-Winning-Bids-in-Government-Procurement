# 数据清洗复现说明

本目录用于从 Downloads 中的四份原始数据复现论文建模用数据表：

- `ccgp_merged_supplier_credit_merged.csv`
- `government_contract_q1_2025_sample_4500.csv`
- `provincial_indicators_2024.csv`
- `provincial_indicators_2025_partial.csv`

运行方式：

```powershell
& "C:\Users\22672\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\Users\22672\Desktop\统计建模代码\数据清洗\rebuild_procurement_tables_from_raw.py"
```

默认输出到：

```text
C:\Users\22672\Desktop\统计建模代码\数据清洗\复现输出
```

默认不会覆盖 `C:\Users\22672\Desktop\统计建模原数据` 下已经用于论文分析的正式表。

脚本执行的主要步骤：

1. 读取两份政府采购原始表和两份省级宏观指标表。
2. 删除预算金额或中标金额缺失、为零或极端异常的记录。
3. 标准化采购方式，包括框架协议、电子卖场、公开招标、竞争性磋商等。
4. 通过项目城市反推缺失省份，并处理深圳、青岛、厦门等城市型字段。
5. 统一供应商名称。
6. 构造 `采购大类` 与 `统一服务类别`。
   - CCGP 公告数据使用原服务类别显式映射。
   - 2025Q1 合同数据缺少可直接使用的服务类型，脚本按论文已定稿的 Q1 扩展样本口径，对 `采购大类` 与 15 类 `统一服务类别` 做确定性关键词校准。
7. 合并 2024 年完整省级宏观指标。
8. 构造价格有效样本、价格异常标记、规则风险标签。
9. 输出主表、主表_v2、全样本表、价格有效样本表、服务类主样本表、2025Q1扩展样本表。
