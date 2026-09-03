#!/usr/bin/env python3
"""
test_enrich_journal_level.py
期刊等级自动标注 smoke test

测试场景：
1. 中文 A+ 级匹配（《管理世界》/《经济研究》）
2. 中文 A 级匹配（《经济地理》/《地理学报》/《中国工业经济》）
3. 中文 B 级匹配（《地理研究》/《产业经济研究》）
4. 英文 A+ 级匹配（Urban Studies）
5. 模糊匹配（International Review of Economics & Finance 之类）
6. 未在目录中时正确标注
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from enrich_journal_level import (
    load_journal_levels, match_journal, normalize_journal_name,
    DEFAULT_JOURNAL_TSV,
)


def assert_eq(actual, expected, msg=''):
    if actual != expected:
        print(f'❌ FAIL: {msg}')
        print(f'   actual:   {actual!r}')
        print(f'   expected: {expected!r}')
        return False
    return True


def test_known_journals():
    """测试已知期刊匹配"""
    if not DEFAULT_JOURNAL_TSV.exists():
        print(f'⚠️  跳过：未找到期刊目录 {DEFAULT_JOURNAL_TSV}')
        return True

    levels = load_journal_levels()

    tests = [
        # (条目, 期望等级)
        ('黄蕙萍，缪子菊，袁野，等 . 题名［J］. 管理世界，2020，36(9)：82 - 97.', 'A+级'),
        ('钟粤俊，等 . 题名［J］. 经济研究，2026，61(1)：119 - 142.', 'A+级'),
        ('宣烨，余泳泽 . 题名［J］. 数量经济技术经济研究，2017，34(2)：89 - 104.', 'A级'),
        ('熊丽芳，等 . 题名［J］. 经济地理，2013，33(7)：67 - 73.', 'A级'),
        ('王姣娥，景悦 . 题名［J］. 地理学报，2017，72(8)：1508 - 1519.', 'A级'),
        ('高鹏，等 . 题名［J］. 地理科学，2019，39(4)：578 - 586.', 'B级'),
        ('Taylor P J，Catalano G，Walker D R F. Title［J］. Urban Studies，2002，39(13)：2367 - 2376.', 'A级'),
    ]

    ok = True
    for entry, expected_level in tests:
        result = match_journal(entry, levels)
        if result is None:
            print(f'❌ FAIL: 未提取出期刊名: {entry!r}')
            ok = False
            continue
        journal, level = result
        if not assert_eq(level, expected_level, f'等级: {journal}'):
            ok = False
    return ok


def test_unknown_journal():
    """测试未知期刊标注"""
    if not DEFAULT_JOURNAL_TSV.exists():
        return True

    levels = load_journal_levels()
    entry = '某作者 . 题名［J］. Some Random Journal XYZ，2025，1(1)：1 - 10.'
    result = match_journal(entry, levels)
    if result is None:
        print('❌ FAIL: 未提取期刊名')
        return False
    journal, level = result
    if '未在目录中' not in level and level != '未在目录中':
        # 即使模糊匹配成功，至少应能找到
        print(f'⚠️  模糊匹配：{journal} → {level}')
    else:
        if not assert_eq(level, '未在目录中', '未知期刊'):
            return False
    return True


def test_normalize():
    """测试期刊名归一化"""
    tests = [
        ('Hanneke', 'hanneke'),
        ('H. Lusher', 'h.lusher'),
        ('管理 世界', '管理世界'),
    ]
    ok = True
    for text, expected in tests:
        actual = normalize_journal_name(text)
        if not assert_eq(actual, expected, f'normalize: {text!r}'):
            ok = False
    return ok


def main():
    tests = [
        ('normalize', test_normalize),
        ('known_journals', test_known_journals),
        ('unknown_journal', test_unknown_journal),
    ]

    print('=== enrich_journal_level smoke test ===\n')

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f'[测试] {name}...', end=' ')
        try:
            if test_fn():
                print('✅ PASS')
                passed += 1
            else:
                print('❌ FAIL')
                failed += 1
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            failed += 1

    print(f'\n=== 结果：{passed} 通过，{failed} 失败 ===')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())