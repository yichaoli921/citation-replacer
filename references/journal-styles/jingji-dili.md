# 《经济地理》期刊引用风格

```yaml
name: jingji-dili
display_name: 《经济地理》
version: 1.0
tested_on: 2026-09-02, "点—圈—网"视角下生产性服务业城市网络的结构特征与演化动力

# 文内引用
citation:
  bracket_open: ［     # 全角左方括号
  bracket_close: ］   # 全角右方括号
  superscript: true   # 上标
  range_separator: '-'        # 连续编号 [1-3]
  discontinuous_separator: '，'  # 非连续 [1，3，5]

# 叙述式引用
narrative:
  enabled: true
  format: '{author}［{ref}］'  # Boschma（2005）→ Boschma［73］
  superscript: false  # 叙述式不上标

# 文末参考文献条目
reference_entry:
  number_format: '［{n}］ {entry}'   # 条目开头
  number_separator: ' '              # 编号与作者间空格
  period_after_author: '. '          # 作者后是 ". "（半角句点 + 空格）
  doc_type_brackets: full_width      # 文献类型用 ［J］/［M］/／[R]/［J/OL］
  page_range_separator: ' - '        # 页码范围用半角 " - "
  year_separator: '，'               # 年份用中文逗号
  volume_issue_open: '('             # 卷(期)
  volume_issue_close: ')'
  colon_before_page: '：'             # 2024，39(8)：51

# DOI 处理
doi_strategy: omit_unless_required   # 默认不写 DOI；编辑部明确要求则保留

# 作者格式
authors:
  chinese_max: 3         # 中文前 3 位全列，第 4 位起 "等"
  chinese_etc: '，等 .'  # "等" 前有中文逗号，后空格再点半角点
  english_max: 3
  english_etc: '，et al.'  # "et al." 前有中文逗号
  author_separator: '，'   # 作者之间用中文逗号

# 文献类型标识
doc_types:
  journal: '［J］'
  monograph: '［M］'
  working_paper: '［R］'
  online_first: '［J/OL］'

# 排序规则
ordering: by_first_appearance  # 按正文首次出现顺序编号
```

## 完整示例

### 正文引用

```text
已有文献并未达成完全共识［1-2］。
生产性服务业集聚对制造业效率有显著影响［3，15，61-64］。
多维邻近性的研究表明……Boschma［73］关于多维邻近性的讨论表明……
```

### 文末参考文献

```text
参考文献：

［1］ 黄蕙萍，缪子菊，袁野，等 . 生产性服务业的全球价值链及其中国参与度［J］. 管理世界，2020，36(9)：82 - 97.

［3］ 宣烨，余泳泽 . 生产性服务业集聚对制造业企业全要素生产率提升研究——来自230个城市微观企业的证据［J］. 数量经济技术经济研究，2017，34(2)：89 - 104.

［73］ Boschma R A . Proximity and Innovation：A Critical Assessment［J］. Regional Studies，2005，39(1)：61 - 74.
```

## 注意事项

1. **作者后空格**：作者和句点之间、句点和题名之间都要有空格：`黄蕙萍 . 题名` 不是 `黄蕙萍.题名`
2. **`等` 后空格**：`，等 .` 不是 `，等.`
3. **`et al.` 不空格**：`，et al.` 不是 `， et al.`
4. **DOI 默认不写**：除非编辑部明确要求
5. **无卷号格式**：`2025(4)：` 不要写成 `2025，(4)：`
6. **页码连字符**：用半角 ` - ` 加空格，不是 `－`

## 不适用范围

- 英文论文（用其他格式如 APA/MLA）
- 期刊缩写：保留期刊英文原名（如 `Journal of Economic Geography` 不缩写）
