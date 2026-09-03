# 工作流踩坑备忘（与现有 `tmp_工作流_参考文献生成.md` 互通）

> 本文档收录实际工作中遇到的所有坑、原因、解决方式。新遇到的问题请追加在末尾。
> 与 `~/Desktop/欣桐科研记录/国内大循环/反投经济地理/tmp_工作流_参考文献生成.md` 互通：那边记录的是本轮工作流原始时间线；这里是 skill 化后保留的硬规则。

---

## A. 文件名问题

### A.1 文件名含中文双引号（`"`/`"`）

**症状**：脚本里 hardcode 了 ASCII `"..."`，结果创建了**新文件**而不是覆盖原文件，原始 docx 没动过。

**原因**：UTF-8 中文双引号是 `e2 80 9c` 和 `e2 80 9d`，与 ASCII `"`（`22`）不同。

**解决**：
```python
import glob
SRC = glob.glob('【完整版】*.docx')[0]

# 或
from pathlib import Path
SRC = next(Path('.').glob('【完整版】*.docx'))
```

**延伸教训**：写脚本前，先用 `print(repr(filename))` 看字节，验证是不是中文双引号。

---

## B. 正则问题

### B.1 正则过宽：把通讯地址当成引用

**症状**：P3 段落 `（1.西南财经大学...611130；2.中国四川，成都 611130）` 被当成引用。

**原因**：原始正则 `[\(（][^\)）]*(19|20)\d{2}[\)）]` 没限制必须有"作者字符"。

**解决**：加 lookahead + `is_citation_block()` 双重过滤：

```python
cite_par = re.compile(
    r'[（(]'
    r'(?=[^）)]*[一-龥A-Za-z])'   # 必须含作者字符
    r'[^）)]*?'
    r'(?<!\d)(?:19|20)\d{2}(?![0-9])'
    r'[）)]'
)

def is_citation_block(text):
    has_author = re.search(r'[一-龥A-Za-z]', text)
    has_year = re.search(r'\b(?:19|20)\d{2}\b', text)
    if not (has_author and has_year):
        return False
    if any(s in text for s in ['中国', '邮编', '通讯作者', '邮箱', '@', 'http', 'www.', 'GS(', '数据来源']):
        return False
    return True
```

### B.2 正则过严：英文 "et al." 匹配失败

**症状**：第一版正则对 "al.，2024" 失败。

**原因**：`[一-龥A-Za-z]\s*[,，]?\s*(?:19|20)\d{2}` 中 `.` 不在 `[,，]?` 范围。

**解决**：简化 `is_citation_block` 只检查"含字符 + 含年份"。

### B.3 缺逗号匹配

**症状**：`余泳泽等2016`（缺逗号）。

**解决**：
```python
r'(.+?)\s*[,，]?\s*((?:19|20)\d{2})'
```

### B.4 OCR 误字前缀

**症状**：`鉴韩峰和阳立高，2020` —— "鉴" 是 OCR 误字。

**解决**：解析作者名前先 `re.sub(r'^[鉴认议谨让论误错谬驾]+\b', '', s)`。

### B.5 叙述式引用漏处理

**症状**：`Boschma（2005）`、`Hanneke等（2010）` 没改。

**原因**：第一版正则只匹配 `(作者，YYYY)`，没考虑作者名进正文。

**解决**：加第二种正则：

```python
NARRATIVE_PAT = re.compile(
    r'(?<![0-9．。])'
    r'([一-龥][一-龥 A-Za-z]{1,30}?(?:等|et\s+al\.?)?)'
    r'[（(]'
    r'(\d{4}[a-z]?(?:[；;]\s*\d{4}[a-z]?)*)'
    r'[）)]'
)
```

| 形态 | 处理 |
|---|---|
| `(张，2020)` | 整段替换为上标 `［N］` |
| `张（2020）` | 仅替换 `(2020)` 部分为 `［N］`（叙述式不上标）|

### B.6 全角 vs 半角括号

中英文括号混杂：`（...）` 全角 vs `(...)` 半角。匹配时都要覆盖。

---

## C. python-docx 跨 run 问题

### C.1 addnext 参数类型错误

```
TypeError: Argument 'element' has incorrect type (expected lxml.etree._Element, got Run)
```

**解决**：`first_run._element.addnext(new_run._element)` 传入 `_element`。

### C.2 索引偏移

**解决**：
- 第一行 `runs = list(paragraph.runs)` 拍快照
- 用 `affected = sorted(set(char_run_idx[start:end]))` 取受影响索引
- 倒序遍历 `replacements`

### C.3 引用块跨 run 处理

```python
if first_run is last_run:
    t = first_run.text
    first_run.text = t[:start_in_first] + t[end_in_last:]
else:
    first_run.text = first_run.text[:start_in_first]
    for ri in affected[1:-1]:
        runs[ri].text = ''
    last_run.text = last_run.text[end_in_last:]
```

---

## D. 格式规范问题

### D.1 作者后空格

**用户偏好**：`黄蕙萍 . 题名`——句点后必须空格。

### D.2 "等" 后空格

`余泳泽，等 . 题目`——"等" 后是 ` .`（半角点+空格）。

### D.3 "et al." 不加空格

`Hanneke，et al.` —— "et al." 前有逗号，后无空格。

### D.4 无卷号格式

**错误**：`2025，(4)：102 - 117.`
**正确**：`2025(4)：102 - 117.`

修复：`re.sub(r'(\d{4})\s*，\s*\((\d+)\)', r'\1(\2)', text)`

### D.5 DOI 处理

**用户偏好**：投稿版参考文献列表**默认不写 DOI**，除非编辑部明确要求。

