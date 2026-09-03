---
name: citation-replacer
description: "Convert Chinese academic papers and target-journal sample PDFs into Markdown-backed citation workflows: summarize journal citation style from two latest sample articles, replace author-year in-text citations in docx with numbered references, append a reference section, and annotate journal levels from the bundled SWUFE 2018 directory. Use for 参考文献, 统一引用格式, 按目标期刊格式整理引用, PDF 样文, 作者-年份改编号, and similar Chinese academic citation tasks. Do not use for LaTeX papers, English-only APA/MLA/IEEE work, or bibliography cleanup without citation-style decisions."
---

# Citation Replacer Skill

## Scope

Use this skill when you need to convert a **Chinese academic paper** to a target journal's citation style. The skill handles three main flows:

1. **PDF / DOCX → MD**：自动把任何喂入的 PDF 转成 MD，方便后续编辑和引用提取
2. **Style learning**：从两篇目标期刊最新文章样本中提取该期刊的引用规范
3. **Citation conversion**：把 author-year 引用 → 编号上标，并在文末追加参考文献
4. **Journal-level annotation**：自动给每条参考文献加 **期刊等级**：A+/A/B/C 级（基于西南财经大学 2018 版目录）

## When to Trigger

Trigger when the user mentions any of:

- 参考文献 / 添加参考文献 / 整理参考文献
- 统一引用格式 / 按 XX 期刊格式 / 按《XX》期刊
- 把作者-年份改成编号 / change citations to numbered format / standardize reference list
- 看看我这篇文献引用对不对 / 帮我整理一下参考文献
- 我要投《XX》期刊，请整理为该刊格式
- 期刊等级 / 西财期刊目录 / A级期刊

Do NOT trigger for:

- LaTeX / Overleaf papers
- English-only APA / MLA / IEEE / Vancouver
- 纯参考文献列表清理（已用编号格式的论文）

## Bundled Resources

```
citation-replacer/
├── SKILL.md                              # 本文件
├── references/
│   ├── journal-styles/
│   │   ├── jingji-dili.md               # 《经济地理》（已测试）
│   │   ├── gb-t-7714.md                 # GB/T 7714-2015 国标通用
│   │   └── dili-xuebao.md               # 《地理学报》
│   ├── journal-levels/
│   │   └── swufe_2018.tsv               # 西财 2018 版期刊等级目录（4849 条）
│   ├── regex-cheatsheet.md              # 各种引用检测正则
│   ├── workflow-memo.md                 # 历史踩坑（OCR、文件双引号、叙述式引用、DOI、无卷号等）
│   └── econ-geography-output-contract.md # 三类中间稿输出契约（风格备忘/参考对照/等级稿）
├── scripts/
│   ├── replace_citations.py             # 跨 run 替换主脚本
│   ├── append_references.py             # 追加参考文献章节
│   ├── fetch_metadata.py                # 联网拉取元数据（OpenAlex/CrossRef/CNKI 占位）
│   ├── normalize_authors.py             # 作者名归一化（OCR 容错）
│   ├── enrich_journal_level.py          # 自动标注期刊等级（A+/A/B/C，支持 Markdown 输出）
│   ├── extract_style_from_samples.py    # 两篇目标期刊样本 → 风格报告
│   └── pdf_to_md.py                     # PDF → MD 转换（pdftotext/pdfplumber/pypdf）
└── assets/
    └── sample_workflow.md               # 完整工作样例
```

## Workflow (9 Steps)

```
[1] 备份原文件                       → <filename.bak>
[2] PDF → MD（若原文件是 PDF）       → scripts/pdf_to_md.py
[3] docx → MD（pandoc）              → 提取引用清单
[4] Style learning：两篇目标期刊样本  → 自动生成 style 配置
[5] 提取所有 (作者，YYYY)            → 初步映射表
[6] 联网补全缺项（OpenAlex/CrossRef） → cite_map_full.tsv
[7] 期刊等级标注                     → refs_with_level.tsv
[8] python-docx 跨 run 替换          → 上标 ［N-M］
[9] 追加参考文献章节 + 验证           → 最终输出
```

