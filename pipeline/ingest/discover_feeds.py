# -*- coding: utf-8 -*-
"""Приток: найти RSS-ленту у источников, где сеть есть, а лента не известна.

ЗАЧЕМ. В `sources.json` 30 сайтов юридических и инвестиционных консультантов
(`firm:*`) и десятки новостных сайтов (`web:*`) стоят с `feed: null,
enabled: false` — их пресс-релизы и новости никто не читает, потому что для
каждого нужен свой разбор HTML-страницы. Писать 30+ отдельных парсеров — не
самый дешёвый способ и большая площадь для поломок при любой вёрстке сайта.

КАК ЭТО ДЕШЕВЛЕ. Почти любой сайт на типовой CMS уже отдаёт адрес своей RSS-
ленты в `<head>` главной страницы тегом
`<link rel="alternate" type="application/rss+xml" href="...">` (или atom+xml).
Одна и та же процедура автообнаружения работает для любого сайта без
знания его вёрстки — и лента, если найдётся, читается уже существующим
`fetch.parse_rss`, без единой новой строчки разбора под конкретную фирму.

ЧТО СКРИПТ ДЕЛАЕТ. Для каждого `html`-источника без `feed`: скачивает `url`,
ищет `<link rel="alternate" type=".../(rss|atom)+xml" href="...">`, и если
адрес нашёлся — проверяет его тем же `fetch.parse_rss`, что и обычный забор
(лента должна реально распарситься и отдать хотя бы одну запись). Только
тогда источник переводится в `kind: "rss"`, `enabled: true`,
`feed_checked: true`. Ничего не найдено или лента не парсится — источник
остаётся как был: непроверенное не становится работающим только потому, что
мы хотели бы, чтобы оно работало (см. правило в CLAUDE.md).

Сеть — не константа среды, а факт сессии (см. тот же файл): скрипт не
предполагает, что доступ есть или закрыт, а честно проверяет и пишет ошибку
в `last_error`, если сайт не ответил.

Запуск:
    python3 pipeline/ingest/discover_feeds.py            # сухой прогон, только отчёт
    python3 pipeline/ingest/discover_feeds.py --write    # записать sources.json
"""
import json
import os
import re
import sys
import urllib.error
from datetime import datetime, timezone
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch  # noqa: E402
from fetch import SOURCES, http_get, parse_rss, load_sources  # noqa: E402

# 119 сайтов без известной ленты — при обычных 20с на попытку необнаружения
# это почти 40 минут. Обнаружение ленты на живой странице, если сайт вообще
# отвечает, укладывается в секунды; короче общий таймаут — короче ожидание
# мёртвых адресов, а не потеря живых (см. измерение ниже, 8с хватает).
fetch.TIMEOUT = 8

# `rel` и `type` встречаются в любом порядке (генераторы сайтов пишут их
# по-разному) — искать по каждому атрибуту отдельно внутри тега, а не по
# фиксированной последовательности «rel затем type», иначе половина реальных
# тегов с type раньше rel молча не находится (проверено на себе: assert на
# обоих порядках в test_ingest.py).
LINK_RE = re.compile(r'<link\b[^>]*>', re.I)
REL_ALT_RE = re.compile(r'\brel=["\']alternate["\']', re.I)
TYPE_FEED_RE = re.compile(r'\btype=["\']application/(?:rss|atom)\+xml["\']', re.I)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def discover(url):
    """Адрес ленты по автообнаружению в <head>, или None."""
    try:
        body = http_get(url)
    except urllib.error.HTTPError as e:
        return None, 'HTTP %s' % e.code
    except Exception as e:                                        # noqa: BLE001
        return None, '%s: %s' % (type(e).__name__, str(e)[:80])
    text = body.decode('utf-8', 'ignore') if isinstance(body, bytes) else body
    for tag in LINK_RE.findall(text):
        if not (REL_ALT_RE.search(tag) and TYPE_FEED_RE.search(tag)):
            continue
        href = HREF_RE.search(tag)
        if href:
            return urljoin(url, href.group(1)), None
    return None, 'ленты в <head> нет'


def main(argv):
    write = '--write' in argv
    sources = load_sources()
    candidates = [s for s in sources if s.get('kind') == 'html' and not s.get('feed') and s.get('url')]
    found, dead = [], []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for src in candidates:
        feed_url, err = discover(src['url'])
        if not feed_url:
            dead.append((src['id'], err))
            continue
        items, parse_err = ([], 'сеть недоступна')
        try:
            items = parse_rss(http_get(feed_url), src['id'])
        except Exception as e:                                    # noqa: BLE001
            parse_err = '%s: %s' % (type(e).__name__, str(e)[:80])
        else:
            parse_err = None if items else 'лента пуста'
        if parse_err:
            dead.append((src['id'], 'нашёлся адрес %s, но %s' % (feed_url, parse_err)))
            continue
        found.append((src, feed_url, len(items)))

    print('Источников без ленты проверено: %d' % len(candidates))
    print('Найдена и подтверждена лента: %d' % len(found))
    for src, feed_url, n in found:
        print('  %-28s -> %s (%d записей)' % (src['id'], feed_url, n))
    print('Без ленты осталось: %d' % len(dead))
    for sid, err in dead[:20]:
        print('  %-28s %s' % (sid, err))

    if not write:
        print('\nСухой прогон — sources.json не изменён. Повторите с --write.')
        return

    for src, feed_url, _ in found:
        assert src.get('feed') is None, '%s уже имел ленту — перезаписывать не должны были' % src['id']
        src['kind'] = 'rss'
        src['feed'] = feed_url
        src['feed_checked'] = True
        src['enabled'] = True
        src['last_check'] = today
        src['last_error'] = None
    json.dump({'sources': sources}, open(SOURCES, 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('\nЗаписано в sources.json: %d источников включено.' % len(found))


if __name__ == '__main__':
    main(sys.argv[1:])
