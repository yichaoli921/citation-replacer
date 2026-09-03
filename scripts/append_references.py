#!/usr/bin/env python3
"""
append_references.py
在 docx 末尾"参考文献："后追加编号化的参考文献条目

依赖：python-docx
运行：python append_references.py <input.docx> <refs.tsv> [style] [output.docx]

refs.tsv 格式：number\tentry_text
例：
1\t黄蕙萍，缪子菊，袁野，等 . 题名［J］. 期刊，2020，36(9)：82 - 97.
"""

import sys
import re
import csv
import glob
from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def load_refs(tsv_path: str) -> list[str]:
    """
    读取 refs.tsv，每行一条
    返回编号化后的列表：['［1］ xxx', '［2］ xxx', ...]
    """
    refs = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            num = int(row[0].strip())
            entry = row[1].strip()
            refs.append((num, entry))
    refs.sort(key=lambda x: x[0])
    return refs


def format_refs(refs: list[tuple[int, str]], style_name: str = 'jingji-dili') -> list[str]:
    """根据风格给条目添加编号前缀"""
    if style_name == 'gb-t-7714':
        return [f'[{num}] {entry}' for num, entry in refs]
    # 《经济地理》、《地理学报》用全角
    return [f'［{num}］ {entry}' for num, entry in refs]


def find_references_title_paragraph(doc):
    """找到 '参考文献：' 段落"""
    for p in doc.paragraphs:
        if p.text.strip().rstrip(':：') == '参考文献':
            return p
    return None


def find_last_content_paragraph(doc, stop_text: str = '参考文献'):
    """找到参考文献前的最后一个非空段落（用作样式参考）"""
    candidates = []
    for p in doc.paragraphs:
        if p.text.strip().rstrip(':：') == stop_text:
            break
        if p.text.strip():
            candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: len(p.text))


def append_references(doc: Document, refs: list[str]) -> int:
    """
    在"参考文献："段落后追加参考文献条目
    段落格式继承最后一个正文段
    返回追加条目数
    """
    title_para = find_references_title_paragraph(doc)
    if title_para is None:
        print('⚠️  未找到"参考文献："段落，请确认已插入该段落')
        return 0

    style_ref = find_last_content_paragraph(doc)

    insert_after = title_para._element
    for ref in refs:
        # 创建新段落元素
        p = OxmlElement('w:p')
        insert_after.addnext(p)
        insert_after = p

        # 复制段落格式（缩进、行距等）
        if style_ref is not None:
            pPr_src = style_ref._element.find(qn('w:pPr'))
            if pPr_src is not None:
                p.insert(0, deepcopy(pPr_src))

        # 创建 run
        r = OxmlElement('w:r')
        p.append(r)
        t = OxmlElement('w:t')
        t.text = ref
        t.set(qn('xml:space'), 'preserve')
        r.append(t)
    return len(refs)


def main():
    if len(sys.argv) < 3:
        print('用法：python append_references.py <input.docx> <refs.tsv> [style] [output.docx]')
        sys.exit(1)

    input_docx = sys.argv[1]
    refs_tsv = sys.argv[2]
    style_name = sys.argv[3] if len(sys.argv) > 3 else 'jingji-dili'
    output_docx = sys.argv[4] if len(sys.argv) > 4 else input_docx.replace('.docx', '_final.docx')

    if '*' in input_docx:
        matches = glob.glob(input_docx)
        if matches:
            input_docx = matches[0]

    refs = load_refs(refs_tsv)
    formatted = format_refs(refs, style_name)
    print(f'→ 加载 {len(refs)} 条参考文献，风格 {style_name}')

    doc = Document(input_docx)
    count = append_references(doc, formatted)
    print(f'✅ 追加 {count} 条参考文献')

    doc.save(output_docx)
    print(f'→ 输出：{output_docx}')


if __name__ == '__main__':
    main()
