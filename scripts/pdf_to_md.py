#!/usr/bin/env python3
"""
Convert one or more PDF files to lightweight Markdown text files.

Usage:
  python scripts/pdf_to_md.py paper.pdf
  python scripts/pdf_to_md.py "samples/*.pdf" --out-dir tmp_md

The script prefers Poppler's pdftotext when available, then falls back to
pdfplumber or pypdf if those packages are installed.
"""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path


def extract_with_pdftotext(pdf: Path) -> str | None:
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    proc = subprocess.run(
        [exe, "-layout", "-enc", "UTF-8", str(pdf), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def extract_with_pdfplumber(pdf: Path) -> str | None:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return None
    pages: list[str] = []
    with pdfplumber.open(str(pdf)) as doc:
        for i, page in enumerate(doc.pages, 1):
            text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            pages.append(f"\n\n<!-- page {i} -->\n\n{text}")
    return "\n".join(pages)


def extract_with_pypdf(pdf: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return None
    reader = PdfReader(str(pdf))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        pages.append(f"\n\n<!-- page {i} -->\n\n{text}")
    return "\n".join(pages)


def pdf_to_md(pdf: Path, out_dir: Path | None = None) -> Path:
    out = (out_dir or pdf.parent) / f"{pdf.stem}.md"
    text = (
        extract_with_pdftotext(pdf)
        or extract_with_pdfplumber(pdf)
        or extract_with_pypdf(pdf)
    )
    if text is None:
        raise RuntimeError(
            "No PDF text extractor available. Install poppler/pdftotext, "
            "pdfplumber, or pypdf, then rerun."
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {pdf.stem}\n\n> Converted from `{pdf}`.\n\n"
    out.write_text(header + text.strip() + "\n", encoding="utf-8")
    return out


def expand_inputs(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            files.extend(Path(m) for m in matches)
        else:
            files.append(Path(pattern))
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="+", help="PDF file path or glob")
    parser.add_argument("--out-dir", default="", help="Optional output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    ok = 0
    for pdf in expand_inputs(args.pdf):
        if not pdf.exists() or pdf.suffix.lower() != ".pdf":
            print(f"skip: {pdf}", file=sys.stderr)
            continue
        try:
            out = pdf_to_md(pdf, out_dir)
            print(f"converted: {pdf} -> {out}")
            ok += 1
        except Exception as exc:
            print(f"failed: {pdf}: {exc}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