每步对应：

| Step | 工具 / Script | 输入 | 输出 |
|---|---|---|---|
| 1 | `cp` | 原文件 | `<file>.bak` |
| 2 | `scripts/pdf_to_md.py` | `*.pdf` | `<file>.md` |
| 3 | `pandoc` | `*.docx` | `<file>.md` |
| 4 | `scripts/extract_style_from_samples.py` | 两篇 PDF/MD | `tmp_<期刊>文献引用风格.md` |
| 5 | `scripts/normalize_authors.py` | `<file>.md` | `cite_map.tsv` |
| 6 | `scripts/fetch_metadata.py` | `cite_map.tsv` | `cite_map_full.tsv` |
| 7 | `scripts/enrich_journal_level.py` | `refs.tsv` 或参考文献 Markdown | `refs_with_level.tsv` 或带等级 Markdown |
| 8 | `scripts/replace_citations.py` | `<file>.docx` + `cite_map_full.tsv` | `<file>_replaced.docx` |
| 9 | `scripts/append_references.py` | `<file>_replaced.docx` + `refs_with_level.tsv` | `<file>_final.docx` |

### Step 2 详细：PDF → MD

优先用本地脚本（自动 fallback）：

```bash
python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md
```

支持三种提取器（按优先级）：
1. `pdftotext`（poppler，最快）
2. `pdfplumber`（中文友好）
3. `pypdf`（Python 原生）

不允许跳过 Markdown 落盘步骤；后续抽取引用、判断风格、生成表格都以 `.md` 为依据。

### Step 4 详细：Style learning（两篇目标期刊样本）

目标期刊最新一期的两篇文章作为样本，提取该期刊的引用规范：

```bash
python scripts/extract_style_from_samples.py \
    "/path/to/target_journal_paper1.pdf" \
    "/path/to/target_journal_paper2.pdf" \
    -o style_report.md
```

报告输出：
- 方括号类型（全角 vs 半角）
- 编号分隔符（连续 - vs 非连续 ，）
- 作者分隔符（中文 vs 英文）
- "等" vs "et al." 使用频率
- 文献类型标识（［J］/［M］/［R］/［J/OL］）
- DOI 处理（保留 vs 不写）
- 卷(期) 冒号（全角 vs 半角）
- 页码格式（半角空格-dash vs 全角连字符）

把报告结果整理成 `tmp_<期刊>文献引用风格.md`；若该风格以后要复用，再沉淀为 `references/journal-styles/<journal_name>.md`。

《经济地理》任务必须读 `references/econ-geography-output-contract.md`，并生成：

- `tmp_经济地理文献引用风格.md`：两篇样文的引用风格备忘
- `tmp_经济地理文献引用.md`：正文替换对照表、综合引用替换表、文末参考文献
- `tmp_参考文献_经济地理风格.md`：完整参考文献、期刊等级、存疑/待补说明

### Step 7 详细：期刊等级标注

依据西南财经大学学术期刊等级分类目录（2018 版）：

```bash
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv
```

若输入是 Markdown 参考文献稿，脚本会在每条期刊文献下方插入等级行：

```bash
python scripts/enrich_journal_level.py \
    tmp_参考文献_经济地理风格.md \
    tmp_参考文献_经济地理风格_with_level.md
```

输出每条参考文献对应期刊的等级：

```
number  entry                                              journal         level
1       黄蕙萍，缪子菊，袁野，等 . ... . 管理世界，2020...  管理世界        A+级
2       Taylor P J ... . Urban Studies，2002...             Urban Studies   A+级
3       Liu Y ... . International Review of Econ...         International Review of Economics & Finance   未在目录中
```

