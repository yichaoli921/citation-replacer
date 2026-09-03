# 架构说明 / Architecture

本文档从代码组织、数据流、扩展点三个角度说明 `citation-replacer` 的内部设计。

---

## 一、总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│  输入                                                            │
│  ├── 中文 docx 论文（含 author-year 引用）                          │
│  ├── 目标期刊最新 2 篇 PDF/MD 样文                                  │
│  └── 用户提供的引用清单（可选）                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1：风格学习（可选）                                          │
│  scripts/extract_style_from_samples.py                            │
│  → tmp_<期刊>文献引用风格.md                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2：PDF→MD（如果原文件是 PDF）                                │
│  scripts/pdf_to_md.py                                             │
│  → <input>.md                                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3：引用抽取与映射                                            │
│  scripts/normalize_authors.py → cite_map_raw.tsv                  │
│  scripts/fetch_metadata.py → cite_map_full.tsv                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4：期刊等级标注                                              │
│  scripts/enrich_journal_level.py                                  │
│  → refs_with_level.tsv                                            │
│  (内置 references/journal-levels/swufe_2018.tsv)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5：docx 跨 run 替换                                         │
│  scripts/replace_citations.py                                     │
│  → <input>_replaced.docx                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6：追加参考文献章节                                           │
│  scripts/append_references.py                                     │
│  → <input>_final.docx                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 7：验证                                                     │
│  (内置脚本，见 tests/test_replace_citations.py)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                          最终 docx
```

---

## 二、模块依赖

```
SKILL.md
  ↓
scripts/
  ├── replace_citations.py  ← 核心，依赖 python-docx + yaml
  ├── append_references.py  ← 核心，依赖 python-docx
  ├── enrich_journal_level.py  ← 核心，依赖内置 swufe_2018.tsv
  ├── extract_style_from_samples.py  ← 可选，依赖 pdfplumber/pdftotext
  ├── normalize_authors.py  ← 工具
  ├── fetch_metadata.py  ← 可选，依赖 requests
  └── pdf_to_md.py  ← 工具，pdftotext/pdfplumber/pypdf fallback

references/
  ├── journal-styles/*.md  ← YAML 配置，被 replace_citations.py 读取
  ├── journal-levels/swufe_2018.tsv  ← TSV，被 enrich_journal_level.py 读取
  ├── regex-cheatsheet.md  ← 文档
  ├── workflow-memo.md  ← 文档
  └── econ-geography-output-contract.md  ← 文档

tests/
  ├── test_replace_citations.py  ← 引用替换单元测试
  └── test_enrich_journal_level.py  ← 期刊等级单元测试
```

---

## 三、关键数据流

### 3.1 cite_map.tsv 格式

```tsv
author	year	number
黄蕙萍等	2020	1
钟粤俊等	2026	2
宣烨和余泳泽	2017	3
...
```

由用户从正文抽取，或由 `normalize_authors.py` 自动生成。

### 3.2 refs.tsv 格式

```tsv
number	entry
1	黄蕙萍，缪子菊，袁野，等 . 生产性服务业的全球价值链及其中国参与度［J］. 管理世界，2020，36(9)：82 - 97.
2	钟粤俊，奚锡灿，陆铭 . 与时俱进的统一大市场...［J］. 经济研究，2026，61(1)：119 - 142.
...
```

由用户整理（CNKI / CrossRef / OpenAlex 联网补全 + 手动核对）。

### 3.3 refs_with_level.tsv（enrich 输出）

```tsv
number	entry	journal	level
1	黄蕙萍，缪子菊，袁野，等 . ... . 管理世界，2020...	管理世界	A+级
2	钟粤俊，奚锡燦，陆铭 . ... . 经济研究，2026...	经济研究	A+级
...
```

---

## 四、扩展点

### 4.1 新增期刊风格

在 `references/journal-styles/<name>.md` 添加 YAML 配置块。

详见 [CONTRIBUTING.md §新增期刊风格](../CONTRIBUTING.md)。

### 4.2 新增数据源

在 `scripts/fetch_metadata.py` 实现 `MetadataSource` 接口，加入 `sources` 列表。

```python
class MySource(MetadataSource):
    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | None:
        ...
```

### 4.3 更新期刊目录

替换 `references/journal-levels/swufe_2018.tsv`。

如有新 PDF，重新解析：

```python
# 用 /tmp/swufe_journals/parse_journals.py
pdftotext -layout -enc UTF-8 <新PDF>.pdf raw.txt
python parse_journals.py
```

### 4.4 自定义输出契约

参考 `references/econ-geography-output-contract.md` 的格式，新增期刊对应的契约文件。

---

## 五、关键算法

### 5.1 跨 run 替换

详见 [regex-cheatsheet.md](../references/regex-cheatsheet.md) § 5。

核心：
1. `runs = list(paragraph.runs)` 拍快照
2. 拼接 `full_text`，记录 `char_run_idx`
3. 匹配 `(作者，YYYY)` → `(start, end, ref_str)` 列表
4. **倒序**遍历避免索引偏移
5. 对每个匹配：
   - 取 `affected = sorted(set(char_run_idx[start:end]))`
   - 新建上标 run（deepcopy first_run 的 rPr + 加 superscript）
   - `first_run._element.addnext(new_run._element)` 移动到正确位置
   - 修改受影响 run 的 text

### 5.2 编号渲染

`render_ref([1,2,3,5], style)`：

1. 排序去重
2. 连续区间合并：`1,2,3 → 1-3`，`5 → 5`
3. 用 `range_separator`（`-`）连接
4. 用 `discontinuous_separator`（`，` 或 `,`）分隔多个区间

### 5.3 期刊等级匹配

`match_journal(entry, levels)`：

1. 中文：`re.search(r'［J(?:/OL)?］\s*\.?\s*([^,，]+)[,，]', entry)` 提取期刊名
2. 英文：`re.search(r'\.\s*([A-Z][^,，]+)[,，]\s*(?:19|20)\d{2}', entry)`
3. 归一化查字典
4. 模糊匹配（`k in journal or journal in k`）
5. 都不中 → 标 "未在目录中"

---

## 六、性能与限制

| 项 | 限制 |
|---|---|
| docx 大小 | < 1000 页（内存内全部加载） |
| 期刊目录 | 4849 条（西财 2018） |
| 引用并发 | 单进程（python-docx 非线程安全） |
| PDF 提取 | 中文表格可能识别不完整 |

---

## 七、安全保证

1. **不动其他 run 格式**：`new_run._element.insert(0, deepcopy(rPr_src))` 后只额外加 `superscript=True`
2. **跳过非引用块**：`is_citation_block()` 多重过滤
3. **保留已有上标**：正则只匹配 `(作者，YYYY)`，不匹配 `[N]`
4. **自动备份**：每个脚本入口都先 `shutil.copy` 备份
5. **glob 文件定位**：避免硬编码中文双引号文件名

---

*最后更新：2026-09-03*