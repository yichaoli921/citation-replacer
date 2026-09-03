# 贡献指南 / Contributing

感谢你考虑为 **citation-replacer** 做出贡献！🎉

本项目欢迎任何形式的贡献：报告 bug、改进文档、提新期刊风格、加新数据源、撰写测试。

---

## 📋 目录

- [行为准则](#-行为准则)
- [我能为项目做什么](#-我能为项目做什么)
- [开发环境](#-开发环境)
- [提 Pull Request 流程](#-提-pull-request-流程)
- [报告 Bug](#-报告-bug)
- [提 Feature Request](#-提-feature-request)
- [新增期刊风格](#-新增期刊风格)
- [新增数据源](#-新增数据源)
- [代码规范](#-代码规范)

---

## 🌟 行为准则

本项目采用 [Contributor Covenant](CODE_OF_CONDUCT.md)。参与即表示你同意遵守其条款。

---

## 💡 我能为项目做什么

| 类型 | 适合谁 | 例子 |
|---|---|---|
| 🐛 报告 Bug | 所有人 | "我用 `replace_citations.py` 处理一篇 100 页 docx 时崩溃" |
| 📝 改进文档 | 所有人 | "README 里 `Quick Start` 步骤不清" |
| 🎨 新增期刊风格 | 投稿到其他期刊的同学 | 加 `urban-planning.md`、`journal-of-finance.md` |
| 🌐 新增数据源 | 数据爱好者 | 接 CNKI API、Sci-Hub 兜底 |
| ⚡ 性能优化 | Python 老手 | 把 `replace_citations.py` 改成多进程 |
| 🧪 写测试 | QA 爱好者 | 跑 fixture 验证替换无丢失字符 |
| 🎓 学术引用 | 写论文的同学 | 在论文里引用本项目 |

---

## 🛠 开发环境

### 1. Fork & Clone

```bash
git clone https://github.com/<your-name>/citation-replacer.git
cd citation-replacer
```

### 2. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 必装
pip install python-docx pyyaml

# 可选（开发时建议都装）
pip install pdfplumber requests pytest
```

### 4. 运行 smoke test

```bash
python tests/test_replace_citations.py
python tests/test_enrich_journal_level.py
```

---

## 🔁 提 Pull Request 流程

1. **Fork** 本仓库到你的账号
2. 创建分支：`git checkout -b feature/<your-feature>` 或 `fix/<bug>`
3. 提交代码：`git commit -m "feat: 加 XX 期刊风格"`
4. 推送到你的 fork：`git push origin feature/<your-feature>`
5. 在 GitHub 上开 Pull Request
6. 等待 CI 通过 + 维护者 review

**Commit 规范**（参考 Conventional Commits）：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 仅文档
- `style:` 格式（无逻辑变更）
- `refactor:` 重构
- `test:` 测试
- `chore:` 杂项

---

## 🐛 报告 Bug

使用 [GitHub Issues](../../issues/new?template=bug_report.md) 的 bug 模板。请包含：

- 系统信息（macOS / Linux / Windows、Python 版本）
- 复现步骤
- 期望行为
- 实际行为
- 错误日志（`traceback`）
- 复现用的样本文档（如可分享）

---

## ✨ 提 Feature Request

使用 [GitHub Issues](../../issues/new?template=feature_request.md) 的 feature 模板。请说明：

- 使用场景
- 期望效果
- 替代方案

---

## 🎨 新增期刊风格

每个期刊风格是一个 `references/journal-styles/<journal-name>.md` 文件，含 YAML 配置块。

### 模板

```markdown
# 《<期刊名>》引用风格

```yaml
name: <journal-name>
display_name: 《<期刊名>》
version: 1.0
tested_on: <可选，测试用例>

# 文内引用
citation:
  bracket_open: ［ | [
  bracket_close: ］ | ]
  superscript: true
  range_separator: '-'
  discontinuous_separator: '，' | ','

# 叙述式引用
narrative:
  enabled: true
  format: '{author}［{ref}］'
  superscript: false

# 文末参考文献条目
reference_entry:
  number_format: '［{n}］ { entry' | '[{n}] {entry}'
  period_after_author: '. '
  doc_type_brackets: full_width | half_width
  page_range_separator: ' - ' | '-'
  year_separator: '，' | ', '
  volume_issue_open: '('
  volume_issue_close: ')'
  colon_before_page: '：' | ': '

# DOI 处理
doi_strategy: omit_unless_required | include

# 作者格式
authors:
  chinese_max: 3
  chinese_etc: '，等 .'
  english_max: 3
  english_etc: '，et al.'
  author_separator: '，'

# 文献类型标识
doc_types:
  journal: '［J］' | '[J]'
  monograph: '［M］' | '[M]'
  working_paper: '［R］' | '[R]'
  online_first: '［J/OL］' | '[J/OL]'

ordering: by_first_appearance
```

## 完整示例

### 正文引用
...

### 文末参考文献
...
```

### 步骤

1. 从目标期刊下载最新一期样文 2 篇
2. 用 `pdf_to_md.py` 转成 MD
3. 用 `extract_style_from_samples.py` 自动生成草稿
4. 手动核对（自动报告仅供参考）
5. 保存为 `references/journal-styles/<journal-name>.md`
6. 在 README.md "支持期刊风格" 表中加一行
7. 提 PR

---

## 🌐 新增数据源

`scripts/fetch_metadata.py` 实现 `MetadataSource` 接口：

```python
class MyDataSource(MetadataSource):
    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | | None:
        """返回 {title, journal, volume, issue, pages, doi, doc_type} 或 None"""
        ...
```

添加到 `sources` 列表即可生效。

---

## 📏 代码规范

- **Python 3.8+**，PEP 8
- **类型注解**：函数签名尽量带 type hint
- **docstring**：每个公共函数/类
- **测试**：新功能必须带测试
- **中文优先**：用户可见文案用中文，注释可中英混用

---

## ❓ 疑问？

开 [GitHub Discussion](../../discussions) 即可。

---

再次感谢！🙏