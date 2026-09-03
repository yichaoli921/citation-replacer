#!/usr/bin/env python3
"""
Create a citation-style memo from two target-journal sample PDFs or Markdown files.

Usage:
  python scripts/extract_style_from_samples.py sample1.pdf sample2.pdf -o tmp_经济地理文献引用风格.md
  python scripts/extract_style_from_samples.py tmp_md/sample1.md tmp_md/sample2.md -o style_report.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PDF_TO_MD = SCRIPT_DIR / "pdf_to_md.py"


def ensure_md(path: Path, out_dir: Path) -> Path:
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return path
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported sample file: {path}")
    proc = subprocess.run(
        [sys.executable, str(PDF_TO_MD), str(path), "--out-dir", str(out_dir)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return out_dir / f"{path.stem}.md"


def collect_examples(text: str) -> dict[str, list[str]]:
    numbered = re.findall(r"［\d+(?:[-，,]\d+)*］|\[\d+(?:[-,]\d+)*\]", text)
    refs = re.findall(r"^[［\[]\d+[］\]].+$", text, flags=re.MULTILINE)
    author_year = re.findall(r"[（(][^）)]*(?:19|20)\d{2}[^）)]*[）)]", text)
    return {
        "numbered": numbered[:20],
        "refs": refs[:20],
        "author_year": author_year[:20],
    }


def infer(texts: list[str]) -> dict[str, str]:
    joined = "\n".join(texts)
    full_width = len(re.findall(r"［\d+", joined))
    half_width = len(re.findall(r"\[\d+", joined))
    ranges = Counter(re.findall(r"［\d+([-,，])\d+［?", joined))
    doc_types = Counter(re.findall(r"［(J/OL|J|M|R|D|C)］", joined))
    doi_count = len(re.findall(r"\bDOI\s*[:：]", joined, flags=re.I))
    ref_lines = re.findall(r"^[［\[]\d+[］\]].+$", joined, flags=re.MULTILINE)
    no_volume_bad = len(re.findall(r"\d{4}，\(\d+\)：", joined))
    no_volume_good = len(re.findall(r"\d{4}\(\d+\)：", joined))
    return {
        "citation_system": "顺序编码制" if full_width or half_width else "未识别，需人工核对",
        "brackets": "全角方括号 ［］" if full_width >= half_width else "半角方括号 []",
        "range_separator": "连字符 -" if "-" in ranges else "需人工核对",
        "discontinuous_separator": "中文逗号 ，" if "，" in ranges else "需人工核对",
        "doc_types": "、".join(k for k, _ in doc_types.most_common()) or "需人工核对",
        "doi": "样文保留 DOI" if doi_count else "样文未见 DOI，默认不写",
        "no_volume": (
            "YYYY(期)：页码"
            if no_volume_good >= no_volume_bad
            else "YYYY，(期)：页码（需核对，可能不符合既有教训）"
        ),
        "ref_count": str(len(ref_lines)),
    }


def render_report(samples: list[Path], md_paths: list[Path], texts: list[str], journal: str) -> str:
    stats = infer(texts)
    examples = [collect_examples(t) for t in texts]
    lines = [
        f"# 《{journal}》文献引用与参考文献风格备忘",
        "",
        "依据样文：",
        "",
    ]
    for src, md in zip(samples, md_paths):
        lines.append(f"- `{src}` → `{md}`")
    lines += [
        "",
        "## 1. 文内引用",
        "",
        f"- 引用制度：{stats['citation_system']}",
        f"- 方括号：{stats['brackets']}",
        f"- 连续编号：{stats['range_separator']}",
        f"- 非连续编号：{stats['discontinuous_separator']}",
        "- 叙述式引用需按样文核对；中文顺序编码制通常保留作者名，年份括号替换为编号。",
        "",
        "样文编号示例：",
    ]
    for ex in examples:
        for item in ex["numbered"][:5]:
            lines.append(f"- `{item}`")
    lines += [
        "",
        "## 2. 文末排序",
        "",
        "- 默认判断为按正文首次出现顺序编号；如样文参考文献与正文首次出现不一致，必须人工标注例外。",
        f"- 样文中识别到文末编号条目约 {stats['ref_count']} 条。",
        "",
        "## 3. 中文期刊论文格式",
        "",
        "- 按样文核对作者截断、作者后空格、文献类型、年份卷期页码。",
        f"- 无卷号期刊格式倾向：`{stats['no_volume']}`。",
        "",
        "## 4. 英文期刊论文格式",
        "",
        "- 按样文核对英文作者缩写、`et al.`、题名大小写、期刊名和页码/文章号。",
        "",
        "## 5. 报告/工作论文格式",
        "",
        f"- 样文文献类型标识：{stats['doc_types']}",
        "",
        "## 6. DOI 处理",
        "",
        f"- {stats['doi']}。投稿版默认不写 DOI，除非样文稳定保留、J/OL 网络首发或编辑部明确要求。",
        "",
        "## 7. 文末参考文献样例",
        "",
    ]
    for ex in examples:
        for item in ex["refs"][:8]:
            lines.append(f"- `{item}`")
    lines += [
        "",
        "## 8. 后续处理规则",
        "",
        "1. 按正文首次出现顺序编号。",
        "2. 同一文献多次出现只保留首次编号。",
        "3. 作者-年份式引用统一转换为编号式引用。",
        "4. 脚注、数据来源、地图来源、网页材料不要混入学术参考文献，除非正文明确作为文献引用。",
        "5. 补全文献时核对题名、期刊、年份、卷期、页码、DOI 和英文作者缩写。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", nargs="+", help="Two target-journal PDFs/MDs")
    parser.add_argument("-o", "--output", default="style_report.md")
    parser.add_argument("--journal", default="经济地理")
    parser.add_argument("--tmp-dir", default="tmp_md")
    args = parser.parse_args()

    if len(args.samples) < 2:
        print("Need at least two latest target-journal sample articles.", file=sys.stderr)
        return 1
    sample_paths = [Path(p) for p in args.samples[:2]]
    tmp_dir = Path(args.tmp_dir)
    md_paths = [ensure_md(p, tmp_dir) for p in sample_paths]
    texts = [p.read_text(encoding="utf-8", errors="ignore") for p in md_paths]
    Path(args.output).write_text(
        render_report(sample_paths, md_paths, texts, args.journal),
        encoding="utf-8",
    )
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
