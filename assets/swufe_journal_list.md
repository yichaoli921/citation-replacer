# 西南财经大学学术期刊等级分类目录（2018 版）

## 用途

`enrich_journal_level.py` 自动给参考文献条目标注期刊等级（A+/A/B/C），原始数据来自此目录。

## 文件位置

- TSV：`references/journal-levels/swufe_2018.tsv`（4849 条期刊）
- 源 PDF：`/Users/zncumac/Desktop/超博士科研/学院相关制度/西南财经大学学术期刊等级分类目录（2018版）.pdf`

## TSV 格式

```
category    level    number    name                    code
中文A+级期刊    A+级     1        中国社会科学                 CN11-1211/C
中文A+级期刊    A+级     2        经济研究                   CN11-1081/F
中文A+级期刊    A+级     3        管理世界                   CN11-1235/F
经济学        A级       3        金融研究                   CN11-1268/F
人文经济地理    A级       1        地理学报                   CN11-1856/P
人文经济地理    A级       3        经济地理                   CN43-1126/K
人文经济地理    B级       5        地理研究                   CN11-1848/P
```

## 使用方式

```bash
# 默认用法：用内置西财 2018 目录
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv

# 或指定自己的目录
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv my_journals.tsv

# Markdown 输入（直接补到参考文献稿中）
python scripts/enrich_journal_level.py refs.md refs_with_level.md
```

## 抽查常用期刊

| 期刊 | 等级 | 类别 |
|---|---|---|
| 中国社会科学 | A+级 | 中文A+级期刊 |
| 经济研究 | A+级 | 中文A+级期刊 |
| 管理世界 | A+级 | 中文A+级期刊 |
| 中国工业经济 | A级 | 经济学 |
| 数量经济技术经济研究 | A级 | 经济学 |
| 经济地理 | A级 | 人文经济地理 |
| 地理学报 | A级 | 人文经济地理 |
| 地理研究 | B级 | 人文经济地理 |
| 改革 | B级 | 经济学 |
| 金融研究 | A级 | 经济学 |
| 产业经济研究 | B级 | 经济学 |
| 世界经济研究 | B级 | 经济学 |
| Urban Studies | A+级 | GEOGRAPHY（英文A+级）|

## 局限

1. **2018 版**：2018 后的新刊可能不在目录中
2. **CN 号匹配**：英文期刊用 ISSN，部分期刊因 ISSN 与正文格式不符可能漏匹配
3. **同名异刊**：极少数期刊有同名异刊现象（如《中国社会科学》有多个 ISSN）
4. **更新**：如需最新版（2023/2024），需重新提供 PDF 并跑 `parse_journals.py`

## 自定义目录

如果用户有自定义期刊目录（如最新 2024 版），按以下 TSV 格式即可：

```tsv
category    level    number    name                    code
<分类>       <等级>    <序号>    <期刊名>                <CN号或ISSN>
```

调用时指定：

```bash
python scripts/enrich_journal_level.py refs.tsv output.tsv my_journals.tsv
```

## 解析脚本

如果用户更新了源 PDF，重新解析：

```python
# scripts/parse_journals.py（已在 /tmp/swufe_journals/）
# 1. pdftotext -layout -enc UTF-8 source.pdf raw.txt
# 2. python parse_journals.py  → swufe_2018.tsv
```

把生成的 tsv 替换到 `references/journal-levels/swufe_2018.tsv` 即可。

---

*最后更新：2026-09-03*