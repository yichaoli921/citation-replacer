# 正则备忘：中文论文引用识别

本文档汇总替换过程中的常用正则表达式，按"用途"组织。所有正则都经过实测，可在 Python `re` 模块直接使用（不需要 `regex` 库）。

---

## 1. 引用块检测

### 1.1 括号式引用（最常见）

匹配 `(作者，YYYY)` 或 `(作者1，YYYY; 作者2，YYYY2)` 等形态。

```python
cite_par = re.compile(
    r'[（(]'                  # 全角或半角左括号
    r'(?=[^）)]*[一-龥A-Za-z])'   # 断言：括号内至少有一个作者字符
    r'[^）)]*?'                  # 非贪婪匹配括号内文本
    r'(?<!\d)(?:19|20)\d{2}(?![0-9])'  # 19xx 或 20xx 年份（不接前后数字）
    r'[）)]'                  # 右括号
)
```

**关键点**：
- `(?=[^）)]*[一-龥A-Za-z])` —— lookahead，要求括号内有中文/英文（避免匹配 `(2020年...)` 这种没作者的）
- `(?<!\d)` 和 `(?![0-9])` —— 年份前后不能接数字（避免匹配电话号码、邮编中的"2019"）
- `[一-龥]` —— Unicode 汉字范围；`[一-鿿]` 是更宽的中日韩统一表意文字
- 非贪婪 `*?` —— 一段文本中可能有多个并列引用 `(张，2019; 王，2020)`，应分别匹配

### 1.2 叙述式引用

匹配 `作者名（YYYY）` 形态：作者名出现在正文叙述中，年份紧跟其后。

```python
narrative_pat = re.compile(
    r'(?<![0-9．。])'                # 否定：前一字符不是数字/句号（避免被上标后的句号干扰）
    r'([一-龥][一-龥 A-Za-z]{1,30}?(?:等|et\s+al\.?)?)'  # 作者名（中文 2-30 字符，可能带"等"）
    r'[（(]'
    r'(\d{4}[a-z]?(?:[；;]\s*\d{4}[a-z]?)*)'              # 一个或多个年份
    r'[）)]'
)
```

**关键点**：
- `(?<![0-9．。])` —— 防止上标 `[1]` 紧跟的句号被误识别为前文
- 中文作者名用 `[一-龥]` 起始 + 中间允许空格/英文
- `(?:` 非捕获组，仅匹配但不捕获"等"、"et al."
- 多个年份用 `;` 或 `；` 分隔

### 1.3 is_citation_block() 过滤器

```python
def is_citation_block(text: str) -> bool:
    """判断一段文本是否包含真正的引用（而非通讯地址、地图来源等）"""
    # 必须同时含作者字符 + 19xx/20xx 年份
    has_author = re.search(r'[一-龥A-Za-z]', text) is not None
    has_year = re.search(r'\b(?:19|20)\d{2}\b', text) is not None
    if not (has_author and has_year):
        return False
    # 排除地址类
    excluded = ['中国', '邮编', '通讯作者', '邮箱', '@', 'http', 'www.', 'GS(']
    if any(s in text for s in excluded):
        return False
    return True
```

---

## 2. 引用块解析

### 2.1 单个 `作者，YYYY` 解析

```python
def parse_single_cite(s: str):
    """从 '作者，YYYY' 提取 (作者, 年份)"""
    # OCR 容错：去掉"鉴"等误字前缀
    s = re.sub(r'^[鉴认议谨让论误错谬驾]+\b', '', s)
    # 兼容逗号缺失
    m = re.match(r'^\s*(.+?)\s*[,，]?\s*((?:19|20)\d{2})[a-z]?\s*$', s)
    if m:
        return m.group(1).strip(), int(m.group(2))
    return None
```

### 2.2 多引用块 `A，2020; B，2021; C and D，2022`

```python
def parse_cite_block(text: str):
    """返回 [(author, year), ...] 列表"""
    # 先按 ; 或 ； 拆分
    parts = re.split(r'[;；]', text)
    results = []
    for p in parts:
        # 每个 part 可能含 "A and B" 或 "A、B"
        for sub in re.split(r'[、，]| and |与|及', p):
            sub = sub.strip()
            if not sub:
                continue
            result = parse_single_cite(sub)
            if result:
                results.append(result)
    return results
```

### 2.3 作者名归一化

```python
def normalize_author(name: str) -> str:
    """作者名归一化：去空格、去标点、转小写"""
    name = re.sub(r'\s+', '', name)
    name = name.replace('．', '.').replace('·', '')
    return name.lower()

# "Hanneke" 和 "hanneke" 视为同一个
# "H．Lusher" 和 "H.Lusher" 视为同一个
```

---

## 3. 编号渲染

### 3.1 连续区间合并

```python
def render_ref(numbers: list[int], style: dict) -> str:
    """[1,2,3,5] → '[1-3, 5]' 或 '[1-3，5]'（取决于风格）"""
    open_b = style['citation']['bracket_open']
    close_b = style['citation']['bracket_close']
    range_sep = style['citation']['range_separator']
    disc_sep = style['citation']['discontinuous_separator']
    
    # 排序去重
    nums = sorted(set(numbers))
    parts = []
    i = 0
    while i < len(nums):
        start = nums[i]
        end = start
        while i + 1 < len(nums) and nums[i+1] == end + 1:
            i += 1
            end = nums[i]
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f'{start}{range_sep}{end}')
        i += 1
    return f'{open_b}{disc_sep.join(parts)}{close_b}'

# render_ref([1,2,3], jingji_style) → '［1-3］'
# render_ref([1,3,5], jingji_style) → '［1，3，5］'
# render_ref([1,2,3,5], jingji_style) → '［1-3，5］'
```