判断：
- 期刊已正式刊出 → 删 DOI
- J/OL 网络首发未转正式刊 → 可保留 DOI
- 编辑部明确要求 → 保留

### D.6 文献类型标识

| 类型 | 中文期刊（《经济地理》）| GB/T 7714 |
|---|---|---|
| 期刊 | `［J］` | `[J]` |
| 专著 | `［M］` | `[M]` |
| 报告/工作论文 | `［R］` | `[R]` |
| 网络首发 | `［J/OL］` | `[J/OL]` |

---

## E. OCR 与用户校对问题（本轮已确认）

| 原稿 | 实际 | 处理 |
|---|---|---|
| 张虎等，2019 | 张虎等，2017 | 改 [13] |
| 唐晓华等，2024 | 唐晓华等，2018 | 改 [20] |
| 潘强等，2025 | 潘珊，李剑培，顾乃华 | OCR 误字，改 [11] |
| 鉴韩峰和阳立高 | 韩峰和阳立高 | OCR 误字前缀，改 [76] |
| Castells，1999 | Castells，1996《网络社会的崛起》 | 改引经典版，改 [66] |
| Lusher，2013 | 与 Lusher et al. 2013 同 | 删除 [76]，合并到 [69] |

---

## F. PDF → MD 处理

### F.1 用本 skill 自带脚本

优先用本 skill 自带的 `scripts/pdf_to_md.py` 处理 PDF 输入，并把输出写成 `.md`：

```bash
python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md
```

### F.2 退回 pdftotext

如果脚本不可用，可直接调用 `pdftotext` 后把文本保存为 Markdown：

```bash
pdftotext -layout -enc UTF-8 input.pdf output.txt
```

或 Python pdfplumber：

```python
import pdfplumber
with pdfplumber.open('input.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```

### F.3 不要直接用机器翻译 PDF 当作最终 MD

只是参考，最终要人工整理。

---

## G. 性能与可靠性

### G.1 docx 文件路径不可硬编码

每次脚本运行前 `print(glob.glob('*.docx'))` 确认。

### G.2 修改前先备份

```python
import shutil
shutil.copy(SRC, SRC + '.bak')
```

### G.3 验证脚本必须跑

替换完后跑 4 项检查：
1. 残留扫描（author-year 形式）
2. 上标计数
3. 参考文献条目数
4. 编号连续性

任一不通过都不可宣称"完成"。

### G.4 期刊等级标注失败处理

`enrich_journal_level.py` 标"未在目录中"时：
1. 检查期刊名是否有 OCR/笔误
2. 检查是否是 2018 后新刊（目录可能没收录）
3. 检查期刊名是否有别名（如《经济研究》vs《Economic Research Journal》）

---

## H. 风格学习问题（两篇目标期刊样本）

### H.0 PDF 必须先落成 Markdown

**症状**：只打开 PDF 视觉阅读，后续无法复查样文依据，也无法稳定抽取文内引用和文末参考文献。

**规则**：任何输入 PDF，包括目标期刊样文和论文正文 PDF，都先运行：

```bash
python scripts/pdf_to_md.py "<pdf path or glob>" --out-dir tmp_md
```

风格备忘必须列出 PDF 原路径和转换后的 `.md` 路径。

### H.1 选样本的要点

- **最新一期**：避免参考过期规范
- **正刊不是增刊**：增刊可能有临时格式
- **同一作者**：避免不同作者风格差异（如果可能）

### H.2 风格报告字段覆盖

| 项 | 检查方法 |
|---|---|
| 方括号 | regex `［N］` vs `[N]` |
| 编号分隔符 | 连续 `-` vs 非连续 `，` |
| 作者分隔 | 中英文逗号 |
| "等" vs "et al." | 出现频次 |
| 文献类型 | ［J］/［M］/［R］/［J/OL］ |
| DOI 处理 | 是否保留 |
| 卷(期)冒号 | 全角 vs 半角 |
| 页码格式 | 半角空格-dash vs 全角连字符 |

### H.3 风格报告不等于最终配置

报告只是参考。先整理成 `tmp_<期刊>文献引用风格.md`；最终风格文件 `references/journal-styles/<name>.md` 要用户核对后才能定稿。

### H.4 三份 Markdown 中间稿

《经济地理》风格任务至少保留：

| 文件 | 用途 |
|---|---|
| `tmp_经济地理文献引用风格.md` | 两篇样文总结出的引用规范 |
| `tmp_经济地理文献引用.md` | 正文替换对照表、综合引用替换表、文末编号 |
| `tmp_参考文献_经济地理风格.md` | 完整参考文献、期刊等级、存疑和待补 |

这些文件是复核证据链，不是可选草稿。

---

## I. 交付前清单

- [ ] 原文件已备份（`*.bak`）
- [ ] 每一个输入 PDF 都已转成 `.md`
- [ ] 两篇目标期刊最新样文已转成 `.md` 并生成风格备忘
- [ ] 已生成正文替换对照稿，如 `tmp_经济地理文献引用.md`
- [ ] 已生成参考文献等级稿，如 `tmp_参考文献_经济地理风格.md`
- [ ] 输出文件名与原文件名一致（含中文双引号）
- [ ] 残留扫描 0
- [ ] 上标数 = 显式引用数
- [ ] 参考文献条目数 = 编号最大值
- [ ] 编号 1-N 连续
- [ ] OCR/年份笔误已与用户核对
- [ ] 无卷号格式已修复
- [ ] DOI 处理已确认
- [ ] 叙述式引用已处理
- [ ] 期刊等级已用 `references/journal-levels/swufe_2018.tsv` 标注，不凭印象写 A/B/C

---

*最后更新：2026-09-03*
*适用范围：中文 docx 论文，引用格式转换*
