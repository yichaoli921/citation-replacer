# 更新日志 / Changelog

本项目所有重要变更都会记录在此文件。版本号遵循 [Semantic Versioning](https://semver.org/)。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [1.1.0] - 2026-09-03

### ✨ 新增

- **PDF → Markdown 自动转换**（`scripts/pdf_to_md.py`）
  - 三种提取引擎 fallback：`pdftotext`（poppler）→ `pdfplumber` → `pypdf`
  - 支持批量转换（glob 模式）
- **目标期刊样文学**（`scripts/extract_style_from_samples.py`）
  - 从两篇目标期刊最新文章样本自动总结引用规范
  - 输出类似 `tmp_经济地理文献引用风格.md` 的风格备忘
- **期刊等级自动标注**（`scripts/enrich_journal_level.py`）
  - 内置**西财 2018 版期刊目录**（4849 条），覆盖中文/英文 A+/A/B/C 级
  - 支持 TSV 和 Markdown 双格式输出
- **SWUFE 期刊等级目录**（`references/journal-levels/swufe_2018.tsv`）
  - 从 `西南财经大学学术期刊等级分类目录（2018 版）.pdf` 解析
  - 94 个学科分类，4849 种期刊

### 📝 文档

- **README.md**：完整中文项目说明，含徽章、目录、典型用法、命令一览
- **CHANGELOG.md**：本文件
- **CONTRIBUTING.md**：贡献指南
- **CODE_OF_CONDUCT.md**：Contributor Covenant 行为准则
- **docs/architecture.md**：架构说明
- **docs/faq.md**：常见问题
- **examples/**：示例数据

### 🔧 改进

- SKILL.md 全面更新到 9 步工作流
- `workflow-memo.md` 增加 H.0 节（PDF 必须先落成 Markdown）、H.4 节（三份中间稿清单）
- 新增 `econ-geography-output-contract.md` 输出契约

### 🐛 修复

- 文件名含中文双引号时脚本生成新文件的 bug（用 glob 解决）
- 正则过宽导致通讯地址被误判为引用（`is_citation_block()` 过滤）
- 正则过严导致 "et al." 匹配失败（简化过滤逻辑）
- 叙述式引用漏处理（新增 `NARRATIVE_PAT`）

---

## [1.0.0] - 2026-09-03

### ✨ 首发

- **跨 run 替换主脚本**（`scripts/replace_citations.py`）
  - 支持括号式 `(作者，YYYY)` 和叙述式 `作者（YYYY）` 两种引用
  - 不动其他 run 的格式
- **追加参考文献章节**（`scripts/append_references.py`）
- **联网元数据补全**（`scripts/fetch_metadata.py`）
  - OpenAlex（无需 key）
  - CrossRef（DOI 已知时）
  - CNKI（占位）
- **作者归一化**（`scripts/normalize_authors.py`）
  - OCR 误字前缀
  - 缺逗号容忍
- **样例风格文件**：jingji-dili、gb-t-7714、dili-xuebao（用于示例和回归测试，不代表支持期刊上限）
- **完整 SKILL.md** 主入口

---

## 路线图

### [1.2.0] - 计划中

- 图表注、表格内引用支持
- Word 公式/编号保留
- 批量处理（多篇论文一次性转换）
- Web UI

### [2.0.0] - 远期

- 支持 LaTeX / Overleaf
- 集成 CrossRef 更新订阅
- 多语言（English/Japanese/Korean）期刊风格

---

[1.1.0]: https://github.com/yichaoli921/citation-replacer/releases/tag/v1.1.0
[1.0.0]: https://github.com/yichaoli921/citation-replacer/releases/tag/v1.0.0
