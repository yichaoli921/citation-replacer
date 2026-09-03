#!/usr/bin/env python3
"""
fetch_metadata.py
联网拉取文献元数据（CNKI / CrossRef / OpenAlex）
支持中文文献优先 CNKI，英文文献优先 OpenAlex，DOI 已知时 CrossRef 兜底

依赖：requests
运行：python fetch_metadata.py <cite_map.tsv> [output.tsv]

cite_map.tsv 格式：author\tyear\ttitle_hint
输出 TSV：author\tyear\tjournal\tvolume\tissue\tpages\tpublisher\tdoc_type\tdoi\ttitle
"""

import sys
import csv
import time
import json
import re
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    print('请安装 requests：pip install requests')
    sys.exit(1)


# ============================================================
# 多源统一接口
# ============================================================
class MetadataSource:
    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | None:
        """返回 {title, journal, volume, issue, pages, doi, ...} 或 None"""
        raise NotImplementedError


class OpenAlexSource(MetadataSource):
    """OpenAlex 免费 API，无需 key"""
    BASE = 'https://api.openalex.org/works'

    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | None:
        # OpenAlex 用 display_name 搜索作者，filter by publication_year
        # 简化：标题搜索 + 年份过滤
        if title_hint:
            url = f'{self.BASE}?search={quote(title_hint)}&filter=publication_year:{year},type:article'
        else:
            url = f'{self.BASE}?search={quote(author)}&filter=publication_year:{year},type:article'
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                return None
            data = r.json()
            results = data.get('results', [])
            if not results:
                return None
            top = results[0]
            return self._parse(top)
        except Exception as e:
            print(f'  OpenAlex 错误：{e}')
            return None

    def _parse(self, item: dict) -> dict:
        loc = item.get('primary_location') or {}
        src = loc.get('source') or {}
        return {
            'title': item.get('title', '').strip(),
            'journal': src.get('display_name', ''),
            'volume': item.get('biblio', {}).get('volume', ''),
            'issue': item.get('biblio', {}).get('issue', ''),
            'pages': item.get('biblio', {}).get('first_page', '') + ('-' + item.get('biblio', {}).get('last_page', '') if item.get('biblio', {}).get('last_page') else ''),
            'doi': (item.get('doi') or '').replace('https://doi.org/', ''),
            'doc_type': 'J',
        }


class CrossRefSource(MetadataSource):
    """CrossRef API，DOI 已知时优先"""
    BASE = 'https://api.crossref.org/works'

    def fetch_by_doi(self, doi: str) -> dict | None:
        if not doi:
            return None
        try:
            r = requests.get(f'{self.BASE}/{quote(doi)}', timeout=15)
            if r.status_code != 200:
                return None
            return self._parse(r.json().get('message', {}))
        except Exception as e:
            print(f'  CrossRef 错误：{e}')
            return None

    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | None:
        query_parts = []
        if title_hint:
            query_parts.append(quote(title_hint))
        else:
            query_parts.append(quote(author))
        url = f'{self.BASE}?query.bibliographic={query_parts[0]}&filter=from-pub-date:{year}-01-01,until-pub-date:{year}-12-31'
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                return None
            items = r.json().get('message', {}).get('items', [])
            if not items:
                return None
            return self._parse(items[0])
        except Exception as e:
            print(f'  CrossRef 错误：{e}')
            return None

    def _parse(self, item: dict) -> dict:
        title = item.get('title', [''])[0] if item.get('title') else ''
        container = item.get('container-title', [''])[0] if item.get('container-title') else ''
        return {
            'title': title,
            'journal': container,
            'volume': item.get('volume', ''),
            'issue': item.get('issue', ''),
            'pages': item.get('page', ''),
            'doi': item.get('DOI', ''),
            'doc_type': 'J',
        }


class CNKISource(MetadataSource):
    """
    CNKI 数据源（占位实现）

    实际使用需要：
    1. 登录态 cookie（requests.Session 维持）
    2. 处理反爬（验证码、IP 限流）
    3. 解析 HTML 结构（cnki.net 的搜索结果页）

    或使用第三方封装：
    - scholarly（部分中文支持）
    - 知网官方 API（需申请）
    - 手动从浏览器复制

    当前实现：检测到 CNKI 调用直接返回 None 并提示用户手动提供
    """
    def fetch(self, author: str, year: int, title_hint: str = '') -> dict | None:
        print(f'  ⚠️  CNKI 暂未实现自动抓取，请手动补全：{author}, {year}, "{title_hint}"')
        return None


# ============================================================
# 主流程
# ============================================================
def main():
    if len(sys.argv) < 2:
        print('用法：python fetch_metadata.py <cite_map.tsv> [output.tsv]')
        print('输入格式：author\\tyear\\ttitle_hint（可选）')
        print('输出格式：author\\tyear\\ttitle\\tjournal\\tvolume\\tissue\\tpages\\tdoi\\tdoc_type')
        sys.exit(1)

    input_tsv = Path(sys.argv[1])
    output_tsv = Path(sys.argv[2]) if len(sys.argv) > 2 else input_tsv.with_name('cite_map_full.tsv')

    sources = [
        OpenAlexSource(),
        CrossRefSource(),
        CNKISource(),
    ]

    with open(input_tsv, 'r', encoding='utf-8') as fin, \
         open(output_tsv, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin, delimiter='\t')
        writer = csv.writer(fout, delimiter='\t')
        writer.writerow(['author', 'year', 'title', 'journal', 'volume',
                         'issue', 'pages', 'doi', 'doc_type', 'source'])

        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            author = row[0].strip()
            year = int(row[1].strip())
            title_hint = row[2].strip() if len(row) > 2 else ''

            print(f'查询：{author}, {year}, "{title_hint}"')
            meta = None
            used_source = ''
            for src in sources:
                meta = src.fetch(author, year, title_hint)
                if meta:
                    used_source = type(src).__name__
                    break
                time.sleep(0.5)  # 礼貌限流

            if meta:
                writer.writerow([
                    author, year, meta.get('title', ''), meta.get('journal', ''),
                    meta.get('volume', ''), meta.get('issue', ''), meta.get('pages', ''),
                    meta.get('doi', ''), meta.get('doc_type', 'J'), used_source
                ])
                print(f'  ✅ 来自 {used_source}')
            else:
                writer.writerow([author, year, '', '', '', '', '', '', '', ''])
                print(f'  ❌ 未找到，需要手动补全')

    print(f'\n输出：{output_tsv}')


if __name__ == '__main__':
    main()
