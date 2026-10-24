"""Наблюдение за конкурентами: что изменилось на их сайтах с прошлой проверки.

Владелец 24 октября 2026: «пусть он постоянно этих мониторит, раз в неделю,
… говорит нам, где они нас обгоняют». Порядок работы — `routines/competitors.md`,
разбор и журнал наблюдений — `finance/КОНКУРЕНТЫ.md`.

Скрипт ничего не решает: забирает страницы, сводит их к видимому тексту и
сравнивает с прошлым снимком в `data/inbox/competitors/snapshots/`. Что
появилось, что пропало, что изменилось — печатает; читает и судит человек
(или агент рутины). Снимки лежат в git: так через месяц видно, когда
именно у конкурента появился раздел, а не только что он есть.

    python3 pipeline/competitors_watch.py            # сравнить, ничего не записывая
    python3 pipeline/competitors_watch.py --write    # сравнить и сохранить новый снимок
"""
import difflib
import hashlib
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, 'data', 'inbox', 'competitors', 'snapshots')
UA = 'Mozilla/5.0 (compatible; KompasCompetitorsWatch/1.0)'

# Кого смотрим. Новый конкурент — строка сюда и абзац в finance/КОНКУРЕНТЫ.md.
TARGETS = [
    {'id': 'dealmap', 'name': 'DealMap (Softline VP и «Иннопрактика»)',
     'pages': ['https://dealmap.ru/', 'https://dealmap.ru/llms.txt'],
     'sitemap': 'https://dealmap.ru/sitemap.xml'},
    {'id': 'aspring', 'name': 'Aspring M&A Navigator',
     'pages': ['https://aspring.capital/deals-database']},
    {'id': 'burakova', 'name': 'Навигатор Анны Бураковой (@burakovainvest)',
     'pages': ['https://t.me/s/burakovainvest',
               'https://burakovainvest-navigator.website.yandexcloud.net/']},
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', errors='replace')


def visible_text(raw):
    raw = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', raw)
    raw = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d|section|article)>', '\n', raw)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', raw))
    lines = [' '.join(l.split()) for l in text.splitlines()]
    return '\n'.join(l for l in lines if l)


def slug(url):
    s = re.sub(r'^https?://', '', url).strip('/')
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s) or 'root'


def sitemap_urls(raw):
    return sorted(set(re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', raw)))


def compare(old, new, limit=60):
    diff = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm='', n=0)
            if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    return diff[:limit], len(diff)


def run(write):
    report = {}
    for t in TARGETS:
        folder = os.path.join(SNAP, t['id'])
        rows = []
        for url in t['pages']:
            path = os.path.join(folder, slug(url) + '.txt')
            try:
                text = visible_text(fetch(url))
            except Exception as e:                               # noqa: BLE001
                rows.append({'url': url, 'error': str(e)[:200]}); continue
            old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
            row = {'url': url, 'chars': len(text), 'sha': hashlib.sha1(text.encode()).hexdigest()[:10]}
            if old is None:
                row['new_snapshot'] = True
            elif old != text:
                row['diff'], row['diff_lines'] = compare(old, text)
            rows.append(row)
            if write:
                os.makedirs(folder, exist_ok=True)
                open(path, 'w', encoding='utf-8').write(text)
        if t.get('sitemap'):
            path = os.path.join(folder, 'sitemap_urls.json')
            try:
                urls = sitemap_urls(fetch(t['sitemap']))
                old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None
                row = {'url': t['sitemap'], 'urls': len(urls)}
                if old is not None:
                    row['added'] = sorted(set(urls) - set(old))[:80]
                    row['removed'] = sorted(set(old) - set(urls))[:80]
                rows.append(row)
                if write:
                    os.makedirs(folder, exist_ok=True)
                    json.dump(urls, open(path, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
            except Exception as e:                               # noqa: BLE001
                rows.append({'url': t['sitemap'], 'error': str(e)[:200]})
        report[t['id']] = {'name': t['name'], 'rows': rows}
    return report


def main(argv):
    report = run('--write' in argv)
    for tid, item in report.items():
        print('=== %s' % item['name'])
        for r in item['rows']:
            if r.get('error'):
                print('  НЕ ОТВЕТИЛ %s — %s' % (r['url'], r['error']))
            elif 'urls' in r:
                print('  карта сайта: %d адресов; новых %d, пропало %d'
                      % (r['urls'], len(r.get('added') or []), len(r.get('removed') or [])))
                for u in (r.get('added') or [])[:40]:
                    print('    + ' + u)
                for u in (r.get('removed') or [])[:40]:
                    print('    - ' + u)
            elif r.get('new_snapshot'):
                print('  первый снимок: %s (%d знаков)' % (r['url'], r['chars']))
            elif r.get('diff'):
                print('  ИЗМЕНИЛОСЬ %s — строк изменено %d:' % (r['url'], r['diff_lines']))
                for l in r['diff']:
                    print('    ' + l[:200])
            else:
                print('  без изменений: %s' % r['url'])
    if '--json' in argv:
        print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
