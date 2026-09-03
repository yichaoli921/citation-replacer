# 《地理学报》引用风格

```yaml
name: dili-xuebao
display_name: 《地理学报》
version: 1.0

# 文内引用
citation:
  bracket_open: ［
  bracket_close: ］
  superscript: true
  range_separator: '-'
  discontinuous_separator: '，'

# 叙述式引用
narrative:
  enabled: true
  format: '{author}［{ref}］'
  superscript: false

# 文末参考文献条目
reference_entry:
  number_format: '［{n}］ {entry}'
  number_separator: ' '
  period_after_author: '. '
  doc_type_brackets: full_width
  page_range_separator: ' - '
  year_separator: '，'
  volume_issue_open: '('
  volume_issue_close: ')'
  colon_before_page: '：'

# DOI 处理
- doi_strategy: include             # 默认保留 DOI

# 作者格式
authors:
  chinese_max: 3
  chinese_etc: '，等 .'
  english_max: 3
  english_etc: '，et al.'
  author_separator: '，'

# 文献类型标识
doc_types:
  journal: '［J］'
  monograph: '［M］'
  working_paper: '[R]'              # 报告用半角
  online_first: '［J/OL］'

ordering: by_first_appearance
```

## 与《经济地理》的差异

几乎一致，主要差异：
1. DOI 默认保留（地理学报倾向）
2. 报告 [R] 用半角方括号

## 完整示例

### 正文引用

```text
已有研究并未达成共识［1-3］。
城市网络研究方法多样［5-8］。
```

### 文末参考文献

```text
参考文献：

［1］ 王姣娥，景悦 . 中国城市网络等级结构特征及组织模式——基于铁路和航空流的比较［J］. 地理学报，2017，72(8)：1508 - 1519.

［5　熊丽芳，甄峰，王波，等 . 基于百度指数的长三角核心区城市网络特征研究［J］. 经济地理，2013，33(7)：67 - 73.
```

## 注意事项

- 地理学报倾向要求 DOI，可在投稿时根据编辑部意见调整