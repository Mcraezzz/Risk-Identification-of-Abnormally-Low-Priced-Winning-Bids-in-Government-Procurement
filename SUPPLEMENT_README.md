# 补充项目说明

本次补充来自桌面“统计建模比赛”和“统计建模代码”。原仓库脚本保留。

- `competition_project/`：分章节代码、公共核心、数据清洗及论文辅助脚本、比赛目录的输出结果。
- `data/`：按 SHA-256 去重的原数据目录；同内容原名对应关系见 `duplicate_aliases.json`。
- `alternate_results/`：桌面独立“统计建模代码”目录的另一套结果快照，不与比赛结果混用。
- `papers/`：修改时间较晚的学术润色版 Word/PDF，以及原文件名标记的最终版 Word。尚未确认哪一份是正式提交版。
- `UPLOAD_MANIFEST.json`：源文件、目标位置、大小及原始 SHA-256；公共核心另记录调整后的 uploaded_sha256。

## 分章节运行

在仓库根目录执行：

```bash
python -m pip install -r competition_project/requirements.txt
python competition_project/run_all.py
```

公共核心默认读取仓库 `data/`，可用环境变量 `PROCUREMENT_DATA_DIR` 指定输入目录。原 `main_table_v2.csv` 与 `full_sample.csv` 内容完全一致，核心已映射到后者。字体配置仍沿用 Windows 中文字体。依赖未锁定版本，未执行完整模型重跑。

数据清洗和论文辅助脚本保留原始路径，使用前需调整。其中原始重建脚本引用的 `government_contract_q1_2025_sample_4500.csv` 不在这两个源目录中；现有的是带“服务类型”后缀的文件，未改名替代。现有建模输入表可供分析，但最原始数据到清洗结果的全流程尚未验证。

两套结果有实质差异：比赛目录摘要的 XGBoost AUC 为 0.9913399249914764，独立代码目录为 0.9838504375497216。须按对应版本使用，不能拼接为同一次运行。

未收录第三方文献全文、其他历史论文版本、论文页面渲染缓存、压缩包、临时测试文件及 Python 缓存。结果文件夹保留原有图表版本。