- 默认期刊目录：`references/journal-levels/swufe_2018.tsv`（4849 条，覆盖中文 A+/A/B/C 级和英文 A+/A/B/C 级）
- 输出格式：`- **期刊等级**：A+级（《管理世界》）`
- 期刊不在目录中 → 标记 `未在西财目录中（《期刊名》）`
- 用户可指定自己的目录：`<journal_tsv>`

## Citation Style Selection

| Style | File | Bracket | Period | DOI 默认 |
|---|---|---|---|---|
| **《经济地理》** | `jingji-dili.md` | `［］` 全角 | `. ` 半角 | 不写（默认）|
| **GB/T 7714** | `gb-t-7714.md` | `[]` 半角 | `. ` 半角 | 保留 |
| **《地理学报》** | `dili-xuebao.md` | `［］` 全角 | `. ` 半角 | 保留 |
| **目标期刊** | `extract_style_from_samples.py` 自动生成 | — | — | — |

切换风格：脚本顶部 `STYLE = load_style('<name>')`。

## Critical Constraints（不能犯的错——基于本轮工作沉淀）

> 这些是从 `tmp_工作流_参考文献生成.md`、`tmp_经济地理文献引用风格.md`、`tmp_经济地理文献引用.md` 提炼的硬规则。

### 1. 不能动其他 run 的格式

- 只在引用位置**插入**新的上标 run
- 不修改既有 run 的字号、字体、加粗、颜色
- 新 run 必须 `deepcopy` 原 first_run 的 rPr，只额外加 `superscript=True`

### 2. 跳过非引用块

通讯地址、地图来源虽含 `(...)` 但不是引用。用 `is_citation_block()` 过滤：

```python
if re.search(r'(中国.{1,4}省|邮编|通讯作者|邮箱|@\w|http|www\.)', text):
    return False
if not (re.search(r'[一-龥A-Za-z]', text) and re.search(r'\b(?:19|20)\d{2}\b', text)):
    return False
```

### 3. 文件名含中文双引号时不替换

用户文件名经常含中文 `"..."`（UTF-8: `e2 80 9c`...`e2 80 9d`），**不要**用 ASCII `"` 替换。

```python
# 错误：硬编码 ASCII 双引号
src = '【完整版】20260817-返-"点—圈—网"...docx'  # 这是 ASCII!

# 正确：glob 动态匹配
import glob
files = glob.glob('【完整版】*.docx')
```

### 4. 保留原稿已有的上标

如果原稿已经有 `［1-2］`、`［3-4］` 等上标，**不要**重复处理。正则 `（...)` 不会匹配 `[]`，继续用 `（...)` 模式可自动跳过。

### 5. OCR 容错

| 错误类型 | 示例 | 处理 |
|---|---|---|
| 误字前缀 | `鉴韩峰和阳立高` | `re.sub(r'^鉴', '', s)` |
| 缺逗号 | `余泳泽等2016` | 正则 `(.+?)[,，]?\s*((?:19|20)\d{2})` |
| 年份笔误 | `张虎等，2019`（实为 2017） | 用户确认后改 mapping |
| 作者笔误 | `潘强等`（实为潘珊） | 用户确认后改 mapping |

### 6. 两种引用形式都要处理

中文论文里有**两种**引用方式：

| 形式 | 形态 | 处理 |
|---|---|---|
| 括号式 | `(作者，YYYY)` 整段在括号 | 整段替换为上标 `［N-M］` |
| **叙述式** | `作者（YYYY）` 作者名进入正文 | 仅替换 `(YYYY)` 部分为 `［N］`（非上标） |

叙述式样例（本轮漏掉的 3 处）：
- `Boschma（2005）...` → `Boschma［73］...`
- `Hanneke等（2010）和Leifeld等（2018）...` → `Hanneke等［70］和Leifeld等［71］...`
- `Hanneke等（2010）...` → `Hanneke等［70］...`

### 7. DOI 处理（用户偏好）

**默认不写 DOI**，除非编辑部明确要求保留网络首发 DOI。

