# 样例：从头到尾跑一遍

> 本文档以 `【完整版】20260817-返-"点—圈—网"视角下生产性服务业城市网络的结构特征与演化动力(1).docx` 为样例，展示完整工作流。

---

## 0. 文件准备

```bash
cd ~/Desktop/欣桐科研记录/国内大循环/反投经济地理/

ls *完整版*.docx
# 【完整版】20260817-返-"点—圈—网"视角下生产性服务业城市网络的结构特征与演化动力(1).docx

# 注意：文件名含中文双引号（UTF-8: e2 80 9c...e2 80 9d）
```

---

## 1. 备份原文件

```python
import shutil, glob
SRC = glob.glob('*完整版*.docx')[0]
shutil.copy(SRC, 'tmp_用户原稿_中文引号备份.docx')
print(f'已备份：{SRC} → tmp_用户原稿_中文引号备份.docx')
```

---

## 2. docx → md（pandoc）

```bash
SRC=$(ls *完整版*.docx | head -1)
pandoc "$SRC" -o tmp_副本转换稿.md

# 查看引用清单
grep -oE '（[^）]+[0-9]{4}[^）]*）' tmp_副本转换稿.md | head -30
```

---

## 3. 提取引用清单 → cite_map.tsv

### 3.1 从 md 提取所有 `(作者，YYYY)` 块

```python
import re
import csv

with open('tmp_副本转换稿.md', 'r', encoding='utf-8') as f:
    md = f.read()

cite_par = re.compile(
    r'[（(](?=[^）)]*[一-龥A-Za-z])'
    r'[^）)]*?(?<!\d)(?:19|20)\d{2}(?![0-9])[）)]'
)

cite_pairs = []
for m in cite_par.finditer(md):
    inner = m.group(0)[1:-1]
    for sub in re.split(r'[;；]', inner):
        sub = sub.strip()
        # 拆 "作者1和作者2，YYYY" → 多个
        for s in re.split(r'[、，]|和|与|及', sub):
            s = s.strip()
            mm = re.match(r'(.+?)\s*[,，]?\s*((?:19|20)\d{2})', s)
            if mm:
                cite_pairs.append((mm.group(1).strip(), int(mm.group(2))))

print(f'提取到 {len(cite_pairs)} 条原始引用（含重复）')

# 写入临时映射
with open('cite_map_raw.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['author', 'year'])
    for a, y in cite_pairs:
        w.writerow([a, y])
```

### 3.2 人工/联网补全 → cite_map.tsv（带编号）

```python
# 用户手动整理 + 联网补全后得到的最终映射表
# 格式：author\tyear\tnumber
# 共 76 条，按正文首次出现顺序编号 1-76

cite_map = [
    ('黄蕙萍等', 2020, 1),
    ('钟粤俊等', 2026, 2),
    ('宣烨和余泳泽', 2017, 3),
    # ... 共 76 条 ...
    ('韩峰和阳立高', 2020, 76),  # 原文 "鉴韩峰"，OCR 误字
]

with open('cite_map.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['author', 'year', 'number'])
    for a, y, n in cite_map:
        w.writerow([a, y, n])
```

---

## 4. 联网补全（可选）

```bash
python scripts/fetch_metadata.py cite_map.tsv cite_map_full.tsv
# 自动查 OpenAlex + CrossRef，CNKI 留空待手动补全
```

如果 OpenAlex 命中率低，可手动从 CNKI 网页复制元数据填入。

---

## 5. python-docx 跨 run 替换

```bash
python scripts/replace_citations.py \
    "*完整版*.docx" \
    cite_map.tsv \
    jingji-dili \
    tmp_尝试_已替换引用.docx

# 输出：
# → 风格：jingji-dili，映射表 76 条
# → 已备份到 ...docx.bak
# ✅ 完成 N 处替换
# → 输出：tmp_尝试_已替换引用.docx
```

脚本会：
1. glob 匹配原 docx（避免文件名双引号问题）
2. 自动备份
3. 扫描所有段落，跳过参考文献
4. 处理括号式 + 叙述式两种引用
5. 替换为上标 `［N-M］` 或 `［N，M，K-L］`

---

## 6. 追加参考文献章节

### 6.1 准备 refs.tsv

