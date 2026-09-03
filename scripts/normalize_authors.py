#!/usr/bin/env python3
"""
normalize_authors.py
作者名归一化与 OCR 容错

用法：
1. 交互式：
   python normalize_authors.py
2. 批量处理 TSV：
   python normalize_authors.py <input.tsv> <output.tsv>

输入 TSV：author\tyear
输出 TSV：author_normalized\tyear\tmatched_author\tsuggested_year
"""

import sys
import re
import csv
from pathlib import Path


# ============================================================
# OCR 误字修正词典
# ============================================================
# OCR 常见误字前缀
OCR_PREFIX_NOISE = re.compile(r'^([鉴认议谨让论误错谬驾]{1,3})\b')

# 常见字符替换（视觉相似）
CHAR_SUBSTITUTIONS = {
    '峰': '峰', '锋': '峰',  # 锋 → 峰
    '珊': '珊', '善': '珊',  # 善 → 珊
    '强': '强', '墻': '强',  # 墻 → 强
    '虎': '虎', '虏': '虎',  # 虏 → 虎
    '陆': '陆', '陛': '陆',
    '土': '土', '士': '士',
}

# OCR 后可能出现的繁体/异体字
TRAD_TO_SIMP = {
    '國': '国', '經': '经', '濟': '济', '學': '学', '術': '术',
    '業': '业', '發': '发', '達': '达', '構': '构', '觀': '观',
    '點': '点', '綠': '绿', '線': '线', '際': '际', '關': '关',
}


def normalize(name: str) -> str:
    """
    作者名归一化：
    1. 去空白
    2. OCR 误字前缀
    3. 字符替换
    4. 转简体
    5. 转小写
    """
    if not name:
        return ''
    # 去空白
    name = re.sub(r'\s+', '', name)
    # 全角转半角（中文括号、点等）
    name = name.replace('．', '.').replace('，', ',').replace('（', '(').replace('）', ')')
    name = name.replace('·', '').replace('•', '')
    # 字符替换
    for old, new in CHAR_SUBSTITUTIONS.items():
        name = name.replace(old, new)
    # 繁体转简体（简化版，只处理高频）
    for trad, simp in TRAD_TO_SIMP.items():
        name = name.replace(trad, simp)
    # 去 OCR 误字前缀
    name = OCR_PREFIX_NOISE.sub('', name)
    return name.lower().strip()


def match_author(author: str, candidates: list[str], threshold: float = 0.85) -> str | None:
    """
    在 candidates 中找最相似的作者名
    返回最相似的或 None（如果相似度都 < threshold）
    """
    norm = normalize(author)
    if not norm:
        return None
    best_match = None
    best_score = 0.0
    for cand in candidates:
        cand_norm = normalize(cand)
        if not cand_norm:
            continue
        score = similarity(norm, cand_norm)
        if score > best_score:
            best_score = score
            best_match = cand
    if best_score >= threshold:
        return best_match
    return None


def similarity(s1: str, s2: str) -> float:
    """
    字符串相似度（最长公共子序列 / max(len1, len2)）
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    # LCS 长度
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs = dp[m][n]
    return lcs / max(m, n)


# ============================================================
# 主入口
# ============================================================
def interactive_mode():
    """交互式：输入一个作者名，输出归一化结果"""
    print('作者名归一化（OCR 容错）')
    print('输入作者名（直接回车退出）：')
    while True:
        try:
            line = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            break
        normalized = normalize(line)
        print(f'  原: {line!r}')
        print(f'  归一化: {normalized!r}')
        # 显示 OCR 误字前缀检测
        m = OCR_PREFIX_NOISE.match(line)
        if m:
            print(f'  检测到 OCR 误字前缀：{m.group(1)!r}')
        print()


def batch_mode(input_tsv: str, output_tsv: str):
    """批量处理 TSV"""
    with open(input_tsv, 'r', encoding='utf-8') as fin, \
         open(output_tsv, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin, delimiter='\t')
        writer = csv.writer(fout, delimiter='\t')
        writer.writerow(['author_orig', 'year', 'author_normalized'])
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            author = row[0].strip()
            year = row[1].strip()
            norm = normalize(author)
            writer.writerow([author, year, norm])
    print(f'✅ 处理完成，输出：{output_tsv}')


def main():
    if len(sys.argv) == 1:
        interactive_mode()
    elif len(sys.argv) == 3:
        batch_mode(sys.argv[1], sys.argv[2])
    else:
        print('用法：')
        print('  交互式：python normalize_authors.py')
        print('  批量：  python normalize_authors.py <input.tsv> <output.tsv>')


if __name__ == '__main__':
    main()