判断规则：
- 期刊已正式刊出 → 删 DOI
- J/OL 网络首发未转正式刊 → 可保留 DOI
- 编辑部明确要求 → 保留

### 8. 无卷号期刊格式

**错误**：`2025，(4)：102 - 117.`
**正确**：`2025(4)：102 - 117.`

修复：`re.sub(r'(\d{4})\s*，\s*\((\d+)\)', r'\1(\2)', text)`

### 9. 跨 run 类型错误

`first_run._element.addnext(new_run)` ❌
`first_run._element.addnext(new_run._element)` ✅

### 10. 索引偏移

倒序遍历 `replacements` 列表，避免先处理前面后索引偏移。

## Verification Checklist

```python
from docx import Document
from docx.oxml.ns import qn
import re

doc = Document('output.docx')

# 1. 残留 author-year 扫描
cite_pat = re.compile(r'[（(][^）()]*?(?<!\d)(?:19|20)\d{2}(?![0-9])[）)]')
residual = 0
for p in doc.paragraphs:
    if p.text == '参考文献：':
        break
    for m in cite_pat.findall(p.text):
        if re.search(r'[一-龥A-Za-z]', m[1:-1]):
            if not any(s in m for s in ['GS', '中国', '邮编', '数据来源']):
                residual += 1

# 2. 上标计数
super_count = 0
for p in doc.paragraphs:
    for r in p.runs:
        rPr = r._element.find(qn('w:rPr'))
        if rPr is not None:
            vert = rPr.find(qn('w:vertAlign'))
            if vert is not None and vert.get(qn('w:val')) == 'superscript':
                super_count += 1

# 3. 参考文献条目数 + 连续性
refs = [p.text for p in doc.paragraphs if re.match(r'［\d+］', p.text)]
nums = sorted([int(re.match(r'［(\d+)］', r).group(1)) for r in refs])

print(f'残留 {residual}，上标 {super_count}，参考文献 {len(refs)} 条，编号 {nums[0]}-{nums[-1]}')
assert residual == 0
assert nums == list(range(nums[0], nums[-1]+1))
```

## Known Limitations

1. **不支持 LaTeX/Overleaf** —— 仅 docx
2. **不支持图表注、表格内引用** —— 仅正文段落（待扩展）
3. **OCR 误字识别有限** —— 仅处理已知模式（"鉴"前缀、缺逗号）
4. **联网补全需联网** —— CNKI 自动抓取未实现（需手动补全）
5. **西财期刊目录为 2018 版** —— 部分 2018 后的新刊会显示"未在目录中"

## Final Checks (交付前)

- [ ] 原文件已备份
- [ ] 所有输入 PDF 已转成 MD，并在风格备忘中记录 PDF 与 MD 路径
- [ ] 两篇目标期刊最新样文已总结为 `tmp_<期刊>文献引用风格.md`
- [ ] 正文引用映射已整理为 `tmp_<期刊>文献引用.md`
- [ ] 参考文献等级稿已整理为 `tmp_参考文献_<期刊>风格.md`
- [ ] 残留 author-year 引用 = 0
- [ ] 上标 run 数 = 显式引用数
- [ ] 参考文献条目数 = 编号最大值
- [ ] 编号 1-N 连续无缺
- [ ] 期刊等级已根据 `references/journal-levels/swufe_2018.tsv` 标注，不凭记忆判断
- [ ] OCR / 年份笔误已与用户核对
- [ ] 无卷号格式已修复
- [ ] DOI 处理已确认
- [ ] 叙述式引用已处理（包括作者名后括号年份形式）

## Version

- v1.1 (2026-09-03) — 集成 PDF→MD、style learning、期刊等级自动标注
- v1.0 (2026-09-03) — Initial release
- Tested on: 《"点—圈—网"视角下生产性服务业城市网络的结构特征与演化动力》（西南财经大学）
- Python deps: `python-docx>=0.8.10`, `pyyaml`, `pdfplumber`（可选）, `requests`
