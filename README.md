# citation-replacer

一个用于中文论文投稿前整理参考文献的 Codex / Claude Code Skill。

它不是固定的“某几个期刊格式模板库”。它的核心用法是：给它你的论文，再给它目标期刊最新两篇样文，它会先把样文转成 Markdown，总结出本轮目标期刊的引用格式，然后据此整理正文引用和文末参考文献。

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-blueviolet)](SKILL.md)

## 它解决什么问题

中文论文投稿时，参考文献最麻烦的地方往往不是“有没有文献”，而是这些细碎但很容易出错的格式：

- 正文里还是 `（作者，年份）`，目标期刊要求 `［1］`、`［1-3］` 这类顺序编码制。
- 不同期刊对作者数量、`等`、`et al.`、卷期页码、DOI、网络首发的处理不完全一样。
- Word 里的引用常常跨 run，直接替换容易把字体、字号、加粗、上标弄乱。
- OCR 会把作者名、年份、逗号识别错，导致引用和参考文献对不上。
- 通讯地址、地图来源、数据来源也可能带年份和括号，容易被误判成引用。

`citation-replacer` 把这些步骤整理成一条可复核的工作流：先留下 Markdown 证据链，再改 Word。

## 标准工作流

一次完整任务通常需要三类输入：

1. 你的论文：优先是 `.docx`，如果有 PDF 也会先转成 Markdown。
2. 目标期刊最新两篇样文：PDF 或 Markdown。
3. 参考文献线索：正文引用、已有参考文献、CNKI / CrossRef / OpenAlex 等元数据来源。

工作流如下：

```text
目标期刊两篇最新样文 PDF
        ↓
PDF 转 Markdown
        ↓
总结目标期刊引用格式
        ↓
生成 tmp_<期刊>文献引用风格.md

用户论文 DOCX / PDF
        ↓
转 Markdown 并抽取正文引用
        ↓
按正文首次出现顺序编号、去重、合并重复文献
        ↓
生成 tmp_<期刊>文献引用.md

文献元数据补全与格式化
        ↓
按目标期刊样文格式生成参考文献
        ↓
自动匹配西财 2018 期刊等级目录
        ↓
生成 tmp_参考文献_<期刊>风格.md

回到 Word
        ↓
跨 run 安全替换正文引用
        ↓
追加参考文献章节
        ↓
验证残留引用、编号连续性、条目数和格式问题
```

## 关键产物

这个 skill 的重点不是只交付一个最终 Word 文件，而是保留三份可复核的中间稿：

| 文件 | 作用 |
|---|---|
| `tmp_<期刊>文献引用风格.md` | 从目标期刊两篇最新样文中总结出的引用格式 |
| `tmp_<期刊>文献引用.md` | 正文引用抽取、去重、编号、综合替换方案 |
| `tmp_参考文献_<期刊>风格.md` | 按目标期刊格式整理的参考文献，并附期刊等级和存疑说明 |

如果目标期刊是《经济地理》，文件名可以是：

- `tmp_经济地理文献引用风格.md`
- `tmp_经济地理文献引用.md`
- `tmp_参考文献_经济地理风格.md`

如果目标期刊是其他刊物，把文件名里的期刊名替换掉即可。

## 样文驱动，而不是内置期刊清单

本项目里保留了 `references/journal-styles/` 下的一些风格文件，例如：

- `jingji-dili.md`
- `dili-xuebao.md`
- `gb-t-7714.md`

这些文件只是开发样例、测试材料和紧急 fallback，不代表这个 skill 只能处理这些期刊。

真实任务中，格式判断优先级是：

1. 本轮用户提供的目标期刊最新两篇样文。
2. 从样文生成的 `tmp_<期刊>文献引用风格.md`。
3. 经人工核对后沉淀的 `references/journal-styles/<期刊>.md`。
4. 旧样例风格文件，仅作参考。

也就是说，你要投哪个期刊，就喂哪个期刊最新两篇样文。

## 能力清单

### 1. PDF 转 Markdown

任何喂入的 PDF 都先转为 Markdown，避免后续引用抽取和格式判断只靠肉眼记忆。

```bash
python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md
```

提取优先级：

1. `pdftotext`
2. `pdfplumber`
3. `pypdf`

### 2. 目标期刊格式学习

从两篇目标期刊样文中生成引用风格备忘：

```bash
python scripts/extract_style_from_samples.py \
  sample1.pdf sample2.pdf \
  --journal "目标期刊名" \
  -o tmp_目标期刊文献引用风格.md
```

风格备忘会关注：

- 文内引用是顺序编码制还是作者年份制。
- 方括号使用全角还是半角。
- 连续编号和非连续编号如何写。
- 叙述式引用如何处理。
- 中文作者、英文作者、`等`、`et al.` 的写法。
- 文末参考文献是否按正文首次出现顺序编号。
- DOI 是否保留。
- 卷、期、页码、网络首发、报告和专著如何排版。

### 3. 正文引用替换

支持两类常见中文论文引用：

| 类型 | 原文 | 处理 |
|---|---|---|
| 括号式引用 | `（黄蕙萍等，2020；钟粤俊等，2026）` | 替换为上标 `［1-2］` |
| 叙述式引用 | `Boschma（2005）认为...` | 替换为 `Boschma［73］认为...` |

Word 替换使用 `python-docx` 跨 run 处理，只在引用位置插入新 run，尽量保留原文的字体、字号、加粗、颜色等格式。

### 4. 参考文献生成与核对

生成文末参考文献时会处理：

