# 示例 / Examples

本目录包含可运行的最小示例。

## 文件清单

| 文件 | 说明 |
|---|---|
| `refs_demo.tsv` | 一个示例 refs.tsv，含 8 条参考文献 |
| `cite_map_demo.tsv` | 一个示例 cite_map.tsv，含 8 条 author-year 映射 |
| `journal_query_demo.py` | 演示如何调用 `enrich_journal_level.py` 的核心函数 |

## 使用示例

### 1. 给示例参考文献标注期刊等级

```bash
cd ..
python scripts/enrich_journal_level.py examples/refs_demo.tsv examples/refs_with_level.tsv
cat examples/refs_with_level.tsv
```

### 2. 测试 render_ref 函数

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from replace_citations import render_ref, DEFAULT_STYLE

print(render_ref([1, 2, 3], DEFAULT_STYLE))   # ［1-3］
print(render_ref([1, 3, 5], DEFAULT_STYLE))   # ［1，3，5］
print(render_ref([1, 2, 15, 16, 17], DEFAULT_STYLE))  # ［1-2，15-17］
```

### 3. 测试 match_journal 函数

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from enrich_journal_level import load_journal_levels, match_journal

levels = load_journal_levels()
result = match_journal(
    '黄蕙萍，缪子菊，袁野，等 . 题名［J］. 管理世界，2020，36(9)：82 - 97.',
    levels,
)
print(result)  # ('管理世界', 'A+级')
```

---

## 完整流程示例

假设你有一篇 docx 论文 `paper.docx`，按以下步骤处理：

```bash
# Step 1: 备份
cp paper.docx paper.docx.bak

# Step 2: 提取引用清单
python scripts/normalize_authors.py paper.md > cite_map.tsv
# 手动整理 cite_map.tsv（去重、补全）

# Step 3: 准备参考文献
# （人工整理 / OpenAlex 补全 / 用户提供）
# 输出 refs.tsv

# Step 4: 期刊等级标注
python scripts/enrich_journal_level.py refs.tsv refs_with_level.tsv

# Step 5: 跨 run 替换
python scripts/replace_citations.py paper.docx cite_map.tsv jingji-dili paper_replaced.docx

# Step 6: 追加参考文献
python scripts/append_references.py paper_replaced.docx refs_with_level.tsv jingji-dili paper_final.docx

# Step 7: 验证
python tests/test_replace_citations.py
```

---

*最后更新：2026-09-03*