---

## 4. 参考文献条目检测

### 4.1 条目开头

```python
# 匹配以 ［N］ 或 [N] 开头的条目
ref_pat = re.compile(r'^[\[［]\s*(\d+)\s*[\]］]\s*(.+)')

# 例如：
# '［17］ 蒋灵多等...' → ('17', '蒋灵多等...')
```

### 4.2 错误格式检测（无卷号）

```python
# 检测错误的年份+中文逗号+期号格式
no_volume_err = re.compile(r'(\d{4})\s*，\s*\((\d+)\)')
# '2025，(4)：' 会被匹配，'2025(4)：' 不会被匹配

# 修复
fixed = no_volume_err.sub(r'\1(\2)', text)
# '2025，(4)：' → '2025(4)：'
```

### 4.3 DOI 检测

```python
doi_pat = re.compile(r'\bDOI\s*[:：]\s*\S+', re.IGNORECASE)

# 移除 DOI
cleaned = doi_pat.sub('', text).rstrip()
```

---

## 5. python-docx 跨 run 文本拼接

由于 python-docx 把段落拆成多个 run（字号、加粗等不同时分 run），引用可能跨多个 run。需要先把所有 run 文本拼起来再做匹配。

```python
def get_paragraph_full_text(paragraph):
    """返回段落完整文本 + 每个字符对应的 run 索引"""
    runs = list(paragraph.runs)
    text = ''
    char_run_idx = []
    for i, run in enumerate(runs):
        for _ in run.text:
            char_run_idx.append(i)
        text += run.text
    return text, char_run_idx
```

⚠️ **不要**修改原始 runs 列表的迭代顺序 —— 用 snapshot。

---

## 6. 常见陷阱

### 6.1 `[` vs `［`

| 字符 | Unicode | 用途 |
|---|---|---|
| `[` | U+005B | 半角，多数英文学术格式（APA, GB/T 7714）|
| `［` | U+FF3B | 全角，中文期刊风格（《经济地理》、《地理学报》）|

错误识别会出现"用半角框套全角引用"或反之。务必在脚本顶部显式定义并复用。

### 6.2 `，` vs `,`

| 字符 | Unicode | 用途 |
|---|---|---|
| `，` | U+FF0C | 全角，中文规范 |
| `,` | U+002C | 半角，英文规范 |

中文文本中出现半角逗号通常是 OCR 错误。

### 6.3 中文双引号 vs ASCII 双引号

| 字符 | Unicode | 用途 |
|---|---|---|
| `"` | U+201C | 左中文引号 |
| `"` | U+201D | 右中文引号 |
| `"` | U+0022 | ASCII 双引号 |

文件名中如果用了中文双引号，bash heredoc 会把内容切成多段，python 脚本里硬编码 ASCII 双引号会生成新文件而不是覆盖原文件。

**解决**：用 `glob.glob('【完整版】*.docx')[0]` 动态定位，不要在脚本里硬编码文件名。

---

## 7. 完整工作流示例代码

```python
import re
from docx import Document

doc = Document('input.docx')

cite_par = re.compile(
    r'[（(](?=[^）)]*[一-龥A-Za-z])'
    r'[^）)]*?(?<!\d)(?:19|20)\d{2}(?![0-9])[）)]'
)

for p in doc.paragraphs:
    if p.text == '参考文献：':
        break  # 跳过参考文献区
    if not is_citation_block(p.text):
        continue
    full_text, char_run_idx = get_paragraph_full_text(p)
    matches = list(cite_par.finditer(full_text))
    if not matches:
        continue
    
    replacements = []
    for m in matches:
        parsed = parse_cite_block(m.group(1))
        if not parsed:
            continue
        nums = [lookup_number(author, year) for author, year in parsed]
        if any(n is None for n in nums):
            continue
        ref_str = render_ref([n for n in nums if n], STYLE)
        replacements.append((m.start(), m.end(), ref_str))
    
    apply_replacements(p, replacements)
```

---

## 8. 测试用例

```python
# 应该匹配
assert cite_par.search('(黄蕙萍等，2020)') is not None
assert cite_par.search('（宣烨和余泳泽，2017）') is not None
assert cite_par.search('(张虎等，2017; 唐晓华等，2018)') is not None

# 不应该匹配（地址类）
assert cite_par.search('（1.西南财经大学，611130；2.中国四川，成都 611130）') is None
# → is_citation_block() 返回 False，含"中国"和"邮编"

# 不应该匹配（数字年份无作者）
assert cite_par.search('（2020年3月）') is None
# → lookahead 失败

# 不应该匹配（年份前后接数字）
assert cite_par.search('（邮编 201901）') is None
# → (?<!\d) 失败
```

---

*测试环境：Python 3.11 + python-docx 0.8.11*
*最新更新：2026-09-03*