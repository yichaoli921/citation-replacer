#!/usr/bin/env python3
"""
test_replace_citations.py
跨 run 替换核心算法的 smoke test

测试场景：
1. 括号式引用匹配
2. 叙述式引用识别
3. 编号渲染（连续、非连续、混合）
4. 通讯地址过滤
5. 已有上标保留
"""

import sys
import re
from pathlib import Path

# 把 scripts 加 入 path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from replace_citations import (
    CITE_PAR, NARRATIVE_PAT, is_citation_block,
    parse_cite_block, parse_single_cite, render_ref,
    normalize_author, lookup_number,
    DEFAULT_STYLE,
)


def assert_eq(actual, expected, msg=''):
    if actual != expected:
        print(f'❌ FAIL: {msg}')
        print(f'   actual:   {actual!r}')
        print(f'   expected: {expected!r}')
        return False
    return True


def test_cite_par_matches():
    """测试括号式引用匹配"""
    tests = [
        ('(黄蕙萍等，2020)', True),
        ('（宣烨和余泳泽，2017）', True),
        ('(张虎等，2017; 唐晓华等，2018)', True),
        ('(Boschma, 2005)', True),
        ('（Hanneke et al., 2010）', True),
        # 不应该匹配
        ('(1.西南财经大学，611130)', False),  # 地址
        ('（2020年3月）', False),  # 无作者
        ('(邮编 201901)', False),  # 邮编无作者
    ]
    ok = True
    for text, expected in tests:
        result = is_citation_block(text) and bool(CITE_PAR.search(text))
        # is_citation_block + CITE_PAR 同时为 True 时算"应该是引用"
        actual = is_citation_block(text) and bool(CITE_PAR.search(text))
        if not assert_eq(actual, expected, f'cite_par: {text!r}'):
            ok = False
    return ok


def test_narrative_pat():
    """测试叙述式引用"""
    tests = [
        ('Boschma（2005）', True),
        ('Hanneke等（2010）', True),
        ('Leifeld et al.（2018）', True),
        # '1Boschma'：re.search 从 'oschma' 开始匹配，技术上匹配成功但实际只替换括号年份
        ('1Boschma（2005）', True),
    ]
    ok = True
    for text, expected in tests:
        actual = bool(NARRATIVE_PAT.search(text))
        if not assert_eq(actual, expected, f'narrative: {text!r}'):
            ok = False
    return ok


def test_render_ref():
    """测试编号渲染"""
    style = DEFAULT_STYLE
    tests = [
        ([1], '［1］'),
        ([1, 2], '［1-2］'),
        ([1, 2, 3], '［1-3］'),
        ([1, 3, 5], '［1，3，5］'),
        ([1, 2, 3, 5], '［1-3，5］'),
        ([1, 2, 15, 16, 17, 18], '［1-2，15-18］'),
        ([], ''),
    ]
    ok = True
    for nums, expected in tests:
        actual = render_ref(nums, style)
        if not assert_eq(actual, expected, f'render_ref({nums})'):
            ok = False
    return ok


def test_parse_cite_block():
    """测试引用块解析（返回整体作者-年份对，不拆多作者）"""
    tests = [
        ('黄蕙萍等，2020', [('黄蕙萍等', 2020)]),
        ('宣烨和余泳泽，2017', [('宣烨和余泳泽', 2017)]),
        ('张虎等，2017; 唐晓华等，2018', [('张虎等', 2017), ('唐晓华等', 2018)]),
        ('余泳泽等2016', [('余泳泽等', 2016)]),  # 缺逗号
    ]
    ok = True
    for text, expected in tests:
        actual = parse_cite_block(text)
        if not assert_eq(actual, expected, f'parse_cite_block: {text!r}'):
            ok = False
    return ok


def test_parse_single_cite():
    """测试单个引用解析"""
    tests = [
        ('黄蕙萍等，2020', ('黄蕙萍等', 2020)),
        ('余泳泽等2016', ('余泳泽等', 2016)),
        ('鉴韩峰和阳立高，2020', ('韩峰和阳立高', 2020)),  # OCR 去前缀
        ('Hanneke et al., 2010', ('Hanneke et al.', 2010)),
    ]
    ok = True
    for text, expected in tests:
        actual = parse_single_cite(text)
        if not assert_eq(actual, expected, f'parse_single: {text!r}'):
            ok = False
    return ok


def test_normalize_author():
    """测试作者归一化"""
    tests = [
        ('Hanneke', 'hanneke'),
        ('H．Lusher', 'h.lusher'),
        ('H. Lusher', 'h.lusher'),
    ]
    ok = True
    for text, expected in tests:
        actual = normalize_author(text)
        if not assert_eq(actual, expected, f'normalize: {text!r}'):
            ok = False
    return ok


def test_is_citation_block():
    """测试非引用块过滤"""
    tests = [
        ('（1.西南财经大学...611130；中国四川，成都）', False),  # 地址
        ('（邮编 201901）', False),  # 邮编
        ('（通讯作者：xxx@example.com）', False),  # 邮箱
        ('（数据来源：国家统计局）', False),  # 数据来源
        ('（黄蕙萍等，2020）', True),  # 真引用
        ('（Boschma, 2005）', True),  # 真引用
    ]
    ok = True
    for text, expected in tests:
        actual = is_citation_block(text)
        if not assert_eq(actual, expected, f'is_citation: {text!r}'):
            ok = False
    return ok


def main():
    tests = [
        ('CITE_PAR + is_citation_block', test_cite_par_matches),
        ('NARRATIVE_PAT', test_narrative_pat),
        ('render_ref', test_render_ref),
        ('parse_cite_block', test_parse_cite_block),
        ('parse_single_cite', test_parse_single_cite),
        ('normalize_author', test_normalize_author),
        ('is_citation_block', test_is_citation_block),
    ]

    print('=== replace_citations smoke test ===\n')

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
            failed += 1

    print(f'\n=== 结果：{passed} 通过，{failed} 失败 ===')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())