# 常见问题 / FAQ

---

## Q1: 我应该把 PDF 还是 docx 喂给脚本？

**A**：本 skill 主要处理 docx（用 `python-docx` 跨 run 替换）。如果原文件是 PDF：

1. 用 `scripts/pdf_to_md.py` 转成 MD
2. 用 MD 作为引用抽取的输入
3. 用 docx 作为最终替换的目标

---

## Q2: PDF 转 MD 后表格乱了怎么办？

**A**：这是 PDF 提取的固有问题。三个引擎各有优劣：

| 引擎 | 优点 | 缺点 |
|---|---|---|
| `pdftotext`（poppler）| 快 | 表格乱 |
| `pdfplumber` | 中文友好 | 复杂表格仍乱 |
| `pypdf` | Python 原生 | 中文支持弱 |

**建议**：
- 简单论文 → `pdftotext -layout`
- 复杂表格论文 → 手修 MD 或用 Word 重新编辑
- 学术严谨场景 → 用 Adobe Acrobat 导出 MD

---

## Q3: 为什么我处理后正文还是有一些 `(作者，YYYY)` 残留？

**A**：可能是以下原因之一：

1. **叙述式引用漏处理**：检查脚本是否启用了 narrative 模式
2. **OCR 误字太严重**：作者名无法匹配 cite_map，脚本跳过该位置
3. **跨 run 替换失败**：报告 bug 并附 docx 片段
4. **通讯地址类假阳性**：被 `is_citation_block()` 过滤（这其实是正确的）

排查命令：

```python
from docx import Document
import re
doc = Document('output.docx')
pat = re.compile(r'[（(][^）()]*?(?<!\d)(?:19|20)\d{2}(?![0-9])[）)]')
for p in doc.paragraphs:
    if p.text == '参考文献：':
        break
    for m in pat.findall(p.text):
        print(p.text[:80], '->', m)
```

---

## Q4: 期刊不在西财 2018 目录中怎么办？

**A**：三种方式：

1. **接受标记**：`enrich_journal_level.py` 会标 "未在目录中"，你可以保留这个标记
2. **更新目录**：从西财研究生院/科研处下载最新版 PDF，重新解析：

```bash
pdftotext -layout -enc UTF-8 新版期刊目录.pdf raw.txt
python parse_journals.py
```

3. **自定义目录**：自己做一个 TSV，按相同格式（`category\tlevel\tnumber\tname\tcode`）：

```bash
python scripts/enrich_journal_level.py refs.tsv out.tsv my_journals.tsv
```

---

## Q5: 为什么叙述式引用 `Boschma（2005）` 被改成了 `Boschma［73］` 但没上标？

**A**：这是设计。两种引用形式的处理不同：

| 形式 | 形态 | 处理 |
|---|---|---|
| 括号式 | `(张，2020)` | 整段替换为**上标** `［1-2］` |
| 叙述式 | `张（2020）` | 仅替换 `(2020)` 为**平排** `［N］`，保留作者名 |

叙述式不转为上标的原因是：作者名已经是正文叙述的一部分，上标会破坏阅读节奏。

如果需要强制上标，可修改 `replace_citations.py` 中的 `process_paragraph()` 函数。

---

## Q6: 替换后上标的字号和正文不一致？

**A**：不会！脚本强制 `deepcopy` first_run 的 rPr，仅加 `superscript=True`：

```python
rPr_src = first_run._element.find(qn('w:rPr'))
if rPr_src is not None:
    new_run._element.insert(0, deepcopy(rPr_src))
new_run.font.superscript = True
```

如果还是不一致，可能是：

1. 原稿同一引用跨多个 run，first_run 是 `（` 那个 run
2. 原稿 rPr 信息丢失（如 LibreOffice 编辑过的 docx）

请报告 bug 并附 docx。

---

## Q7: 我想投一个 skill 里没有的期刊怎么办？

**A**：

1. 从该期刊官网下载最新一期 2 篇文章
2. 用 `pdf_to_md.py` 转成 MD
3. 用 `extract_style_from_samples.py` 自动生成风格草稿
4. 在 `references/journal-styles/<name>.md` 创建新文件
5. 在 README.md "支持期刊风格" 表加一行
6. 提 PR 分享给社区

---

## Q8: DOI 我应该写还是不写？

**A**：本 skill 的默认（`jingji-dili.md` 风格）是**不写 DOI**，除非：

- J/OL 网络首发未转正式刊
- 编辑部明确要求

判断规则见 `references/workflow-memo.md` § D.5。

其他期刊风格参考：
- 《地理学报》→ 默认**保留** DOI
- GB/T 7714 → 默认**保留** DOI

投稿前请查目标期刊最新一期样文确认。

---

## Q9: 编号是按作者拼音排还是正文首次出现？

**A**：所有内置期刊风格都是**按正文首次出现顺序**编号（顺序编码制）。

不是按作者拼音，也不是按发表年份。

---

## Q10: 我的论文是英文（投 SSci 期刊）能用吗？

**A**：部分可以，但有限：

- ✅ 英文 author-year 引用 → 英文编号引用
- ✅ 跨 run 替换逻辑
- ⚠️ 内置风格都是中文期刊
- ⚠ 没有 APA / MLA / IEEE 等英文格式

如果你需要投 SSci，建议：

1. 用 `extract_style_from_samples.py` 从目标期刊学习风格
2. 参考 GB/T 7714 风格（半角方括号，接近 SSci 习惯）

---

## Q11: 处理大文件很慢怎么办？

**A**：当前是单进程顺序处理。可优化方向：

- 多进程（按段落分块）—— 见 v1.2 路线图
- 只处理指定段落范围（当前默认全部正文段落）

---

## Q12: 怎么联系作者？

- GitHub Issues：报告 bug 或提问
- Email：在 GitHub 个人页面查看

---

*最后更新：2026-09-03*