#!/usr/bin/env python3
"""journal_query_demo.py
演示如何调用 enrich_journal_level.py 的核心函数查询期刊等级。
"""

import sys
from pathlib import Path

# 把 scripts/ 加入 path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from enrich_journal_level import load_journal_levels, match_journal


def main():
    levels = load_journal_levels()
    print(f'已加载 {len(levels)} 条期刊记录\n')

    # 测试条目
    entries = [
        '黄蕙萍，等 . 题名［J］. 管理世界，2020，36(9)：82 - 97.',
        'Taylor P J . Title［J］. Urban Studies，2002，39(13)：2367.',
        '某作者 . 题名［J］. Some Random Journal XYZ，2025，1(1)：1.',
    ]

    for entry in entries:
        result = match_journal(entry, levels)
        if result:
            journal, level = result
            print(f'✓ {journal} → {level}')
        else:
            print(f'✗ 未匹配: {entry[:60]}...')


if __name__ == '__main__':
    main()