```python
# 参考文献条目（人工整理 + 联网补全）
refs = [
    '黄蕙萍，缪子菊，袁野，等 . 生产性服务业的全球价值链及其中国参与度［J］. 管理世界，2020，36(9)：82 - 97.',
    '钟粤俊，陆铭 . 户籍与土地：城镇化进程中两要素如何再配置［R］. 工作论文，2026.',
    '宣烨，余泳泽 . 生产性服务业集聚对制造业企业全要素生产率提升研究——来自230个城市微观企业的证据［J］. 数量经济技术经济研究，2017，34(2)：89 - 104.',
    # ... 共 76 条 ...
]

with open('refs.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    for i, ref in enumerate(refs, 1):
        w.writerow([i, ref])
```

### 6.2 在 docx 中追加

**先手动**：在 docx 末尾（最后一个正文段落后）插入段落，文本为 `参考文献：`

```bash
python scripts/append_references.py \
    tmp_尝试_已替换引用.docx \
    refs.tsv \
    jingji-dili \
    tmp_尝试_已替换引用_最终版.docx

# 输出：✅ 追加 76 条参考文献
```

---

## 7. 验证

```python
from docx import Document
from docx.oxml.ns import qn
import re

doc = Document('tmp_尝试_已替换引用_最终版.docx')

# 1. 残留扫描
cite_pat = re.compile(r'[（(][^）()]*?(?<!\d)(?:19|20)\d{2}(?![0-9])[）)]')
residual = 0
for p in doc.paragraphs:
    if p.text == '参考文献：':
        break
    for m in cite_pat.findall(p.text):
        if re.search(r'[一-龥A-Za-z]', m[1:-1]):
            if not any(s in m for s in ['GS', '中国', '邮编', '数据来源']):
                residual += 1
                print(f'  残留：{p.text[:80]}... -> {m}')
print(f'残留 author-year 引用：{residual} 处')

# 2. 上标计数
super_count = 0
for p in doc.paragraphs:
    for r in p.runs:
        rPr = r._element.find(qn('w:rPr'))
        if rPr is not None:
            vert = rPr.find(qn('w:vertAlign'))
            if vert is not None and vert.get(qn('w:val')) == 'superscript':
                super_count += 1
print(f'上标 run 数：{super_count}')

# 3. 参考文献条目数
refs = [p.text for p in doc.paragraphs if re.match(r'［\d+］', p.text)]
print(f'参考文献条目数：{len(refs)}')

# 4. 编号连续性
nums = sorted([int(re.match(r'［(\d+)］', r).group(1)) for r in refs])
print(f'编号范围：{nums[0]} - {nums[-1]}，连续：{nums == list(range(nums[0], nums[-1]+1))}')
```

期望输出：
```
残留 author-year 引用：0 处
上标 run 数：29（+5 原稿已有）
参考文献条目数：76
编号范围：1 - 76，连续：True
```

---

## 8. 投稿前人工核对

| 项 | 说明 |
|---|---|
| OCR 笔误 | 张虎→2017、唐晓华→2018、潘强→潘珊、Castells→1996、鉴韩峰→韩峰 |
| DOI 处理 | 默认删除，除非编辑部要求 |
| 无卷号格式 | `2025，(4)：` → `2025(4)：` |
| 叙述式引用 | Boschma（2005）、Hanneke等（2010）等需手工核对 |
| 参考文献正文引用一致性 | 编号 1-76 是否在正文都有引用 |

---

## 9. 覆盖原文件

```python
import shutil, glob
SRC = glob.glob('*完整版*.docx')[0]
DST = 'tmp_尝试_已替换引用_最终版.docx'

# ⚠️ 用中文双引号原文件名覆盖
shutil.copy(DST, SRC)
print(f'✅ 已覆盖：{SRC}')
```

---

## 完整产物清单

| 文件 | 用途 |
|---|---|
| `tmp_用户原稿_中文引号备份.docx` | 原文件备份 |
| `tmp_副本转换稿.md` | docx → md |
| `cite_map_raw.tsv` | 自动提取的原始引用 |
| `cite_map.tsv` | 人工+联网整理后的 76 条映射 |
| `cite_map_full.tsv` | 含元数据的完整映射 |
| `refs.tsv` | 参考文献条目 |
| `tmp_尝试_已替换引用.docx` | 仅替换引用，无参考文献 |
| `tmp_尝试_已替换引用_最终版.docx` | 完整最终版 |
| `【完整版】...原文件.docx` | 覆盖后的最终稿 |
| `*.docx.bak` | 脚本自动备份 |

---

*本样例展示完整 7 步流程。实际使用时可根据需要跳过联网步骤（手动补全更快）。*