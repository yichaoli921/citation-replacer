#!/usr/bin/env python3
"""
enrich_journal_level.py
自动给参考文献条目加 **期刊等级**：A+级/A级/B级/C级

依据：西南财经大学学术期刊等级分类目录（2018 版）

依赖：python（无需 requests）
运行：
  python enrich_journal_level.py <refs.tsv> <output.tsv>
  python enrich_journal_level.py refs.md refs_with_level.md

refs.tsv 格式：number\tentry
Markdown 输入：含 ［N］ 作者 . 题名［J］. 期刊名，年份... 的参考文献稿
TSV 输出：number\tentry\tjournal\tlevel
Markdown 输出：在期刊条目下方插入 - **期刊等级**：A+级（《期刊名》）
"""

import sys
import csv
import re
from pathlib import Path

# ============================================================
# 默认期刊目录路径（西财 2018 版）
# ============================================================
DEFAULT_JOURNAL_TSV = (
    Path(__file__).parent.parent
    / 'references' / 'journal-levels' / 'swufe_2018.tsv'
)


def load_journal_levels(tsv_path: Path = DEFAULT_JOURNAL_TSV) -> dict[str, str]:
    """
    返回 {期刊名: 等级} 字典
    期刊名归一化（去空格、全角转半角）以兼容不同写法
    同名期刊取最高级（A+ > A > B > C）
    """
    if not tsv_path.exists():
        print(f'⚠️  未找到期刊目录 {tsv_path}，跳过等级标注', file=sys.stderr)
        return {}

    LEVEL_RANK = {'A+级': 4, 'A级': 3, 'B级': 2, 'C级': 1}

    levels: dict[str, str] = {}

    def _better(a: str, b: str) -> str:
        return a if LEVEL_RANK.get(a, 0) >= LEVEL_RANK.get(b, 0) else b

    with tsv_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            name = row['name'].strip()
            level = row['level'].strip()
            if not name or not level:
                continue
            # 同名取最高级
            levels[name] = _better(levels.get(name, level), level)
            norm = normalize_journal_name(name)
            levels[norm] = _better(levels.get(norm, level), level)
    return levels


def normalize_journal_name(name: str) -> str:
    """期刊名归一化"""
    name = re.sub(r'\s+', '', name)
    name = name.replace('．', '.').replace('（', '(').replace('）', ')')
    return name.lower()


def match_journal(entry: str, levels: dict[str, str]) -> tuple[str, str] | None:
    """
    从参考文献条目提取期刊名，返回 (journal_name, level)
    中文期刊：[J]. 期刊名，
    英文期刊：Journal Name, Year,
    """
    # 中文：［J］/［J/OL］. 期刊名，年份
    m = re.search(r'［J(?:/OL)?］\s*\.?\s*([^,，]+)[,，]', entry)
    if m:
        journal = m.group(1).strip()
        norm = normalize_journal_name(journal)
        level = levels.get(journal) or levels.get(norm)
        if level:
            return (journal, level)
        # 模糊匹配：去掉"中文"前缀等
        for k, v in levels.items():
            if k in journal or journal in k:
                return (journal, v)
        return (journal, '未在目录中')

    # 英文：Journal, Year 或 Journal，Year
    m = re.search(r'\.\s*([A-Z][^,，]+)[,，]\s*(?:19|20)\d{2}', entry)
    if m:
        journal = m.group(1).strip()
        norm = normalize_journal_name(journal)
        level = levels.get(journal) or levels.get(norm)
        if level:
            return (journal, level)
        # 模糊匹配
        for k, v in levels.items():
            if k in journal or journal in k:
                return (journal, v)
        return (journal, '未在目录中')

    return None


def format_level_line(journal: str, level: str) -> str:
    if not journal:
        return '- **期刊等级**：未识别'
    if level and level != '未在目录中':
        return f'- **期刊等级**：{level}（《{journal}》）'
    return f'- **期刊等级**：未在西财目录中（《{journal}》）'


def enrich(refs_tsv: str, output_tsv: str = '', journal_tsv: str = ''):
    """主函数"""
    levels = load_journal_levels(
        Path(journal_tsv) if journal_tsv else DEFAULT_JOURNAL_TSV
    )
    print(f'→ 加载期刊目录 {len(levels)} 条', file=sys.stderr)

    in_path = Path(refs_tsv)
    out_path = Path(output_tsv) if output_tsv else in_path.with_name(
        in_path.stem + '_with_level.tsv' )

    with in_path.open('r', encoding='utf-8') as fin, \
         out_path.open('w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin, delimiter='\t')
        writer = csv.writer(fout, delimiter='\t')
        writer.writerow(['number', 'entry', 'journal', 'level'])
        header = next(reader, None)
        n_with = 0
        n_without = 0
        for row in reader:
            if len(row) < 2:
                continue
            num, entry = row[0].strip(), row[1].strip()
            result = match_journal(entry, levels)
            if result:
                journal, level = result
                if level != '未在目录中':
                    n_with += 1
                else:
                    n_without += 1
                writer.writerow([num, entry, journal, level])
            else:
                writer.writerow([num, entry, '', ''])
                n_without += 1

    print(f'✅ 输出 {out_path}', file=sys.stderr)
    print(f'   匹配成功 {n_with} 条，未匹配 {n_without} 条', file=sys.stderr)


def enrich_markdown(input_md: str, output_md: str = '', journal_tsv: str = ''):
    """给 Markdown 参考文献稿中的期刊条目补期刊等级行。"""
    levels = load_journal_levels(
        Path(journal_tsv) if journal_tsv else DEFAULT_JOURNAL_TSV
    )
    in_path = Path(input_md)
    out_path = Path(output_md) if output_md else in_path.with_name(
        in_path.stem + '_with_level.md'
    )
    lines = in_path.read_text(encoding='utf-8').splitlines()
    out: list[str] = []
    n_with = 0
    n_without = 0
    ref_line = re.compile(r'^\s*[［\[]\d+[］\]]\s+')
    level_line = re.compile(r'^\s*-\s+\*\*期刊等级\*\*')

    for i, line in enumerate(lines):
        out.append(line)
        if not ref_line.match(line):
            continue
        if '［J' not in line and '[J' not in line:
            continue
        next_line = lines[i + 1] if i + 1 < len(lines) else ''
        if level_line.match(next_line):
            continue
        result = match_journal(line, levels)
        if result:
            journal, level = result
            out.append(format_level_line(journal, level))
            if level != '未在目录中':
                n_with += 1
            else:
                n_without += 1
        else:
            out.append('- **期刊等级**：未识别')
            n_without += 1

    out_path.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')
    print(f'✅ 输出 {out_path}', file=sys.stderr)
    print(f'   匹配成功 {n_with} 条，未匹配 {n_without} 条', file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print('用法：python enrich_journal_level.py <refs.tsv|refs.md> [output.tsv|output.md] [journal_tsv]')
        print('默认期刊目录：references/journal-levels/swufe_2018.tsv（西财 2018 版）')
        sys.exit(1)

    refs_tsv = sys.argv[1]
    output_tsv = sys.argv[2] if len(sys.argv) > 2 else ''
    journal_tsv = sys.argv[3] if len(sys.argv) > 3 else ''
    if Path(refs_tsv).suffix.lower() in {'.md', '.markdown'}:
        enrich_markdown(refs_tsv, output_tsv, journal_tsv)
    else:
        enrich(refs_tsv, output_tsv, journal_tsv)


if __name__ == '__main__':
    main()