- 按正文首次出现顺序编号。
- 同一文献重复出现时沿用同一编号。
- 连续编号合并为 `［1-3］`。
- 非连续编号写作 `［3，15，61-64］`。
- 作者名 OCR 错误、年份误标、缺逗号等问题单独记录。
- DOI 默认按目标期刊样文判断；没有明确要求时，投稿版通常不强行保留。

### 5. 西财期刊等级标注

内置西南财经大学学术期刊等级分类目录 2018 版：

```text
references/journal-levels/swufe_2018.tsv
```

可以给参考文献 Markdown 或 TSV 自动加等级：

```bash
python scripts/enrich_journal_level.py \
  tmp_参考文献_目标期刊风格.md \
  tmp_参考文献_目标期刊风格_with_level.md
```

输出示例：

```text
［1］ 黄蕙萍，缪子菊，袁野，等 . 生产性服务业的全球价值链及其中国参与度［J］. 管理世界，2020，36(9)：82 - 97.
- **期刊等级**：A+级（《管理世界》）
```

期刊不在目录中时，会标注为：

```text
- **期刊等级**：未在西财目录中（《期刊名》）
```

## 防错机制

这个 skill 专门吸收了真实论文处理中的坑：

- 文件名含中文双引号时，不硬编码路径，优先用 glob 匹配。
- 跳过通讯地址、作者单位、邮编、邮箱、地图来源、数据来源、网址等非引用内容。
- 保留原稿已有编号上标，避免重复替换。
- 处理 `余泳泽等2016` 这类缺逗号引用。
- 处理 `鉴韩峰` 这类 OCR 误字前缀。
- 对作者名笔误、年份误标、重复文献、改引经典版本等情况写入备注，不静默修正。
- 检查无卷号期刊格式，避免写成 `2025，(4)：102 - 117.`。
- 检查 DOI 是否应保留，避免投稿版参考文献冗余。

## 安装

```bash
git clone https://github.com/yichaoli921/citation-replacer.git
cd citation-replacer

python3 -m venv .venv
source .venv/bin/activate

pip install python-docx pyyaml
pip install pdfplumber requests
```

如果本机安装了 Poppler，`pdf_to_md.py` 会优先使用 `pdftotext`，PDF 转 Markdown 通常更快。

## 在 Codex 或 Claude Code 中使用

把整个 `citation-replacer/` 文件夹放到对应的 skills 目录，然后在对话里直接说：

```text
使用 citation-replacer。我要投《目标期刊名》，这是我的论文 docx，这是目标期刊最新两篇样文 PDF。请先总结该刊引用格式，再生成引用替换表和参考文献表，最后修改 Word。
```

推荐输入：

- 论文 `.docx`
- 目标期刊最新两篇样文 PDF
- 已有参考文献列表或文献检索线索
- 如果你有明确偏好，也可以说明 DOI 是否保留、是否需要西财期刊等级

## 命令行工具

| 脚本 | 用途 |
|---|---|
| `scripts/pdf_to_md.py` | PDF 转 Markdown |
| `scripts/extract_style_from_samples.py` | 从两篇样文生成目标期刊引用风格备忘 |
| `scripts/normalize_authors.py` | 作者名归一化和 OCR 容错 |
| `scripts/fetch_metadata.py` | 通过 OpenAlex / CrossRef 补全文献元数据 |
| `scripts/enrich_journal_level.py` | 用西财目录标注期刊等级 |
| `scripts/replace_citations.py` | 在 docx 中跨 run 替换正文引用 |
| `scripts/append_references.py` | 在 docx 末尾追加参考文献章节 |

## 项目结构

```text
citation-replacer/
├── SKILL.md
├── README.md
├── scripts/
│   ├── pdf_to_md.py
│   ├── extract_style_from_samples.py
│   ├── normalize_authors.py
│   ├── fetch_metadata.py
│   ├── enrich_journal_level.py
│   ├── replace_citations.py
│   └── append_references.py
├── references/
│   ├── journal-levels/
│   │   └── swufe_2018.tsv
│   ├── journal-styles/
│   │   └── 示例风格文件
│   ├── workflow-memo.md
│   ├── regex-cheatsheet.md
│   └── econ-geography-output-contract.md
├── docs/
├── examples/
└── tests/
```

## 测试

```bash
python tests/test_replace_citations.py
python tests/test_enrich_journal_level.py
```

## 适用边界

适合：

- 中文论文投稿前参考文献格式统一。
- 从目标期刊样文学习引用格式。
- Word `.docx` 中作者年份引用转编号制。
- 需要保留可复核 Markdown 中间稿的研究工作流。
- 需要标注西财期刊等级的参考文献整理。

不适合：

- 纯 LaTeX / Overleaf 项目。
- 只做 APA、MLA、IEEE 等英文格式转换。
- 不需要正文引用替换、只想简单清洗文末参考文献的任务。
- 完全不提供目标期刊样文，却要求严格匹配某刊最新格式的任务。

## License

MIT License. See [LICENSE](LICENSE).

## English

`citation-replacer` is a sample-driven citation formatting skill for Chinese academic manuscripts.

It does not assume a fixed list of supported journals. Instead, you provide your manuscript and two latest sample articles from the target journal. The skill converts PDFs to Markdown, summarizes the target journal's citation style, builds auditable citation-mapping drafts, replaces author-year citations in Word, appends the reference list, and optionally annotates journal tiers using the SWUFE 2018 journal ranking directory.

The built-in journal-style files are examples and regression-test materials, not the boundary of supported journals.
