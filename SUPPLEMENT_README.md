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

---

# Supplementary Project Notes

These additions come from the desktop folders `统计建模比赛` and `统计建模代码`. The original repository scripts are retained.

- `competition_project/`: chapter scripts, shared core, cleaning and manuscript utilities, and competition-folder outputs.
- `data/`: files deduplicated by SHA-256. Original duplicate filenames are mapped in `duplicate_aliases.json`.
- `alternate_results/`: an independent output snapshot from the separate desktop code folder; do not mix it with competition results.
- `papers/`: the more recently modified academically polished Word/PDF files and the Word file originally labelled as final. The formal submission version has not been confirmed.
- `UPLOAD_MANIFEST.json`: source paths, destinations, sizes, and original SHA-256 checksums. The adjusted shared core also records `uploaded_sha256`.

## Running the chapter pipeline

From the repository root:

```bash
python -m pip install -r competition_project/requirements.txt
python competition_project/run_all.py
```

The core reads `data/` by default; override it using `PROCUREMENT_DATA_DIR`. The original `main_table_v2.csv` is identical to `full_sample.csv`, so the core maps that input to the latter. Font settings retain Windows Chinese fonts. Dependencies are not version-pinned, and the full modelling pipeline has not been rerun.

Cleaning and manuscript utilities retain their original local paths and need adjustment. The reconstruction script references `government_contract_q1_2025_sample_4500.csv`, which was absent from both source directories. A file with a Chinese service-type suffix exists but was not renamed as a substitute. Modelling inputs are available, but the complete path from the earliest raw data to cleaned outputs has not been verified.

The two result snapshots differ materially: their summaries report XGBoost AUC values of 0.9913399249914764 for the competition folder and 0.9838504375497216 for the separate code folder. Use each version consistently; do not combine them as a single run.

Third-party literature full texts, other historical manuscript versions, manuscript rendering caches, archives, temporary test files, and Python caches were excluded. Existing figure versions in output directories were retained.
