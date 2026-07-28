# -*- coding: utf-8 -*-
"""Реестр источников: откуда «Компас» будет узнавать о новых сделках.

ЗАЧЕМ. Платформа не запустится, пока база пополняется вручную. Первый шаг —
список источников, за которыми следим. Его не надо выдумывать: в базе уже есть
1333 карточки с ссылками на первоисточники, и по ним видно, кто в реальности
пишет о сделках российского рынка.

КАК СОБРАН. Скрипт читает `static/data/deals_promoted.json` и считает, сколько
карточек пришло с каждого домена. Домены с 3+ карточками попадают в реестр
автоматически, вместе с наблюдаемым названием («Коммерсантъ», «Интерфакс»).
К ним добавляются:
  * Telegram-каналы, уже встречавшиеся в источниках (t.me/dealsma и другие);
  * сайты консультантов из справочника FIRMS в `static/index.html` — они
    публикуют собственные пресс-релизы о сделках, и в прогонах 8–14 именно
    оттуда пришла атрибуция по 64 фирмам;
  * адреса RSS-лент для тех изданий, где они известны (таблица FEEDS).

ЧЕГО ЗДЕСЬ НЕТ И ПОЧЕМУ. Адреса лент НЕ проверены сетью: в этой среде исходящий
доступ к новостным сайтам закрыт политикой прокси (403 на CONNECT). Поэтому у
каждой ленты стоит `feed_checked: false`, а проверять их будет `fetch.py
--verify` там, где сеть есть, — и он же перепишет это поле. Выдумывать
работоспособность мы не можем: непроверенное помечено непроверенным.

Запуск:
    python3 pipeline/ingest/build_sources.py            # сухой прогон
    python3 pipeline/ingest/build_sources.py --write    # записать sources.json
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources.json')

MIN_DEALS = 3          # домен попадает в реестр, если с него пришло столько карточек

# Известные адреса лент. Не проверены сетью — см. docstring.
FEEDS = {
    'kommersant.ru': 'https://www.kommersant.ru/RSS/news.xml',
    'vedomosti.ru': 'https://www.vedomosti.ru/rss/news',
    'rbc.ru': 'https://rssexport.rbc.ru/rbcnews/news/30/full.rss',
    'quote.rbc.ru': 'https://quote.rbc.ru/rss',
    'interfax.ru': 'https://www.interfax.ru/rss.asp',
    'tass.ru': 'https://tass.ru/rss/v2.xml',
    'ria.ru': 'https://ria.ru/export/rss2/archive/index.xml',
    'realty.ria.ru': 'https://realty.ria.ru/export/rss2/archive/index.xml',
    '1prime.ru': 'https://1prime.ru/export/rss2/archive/index.xml',
    'forbes.ru': 'https://www.forbes.ru/newrss.xml',
    'iz.ru': 'https://iz.ru/xml/rss/all.xml',
    'cnews.ru': 'https://www.cnews.ru/inc/rss/news.xml',
    'vc.ru': 'https://vc.ru/rss/all',
    'tadviser.ru': 'https://www.tadviser.ru/xml/tadviser.xml',
    'comnews.ru': 'https://www.comnews.ru/rss.xml',
    'dp.ru': 'https://www.dp.ru/exportnews.xml',
    'fontanka.ru': 'https://www.fontanka.ru/fontanka.rss',
    'incrussia.ru': 'https://incrussia.ru/feed/',
    'rb.ru': 'https://rb.ru/feeds/all/',
    'retail.ru': 'https://www.retail.ru/rss/news/',
    'new-retail.ru': 'https://new-retail.ru/rss/',
    'sostav.ru': 'https://www.sostav.ru/rss/news.xml',
    'vademec.ru': 'https://vademec.ru/rss/',
    'agroinvestor.ru': 'https://www.agroinvestor.ru/rss/',
    'neftegaz.ru': 'https://neftegaz.ru/rss/',
    'frankmedia.ru': 'https://frankmedia.ru/feed',
    'expert.ru': 'https://expert.ru/rss/',
    'abireg.ru': 'https://abireg.ru/rss.xml',
    'business-gazeta.ru': 'https://www.business-gazeta.ru/rss',
    'gazeta.ru': 'https://www.gazeta.ru/export/rss/lenta.xml',
    'secretmag.ru': 'https://secretmag.ru/rss/',
    'pravo.ru': 'https://pravo.ru/rss/',
    'akm.ru': 'https://www.akm.ru/rss/news/',
    'mergers.ru': None,        # ленты нет, нужен разбор страницы
}

# Профильные источники именно о сделках. Отдельный ярус: у них выше и точность,
# и приоритет разбора — почти каждая запись про M&A.
TIER1 = {'mergers.ru', 'akm.ru', 't.me/dealsma'}

# Telegram-каналы. Читаются через веб-зеркало t.me/s/<канал> — токен бота для
# ЧТЕНИЯ чужих каналов не нужен и не даёт доступа: бот видит только те чаты,
# куда он добавлен.
TELEGRAM_EXTRA = [
    ('dealsma', 'Сделки M&A (@dealsma)', 1),
    ('rusven', 'Русский венчур', 2),
    ('alumnimna', 'ALUMNI Partners M&A', 3),
    ('BIRCHLEGAL', 'BIRCH Legal', 3),
    ('LevelLegalServices', 'LEVEL Legal Services', 3),
    ('LKPconsult', 'ЛКП', 3),
    ('kkmpconnect', 'ККМП', 3),
    ('bezrec', 'Без рецепта', 2),
]


def norm_host(url):
    m = re.match(r'https?://([^/]+)', url or '')
    return re.sub(r'^www\.', '', m.group(1)).lower() if m else ''


def firm_sites():
    """Сайты консультантов из справочника FIRMS в index.html."""
    html = open(INDEX, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'\{id:"([a-z0-9_-]+)",n:"([^"]+)"[^}]*?site:"([^"]+)"', html):
        out.append((m.group(1), m.group(2), m.group(3)))
    return out


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    hits, label, tg = Counter(), {}, Counter()
    for deal in data['deals']:
        for src in (deal.get('src') or []):
            url = str(src[1]) if len(src) > 1 else ''
            if not url.startswith('http'):
                continue
            host = norm_host(url)
            if not host:
                continue
            m = re.match(r'https?://t\.me/(?:s/)?([A-Za-z0-9_]+)', url)
            if m:
                tg[m.group(1)] += 1
                continue
            hits[host] += 1
            label.setdefault(host, re.sub(r'\s*\(.*$', '', str(src[0]))[:40].strip())

    sources = []
    for host, count in hits.most_common():
        if count < MIN_DEALS:
            continue
        sources.append({
            'id': 'web:' + host,
            'name': label.get(host) or host,
            'kind': 'rss' if FEEDS.get(host) else 'html',
            'url': 'https://' + host + '/',
            'feed': FEEDS.get(host),
            'feed_checked': False,
            'tier': 1 if host in TIER1 else 2,
            'deals_seen': count,
            'enabled': bool(FEEDS.get(host)),
        })

    seen_tg = set()
    for name, title, tier in TELEGRAM_EXTRA:
        seen_tg.add(name.lower())
        sources.append({
            'id': 'tg:' + name,
            'name': title,
            'kind': 'telegram',
            'url': 'https://t.me/' + name,
            'feed': 'https://t.me/s/' + name,
            'feed_checked': False,
            'tier': tier,
            'deals_seen': tg.get(name, 0),
            'enabled': True,
        })
    for name, count in tg.most_common():
        if name.lower() in seen_tg:
            continue
        sources.append({
            'id': 'tg:' + name, 'name': 'Telegram @' + name, 'kind': 'telegram',
            'url': 'https://t.me/' + name, 'feed': 'https://t.me/s/' + name,
            'feed_checked': False, 'tier': 3, 'deals_seen': count, 'enabled': True,
        })

    for fid, fname, site in firm_sites():
        sources.append({
            'id': 'firm:' + fid, 'name': fname, 'kind': 'html',
            'url': site, 'feed': None, 'feed_checked': False,
            'tier': 3, 'deals_seen': 0, 'enabled': False,
        })

    by_kind = Counter(s['kind'] for s in sources)
    by_tier = Counter(s['tier'] for s in sources)
    print('Источников в реестре: %d' % len(sources))
    print('  по типу:', dict(by_kind))
    print('  по ярусу:', dict(by_tier))
    print('  с известной лентой: %d' % sum(1 for s in sources if s['feed']))
    print('  включено сейчас: %d' % sum(1 for s in sources if s['enabled']))
    print('  доменов отброшено (меньше %d карточек): %d'
          % (MIN_DEALS, sum(1 for h, c in hits.items() if c < MIN_DEALS)))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'sources': sources}, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %s' % os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main('--write' in sys.argv)
