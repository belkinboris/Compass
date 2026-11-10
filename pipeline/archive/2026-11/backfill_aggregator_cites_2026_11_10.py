# -*- coding: utf-8 -*-
"""Разово, 10 ноября 2026: ссылки на первоисточник из заметок mergers.ru для
карточек, собранных до того, как fetch_article_texts начал их сохранять
(поле `cites`, см. cited_links). Скачивает заметку агрегатора каждой карточки
базы и предпросмотра, дописывает в data/inbox/raw/<дата>-articles.jsonl запись
{'url', 'title', 'summary', 'cites'} и печатает карточки, у которых
процитированного первоисточника нет в src.

    python3 pipeline/archive/2026-11/backfill_aggregator_cites_2026_11_10.py          # сухой
    python3 pipeline/archive/2026-11/backfill_aggregator_cites_2026_11_10.py --write
"""
import json
import os
import sys
import time
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fetch_article_texts as fat  # noqa: E402
import accept_card  # noqa: E402
from source_names import is_aggregator  # noqa: E402


def main(write):
    base = json.load(open(os.path.join(ROOT, 'static/data/deals_promoted.json'), encoding='utf-8'))
    pend = json.load(open(os.path.join(ROOT, 'static/data/pending.json'), encoding='utf-8'))
    cards = base['deals'] + pend['cards']
    urls = {}
    for c in cards:
        for s in list(c.get('src') or []) + list(c.get('discovery_src') or []):
            if isinstance(s, (list, tuple)) and len(s) > 1 and is_aggregator(s[1]) \
                    and str(s[1]).startswith('http') and 't.me' not in str(s[1]):
                urls.setdefault(str(s[1]), str(c.get('title') or ''))
    recs = []
    for i, (url, title) in enumerate(sorted(urls.items())):
        req = urllib.request.Request(fat.encode_url(url), headers={'User-Agent': 'Mozilla/5.0'})
        try:
            raw = urllib.request.urlopen(req, timeout=25).read()
            if raw[:2] == b'\x1f\x8b':
                import gzip
                raw = gzip.decompress(raw)
            body = raw.decode('utf-8', 'ignore')
        except Exception as e:
            print('НЕ ЗАБРАН', url, e)
            continue
        cites = fat.cited_links(body, url)
        recs.append({'url': url, 'title': title, 'summary': fat.article_text(body), 'cites': cites})
        time.sleep(0.4)
    print('заметок агрегатора: %d, со ссылкой на первоисточник: %d'
          % (len(recs), sum(1 for r in recs if r['cites'])))
    lacking = []
    for c in cards:
        miss = accept_card.aggregator_cited_missing(c, recs)
        if miss:
            lacking.append((c['id'], c.get('title'), miss))
    print('карточек без процитированного первоисточника в src: %d' % len(lacking))
    for cid, t, miss in lacking:
        print('  %s %s\n      -> %s' % (cid, str(t)[:80], ' '.join(miss)))
    if write and recs:
        out = os.path.join(ROOT, 'data', 'inbox', 'raw', '%s-articles.jsonl' % date.today().isoformat())
        with open(out, 'a', encoding='utf-8') as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print('дописано записей: %d -> %s' % (len(recs), os.path.relpath(out, ROOT)))
    return lacking


if __name__ == '__main__':
    main('--write' in sys.argv)
