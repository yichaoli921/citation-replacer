# 中文论文引用格式转换器 / Citation Replacer

> 把 `（作者，YYYY）` 式作者-年份引用，一键转换为 `［1-3］` 顺序编码制上标，自动按目标期刊规范追加参考文献章节，并自动汇报西财期刊等级。

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-cc785c?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code/skills)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Made with ❤ in SWUFE](https://img.shields.io/badge/Made%20with-%E2%9D%A4-red)](https://www.swufe.edu.cn/)

[English](#english) · [简体中文](#简体中文) · [更新日志](CHANGELOG.md) · [贡献指南](CONTRIBUTING.md) · [踩坑记录](references/workflow-memo.md)

---

## ✨ 项目亮点

- **🎯 期刊级精度**：内置《经济地理》、《地理学报》、GB/T 7714 等期刊风格，按目标期刊样文学
- **🤖 AI 友好**：作为 Claude Code skill 打包，可与 `translate-paper-pdf-to-md` 等协同使用
- **📑 自动等级标注**：内置**西南财经大学学术期刊等级分类目录（2018 版）**，每条参考文献自动加 **A+/A/B/C 级**标签
- **🔄 智能容错**：OCR 误字、缺逗号、年份笔误、叙述式引用全覆盖
- **🌐 联网补全**：集成 OpenAlex / CrossRef，元数据实时拉取
- **🪶 轻依赖**：核心仅需 `python-docx`，可选 `pdfplumber` / `requests`

---

## 📋 目录

- [快速开始](#-快速开始)
- [典型用法](#-典型用法)
- [核心能力](#-核心能力)
- [支持期刊风格](#-支持期刊风格)
- [工作流（9 步）](#-工作流9-步)
- [命令行工具一览](#-命令行工具一览)
- [在 Claude Code 中调用](#-在-claude-code-中调用)
- [项目结构](#-项目结构)
- [测试](#-测试)
- [贡献](#-贡献)
- [许可](#-许可)
- [English](#english)

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/yichaoli921/citation-replacer.git
cd citation-replacer

# 推荐：使用虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 必装依赖
pip install python-docx pyyaml

# 可选依赖（PDF 提取 + 联网补全）
pip install pdfplumber requests
```

### 一行命令跑完整流程

```bash
# 把当前目录所有 PDF 转成 MD（用作引用提取的输入）
python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md

# 从两篇目标期刊样文总结引用风格
python scripts/extract_style_from_samples.py \
    tmp_md/sample1.md tmp_md/sample2.md \
    -o tmp_经济地理文献引用风格.md

# 提取作者-年份引用清单
python scripts/normalize_authors.py paper.md > cite_map_raw.tsv

# 联网补全元数据（OpenAlex 优先，CNKI 占位）
python scripts/fetch_metadata.py cite_map_raw.tsv cite_map_full.tsv

# 自动加 **期刊等级**
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv

# docx 跨 run 替换为上标
python scripts/replace_citations.py paper.docx cite_map.tsv jingji-dili paper_replaced.docx

# 追加参考文献章节
python scripts/append_references.py paper_replaced.docx refs_with_level.tsv jingji-dili paper_final.docx
```

---

## 🎯 典型用法

### 场景 1：投《经济地理》

```bash
# 下载目标期刊最新两篇文章 → style 备忘
python scripts/extract_style_from_samples.py \
    ~/Downloads/经济地理_样文1.pdf ~/Downloads/经济地理_样文2.pdf \
    -o tmp_经济地理文献引用风格.md \
    --journal "经济地理"

# 处理你的论文
python scripts/replace_citations.py 我的论文.docx cite_map.tsv jingji-dili 我的论文_最终.docx
```

### 场景 2：投《地理学报》

```bash
python scripts/replace_citations.py 我的论文.docx cite_map.tsv dili-xuebao 我的论文_最终.docx
```

### 场景 3：投 GB/T 7714 通用格式（学位论文等）

```bash
python scripts/replace_citations.py 学位论文.docx cite_map.tsv gb-t-7714 学位论文_最终.docx
```

### 场景 4：查看每条参考文献的期刊等级

```bash
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv
# 输出：A+级（《管理世界》）、A级（《经济地理》）、B级（《地理研究》）……
```

---

## 💡 核心能力

### 1. PDF → Markdown

任何喂入的 PDF 自动转 MD，方便后续编辑和引用抽取。三种提取引擎自动 fallback：

```bash
python scripts/pdf_to_md.py paper.pdf            # 单文件
python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md   # 批量
```

优先级：`pdftotext`（poppler）→ `pdfplumber`（中文友好）→ `pypdf`（Python 原生）

### 2. 风格自动学习

从两篇目标期刊最新文章样本提取规范：

```bash
python scripts/extract_style_from_samples.py sample1.pdf sample2.pdf -o style_report.md
```

输出涵盖：
- 方括号类型（全角 `［］` vs 半角 `[]`）
- 编号分隔符（连续 `-` vs 非连续 `，`）
- 作者分隔符（中文 `，` vs 英文 `,`）
- "等" vs "et al." 频次
- 文献类型标识（`［J］` / `［M］` / `［R］` / `［J/OL］`）
- DOI 处理（保留 vs 不写）
- 卷(期)冒号（全角 vs 半角）
- 页码格式（半角空格-dash vs 全角连字符）

### 3. 智能识别

- ✅ **括号式引用** `(黄蕙萍等，2020)` → `［1］`（上标）
- ✅ **叙述式引用** `Boschma（2005）...` → `Boschma［73］...`（文中平排，不上标）
- ✅ **OCR 容错**：`鉴韩峰` → `韩峰`，`余泳泽等2016` → `余泳泽等，2016`
- ✅ **跳过非引用块**：通讯地址、地图来源、邮箱、邮编

### 4. 期刊等级自动标注

集成**西财 2018 版期刊目录**（4849 条），自动给每条参考文献打 A+/A/B/C 级：

```
［1］ 黄蕙萍，缪子菊，袁野，等 . 生产性服务业的全球价值链及其中国参与度［J］. 管理世界，2020，36(9)：82 - 97.
- **期刊等级**：A+级（《管理世界》）

［3］ 宣烨，余泳泽 . 生产性服务业集聚对制造业企业全要素生产率提升研究［J］. 数量经济技术经济研究，2017，34(2)：89 - 104.
- **期刊等级**：A级（《数量经济技术经济研究》）

［5］ 熊丽芳，甄峰，王波，等 . 基于百度指数的长三角核心区城市网络特征研究［J］. 经济地理，2013，33(7)：67 - 73.
- **期刊等级**：A级（《经济地理》）
```

### 5. docx 安全替换

- 🛡️ **不动其他 run 的格式**（字号、字体、加粗、颜色）
- 🔒 **保留原稿已有上标**（如 `［1-2］`）
- 📐 **跨 run 安全处理**，不丢字符

---

## 📚 支持期刊风格

| Style | File | 方括号 | 句点 | DOI 默认 | 适用场景 |
|---|---|---|---|---|---|
| 《经济地理》 | [jingji-dili.md](references/journal-styles/jingji-dili.md) | `［］` 全角 | `. ` 半角点+空格 | 默认不写 | 经济地理类期刊 |
| 《地理学报》 | [dili-xuebao.md](references/journal-styles/dili-xuebao.md) | `［］` 全角 | `. ` 半角点+空格 | 默认保留 | 地理学综合 |
| GB/T 7714-2015 | [gb-t-7714.md](references/journal-styles/gb-t-7714.md) | `[]` 半角 | `. ` 半角点+空格 | 默认保留 | 国标通用 / 学位论文 |

**新增期刊**：在 `references/journal-styles/` 下添加 YAML 配置即可，无需改脚本。

---

## 🔄 工作流（9 步）

```
[1] 备份原文件                       → <file>.bak
[2] PDF → MD（自动 fallback）         → <file>.md
[3] docx → MD（pandoc）              → 提取引用清单
[4] Style learning：两篇目标期刊样文  → tmp_<期刊>文献引用风格.md
[5] 提取所有 (作者，YYYY)            → cite_map.tsv
[6] 联网补全缺项（OpenAlex/CrossRef）→ cite_map_full.tsv
[7] 期刊等级标注                     → refs_with_level.tsv
[8] python-docx 跨 run 替换          → 上标 ［N-M］
[9] 追加参考文献章节 + 验证           → 最终输出
```

详见 [assets/sample_workflow.md](assets/sample_workflow.md)。

---

## 🛠 命令行工具一览

| Script | 用途 | 输入 | 输出 |
|---|---|---|---|
| `pdf_to_md.py` | PDF → MD（多引擎 fallback） | `*.pdf` | `<file>.md` |
| `extract_style_from_samples.py` | 两篇样文 → 风格备忘 | 两个 PDF/MD | `tmp_<期刊>文献引用风格.md` |
| `normalize_authors.py` | 作者名归一化（OCR 容错）| MD/TSV | 归一化结果 |
| `fetch_metadata.py` | 联网补全元数据 | TSV | 完整 TSV |
| `enrich_journal_level.py` | 自动加 **期刊等级** | TSV / MD | 带等级标记 |
| `replace_citations.py` | docx 跨 run 替换 | docx + map | 替换后 docx |
| `append_references.py` | 追加参考文献章节 | docx + refs | 最终 docx |

---

## 🤖 在 Claude Code 中调用

作为 [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) 使用：

1. 复制 `citation-replacer/` 到 `~/.claude/skills/`（或项目 `.claude/skills/`）
2. 在对话中提及 **"参考文献"**、**"按 XX 期刊格式"**、**"change citations to numbered format"** 等关键词自动触发
3. 或显式调用：`/citation-replacer 我的论文.docx`

典型触发短语：
- 参考文献 / 添加参考文献 / 整理参考文献
- 统一引用格式 / 按《XX》期刊 / 按 XX 期刊格式
- 把作者-年份改成编号 / 整理为该刊格式
- 期刊等级 / 西财期刊目录 / A级期刊

---

## 📁 项目结构

```
citation-replacer/
├── SKILL.md                              # Claude Code skill 主入口
├── README.md                             # 本文件
├── CHANGELOG.md                          # 更新日志
├── LICENSE                               # MIT 许可证
├── CONTRIBUTING.md                       # 贡献指南
├── CODE_OF_CONDUCT.md                    # 行为准则
├── .gitignore
├── references/
│   ├── journal-styles/                   # 期刊风格配置
│   │   ├── jingji-dili.md               # 《经济地理》
│   │   ├── gb-t-7714.md                 # 国标通用
│   │   └── dili-xuebao.md               # 《地理学报》
│   ├── journal-levels/
│   │   └── swufe_2018.tsv               # 西财期刊等级目录（4849 条）
│   ├── regex-cheatsheet.md              # 正则备忘
│   ├── workflow-memo.md                 # 踩坑历史（OCR、双引号、叙述式引用、DOI）
│   └── econ-geography-output-contract.md # 输出契约
├── scripts/
│   ├── pdf_to_md.py                     # PDF → MD
│   ├── extract_style_from_samples.py    # 样文 → 风格报告
│   ├── normalize_authors.py             # 作者归一化
│   ├── fetch_metadata.py                # 联网拉元数据
│   ├── enrich_journal_level.py          # 期刊等级标注
│   ├── replace_citations.py             # docx 跨 run 替换
│   └── append_references.py             # 追加参考文献
├── assets/
│   ├── sample_workflow.md               # 完整工作样例
│   └── swufe_journal_list.md            # 期刊目录使用说明
├── examples/
│   ├── README.md                        # 示例说明
│   └── refs_demo.tsv                    # 示例 TSV
├── docs/
│   ├── architecture.md                  # 架构说明
│   └── faq.md                           # 常见问题
└── tests/
    ├── test_replace_citations.py        # 替换脚本测试
    ├── test_enrich_journal_level.py     # 等级标注测试
    └── fixtures/                         # 测试 fixture
```

---

## ✅ 测试

```bash
# 跑全部 smoke test
python tests/test_replace_citations.py
python tests/test_enrich_journal_level.py
```

---

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：
- 如何报告 bug
- 如何提新期刊风格
- 如何加新的数据源
- 开发环境设置

---

## 📜 许可

[MIT](LICENSE) © 2026 西财科研

---

## <a name="english"></a>English

**Citation Replacer** converts author-year in-text citations in Chinese academic `.docx` papers (e.g. `(黄蕙萍等，2020)`) into numbered superscript references (e.g. `［1-3］`), appends a properly-formatted reference list at the end, and automatically annotates each entry with a **journal tier** (A+/A/B/C) using the Southwest University of Finance and Economics (SWUFE) 2018 journal ranking list.

### Features

- 🎯 Journal-style aware (《经济地理》/《地理学报》/GB/T 7714)
- 🤖 Packed as a Claude Code skill
- 📑 Auto journal-tier annotation (SWUFE 2018, 4,849 journals)
- 🔄 OCR-tolerant (missing commas, year typos, narrative citations)
- 🌐 Online metadata via OpenAlex / CrossRef
- 🪶 Light dependencies (`python-docx` only)

### Quick Start

```bash
pip install python-docx pyyaml
python scripts/replace_citations.py paper.docx cite_map.tsv jingji-dili paper_out.docx
```

See [SKILL.md](SKILL.md) for the full Claude Code skill workflow.

---

*Last updated: 2026-09-03*
*Made with ❤ in Chengdu — 西南财经大学*