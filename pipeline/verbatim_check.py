# -*- coding: utf-8 -*-
"""Дословность: не переписана ли карточка словами источника.

Правило владельца 3 октября 2026: текст карточки — не дословно из
источника; а если дословно, то в кавычках и с указанием, кто сообщает.
Замер 3 октября на 78 карточках 2026 года с доступными источниками: у 65%
есть общая с источником цепочка от 8 слов, у 46% — от 12, у 22% — от 20,
у 12% — от 30 (целые абзацы). Причина системная: `review.py` требует
ДОСЛОВНУЮ цитату источника, пересказ делает `proofread.py` следующим шагом —
и не все карточки до него доходят, а вычитка не сверяет текст с источником.

Что делает скрипт: качает источники карточки, ищет самые длинные общие
цепочки слов между прозой карточки (заголовок, предмет, «Контекст», «Цель
сделки», юридические поля, `extra`) и текстом статьи. Порог — `MIN_WORDS`
слов подряд: список юрлиц с долями или «сумма сделки не раскрывается» в
него не попадают, абзац статьи — попадает.

    python3 pipeline/verbatim_check.py --queue [N]     # свежие карточки с дословными кусками
    python3 pipeline/verbatim_check.py --card <id>     # одна карточка подробно
    python3 pipeline/verbatim_check.py --sample 80     # замер по случайной выборке

Найденное — очередь вычитки (`proofread.py`, правило 2 в
`PROOFREADING_ROUTINE.md`): пересказать или оставить в кавычках с «— сообщает
<издание>». Агрегаторы (t.me, mergers.ru) не качаются: их текст сам пересказ.
"""
import json
import os
import random
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import source_names  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
MIN_WORDS = 12
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
PROSE_FIELDS = ('title', 'asset', 'extra')
LENS_MIN_LEN = 40


def words(text):
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    for a, b in (('&nbsp;', ' '), ('&laquo;', '«'), ('&raquo;', '»'), ('&mdash;', '—'), ('&quot;', '"'), ('&amp;', '&')):
        text = text.replace(a, b)
    text = re.sub(r'&#\d+;', ' ', text)
    return re.findall(r'[0-9a-zа-яё]+', text.lower().replace('ё', 'е'))


def longest_common_run(a, b, minw=MIN_WORDS):
    """Самая длинная общая цепочка слов двух текстов: (длина, текст)."""
    if len(a) < minw or len(b) < minw:
        return 0, ''
    index = {}
    for i in range(len(b) - minw + 1):
        index.setdefault(tuple(b[i:i + minw]), []).append(i)
    best, best_text, i = 0, '', 0
    while i <= len(a) - minw:
        key = tuple(a[i:i + minw])
        if key in index:
            run = 0
            for j in index[key]:
                k = 0
                while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                    k += 1
                run = max(run, k)
            if run > best:
                best, best_text = run, ' '.join(a[i:i + run])
            i += max(1, run - minw + 1)
        else:
            i += 1
    return best, best_text


def card_prose(deal):
    out = {}
    for k in PROSE_FIELDS:
        if deal.get(k):
            out[k] = str(deal[k])
    for lens in ('eco', 'law'):
        for k, v in (deal.get(lens) or {}).items():
            if isinstance(v, str) and len(v) >= LENS_MIN_LEN and v != '—':
                out['%s.%s' % (lens, k)] = v
    return out


def fetch(url):
    import httpx
    try:
        r = httpx.get(url, headers={'User-Agent': UA}, timeout=20, follow_redirects=True)
        return r.status_code, r.text
    except Exception:                                       # noqa: BLE001
        return 0, ''


def check_card(deal, max_sources=3):
    """{'id', 'fetched': n, 'fields': {поле: {'run', 'snippet', 'src'}}} —
    только поля с цепочкой от MIN_WORDS."""
    res = {'id': deal['id'], 'title': deal.get('title', ''), 'fetched': 0, 'fields': {}}
    prose = {k: words(v) for k, v in card_prose(deal).items()}
    srcs = [s for s in (deal.get('src') or []) if isinstance(s, list) and len(s) > 1
            and str(s[1]).startswith('http') and not source_names.is_aggregator(s[1])]
    for name, url in srcs[:max_sources]:
        code, html = fetch(url)
        if code != 200 or len(html) < 2000:
            continue
        res['fetched'] += 1
        article = words(html)
        for field, w in prose.items():
            run, snippet = longest_common_run(w, article)
            if run >= MIN_WORDS and run > res['fields'].get(field, {}).get('run', 0):
                res['fields'][field] = {'run': run, 'snippet': snippet[:240], 'src': name}
    return res


def report(rows):
    for r in rows:
        if not r['fields']:
            continue
        worst = max(r['fields'].items(), key=lambda kv: kv[1]['run'])
        print('%s %s' % (r['id'], r['title'][:60]))
        for field, v in sorted(r['fields'].items(), key=lambda kv: -kv[1]['run']):
            print('   %-14s %3d слов подряд как у «%s»: %s…' % (field, v['run'], v['src'], v['snippet'][:110]))
        _ = worst


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    if '--card' in argv:
        deal = next(d for d in deals if d['id'] == argv[argv.index('--card') + 1])
        r = check_card(deal)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if '--sample' in argv:
        n = int(argv[argv.index('--sample') + 1])
        pool = [d for d in deals if d.get('src')]
        random.seed(7)
        random.shuffle(pool)
        chosen = pool[:n]
    else:
        n = int(argv[argv.index('--queue') + 1]) if '--queue' in argv and len(argv) > argv.index('--queue') + 1 \
            and argv[argv.index('--queue') + 1].isdigit() else 40
        chosen = sorted((d for d in deals if d.get('src')), key=lambda d: str(d.get('added') or d.get('date') or ''),
                        reverse=True)[:n]
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(check_card, chosen))
    fetched = [r for r in rows if r['fetched']]
    hit = [r for r in fetched if r['fields']]
    print('Проверено карточек: %d, источник открылся у %d, дословные куски (от %d слов) у %d.'
          % (len(rows), len(fetched), MIN_WORDS, len(hit)))
    for th in (20, 30):
        print('  от %d слов: %d' % (th, sum(1 for r in hit if max(v['run'] for v in r['fields'].values()) >= th)))
    print()
    report(sorted(hit, key=lambda r: -max(v['run'] for v in r['fields'].values())))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
