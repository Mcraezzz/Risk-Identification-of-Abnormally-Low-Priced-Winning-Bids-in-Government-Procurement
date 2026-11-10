# 政府采购异常低价中标风险识别
# Risk Identification of Abnormally Low-Priced Winning Bids in Government Procurement

## 中文说明

本项目构建政府采购项目层面的异常低价中标风险识别流程，结合分类价格规则、集成异常检测、监督模型解释、组态分析以及供应商—采购人关系网络分析，为风险筛查与监管研究提供支持。

### 项目结构

| 路径 | 内容 |
| --- | --- |
| `competition_project/` | 完整分章节代码、公共核心、清洗和论文辅助脚本 |
| `competition_project/输出结果/` | 比赛目录中的分析报告、数据、表格和图件 |
| `data/` | 去重后的输入数据；重复名称映射见 `duplicate_aliases.json` |
| `alternate_results/` | 另一套独立结果，不能与比赛结果混用 |
| `papers/` | 学术润色版 Word/PDF 和文件名标记的最终版 Word |
| `chapter_code_templates/` | 首次上传的章节模板 |
| 根目录 Python 脚本 | 首次上传的分析、校验、绘图及论文生成工具 |
| `SUPPLEMENT_README.md` | 中英文补充说明、来源和版本限制 |
| `UPLOAD_MANIFEST.json` | 补充上传时的源文件清单与校验值 |

### 运行方式

在仓库根目录执行：

```bash
python -m pip install -r competition_project/requirements.txt
python competition_project/run_all.py
```

核心默认读取 `data/`，可通过环境变量 `PROCUREMENT_DATA_DIR` 指定输入目录。运行会更新 `competition_project/输出结果/`；如需保留既有结果，请先备份。

### 复现状态

56 个补充 Python 脚本已通过语法检查，但完整模型未重跑，依赖未锁定版本。绘图沿用 Windows 中文字体；清洗和论文辅助脚本中的本机路径需调整。

两套既有摘要记录的 XGBoost AUC 分别为 0.99134 和 0.98385，应按对应版本使用。这些并非本次重新验证得到的指标。最原始数据重建脚本引用的一份合同 CSV 缺失，完整清洗链路尚未验证。论文保留原版本名，正式提交版本尚未确认。详见[补充说明](SUPPLEMENT_README.md)。

## English

This project provides a project-level pipeline for identifying abnormally low-priced winning bids in government procurement. It combines category-aware price rules, ensemble anomaly detection, supervised model interpretation, configurational analysis, and supplier–buyer network analysis to support risk screening and regulatory research.

### Repository structure

| Path | Contents |
| --- | --- |
| `competition_project/` | Full chapter-based pipeline, shared core, cleaning and manuscript utilities |
| `competition_project/输出结果/` | Reports, data outputs, tables, and figures from the competition folder |
| `data/` | Deduplicated inputs; filename mappings are in `duplicate_aliases.json` |
| `alternate_results/` | A separate result snapshot that must not be mixed with competition outputs |
| `papers/` | Academically polished Word/PDF files and a Word file labelled as final |
| `chapter_code_templates/` | Chapter templates from the initial upload |
| Root-level Python scripts | Original analysis, validation, plotting, and manuscript generation tools |
| `SUPPLEMENT_README.md` | Bilingual supplementary notes, provenance, and version limitations |
| `UPLOAD_MANIFEST.json` | Source inventory and checksums recorded for the supplementary upload |

### Running the pipeline

Run from the repository root:

```bash
python -m pip install -r competition_project/requirements.txt
python competition_project/run_all.py
```

The core reads `data/` by default. Set `PROCUREMENT_DATA_DIR` to override the input directory. Running the pipeline updates `competition_project/输出结果/`; back up existing results if they need to be preserved.

### Reproducibility status

The 56 supplementary Python scripts passed syntax checks, but the full modelling pipeline has not been rerun and dependency versions are not pinned. Plotting retains Windows Chinese font settings. Local paths in cleaning and manuscript utilities require adjustment.

The two existing summaries report XGBoost AUC values of 0.99134 and 0.98385. Use each version consistently; these are historical outputs, not newly validated metrics. One contract CSV referenced by the raw-data reconstruction script is missing, so end-to-end cleaning reproducibility has not been established. Manuscripts retain their original version names; the formal submission version has not been confirmed. See the [supplementary notes](SUPPLEMENT_README.md).
