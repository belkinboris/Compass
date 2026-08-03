# -*- coding: utf-8 -*-
"""Живы ли ссылки на источники — и особенно у карточек с единственной ссылкой.

ЗАЧЕМ. 71% карточек держатся на одной ссылке. Обещание продукта — «со ссылкой
на первоисточник» (первая строка PRODUCT_ROADMAP.md), и у карточки с
единственной мёртвой ссылкой оно не выполнено: подтвердить факт нечем.
Добрать второй источник по каждой карточке дорого, а проверить, что
имеющийся жив, — дёшево и отвечает ровно на тот же вопрос: где мы уже
ничем не подкреплены.

ЧТО СЧИТАЕТСЯ МЁРТВОЙ ССЫЛКОЙ. Только ответ 404 и 410 — «страницы нет».
403 и 401 не считаются: у части изданий (rbc.ru) так отвечает защита от
роботов, а человеку страница открывается; считать их мёртвыми значило бы
пометить сотни живых карточек. Таймаут и обрыв соединения — тоже не
приговор, а неудача одной попытки: они идут отдельной строкой отчёта.

СКРИПТ НИЧЕГО НЕ ПРАВИТ. Он только меряет и печатает список — решение по
каждой мёртвой ссылке принимает человек, потому что вариантов два и они
разные: найти живую замену или честно подписать «источник не подтверждён»
(так уже сделано у карточки `g2544a5cb`).

Запуск:
    python3 pipeline/check_source_links.py            # только карточки с одной ссылкой
    python3 pipeline/check_source_links.py --all      # все ссылки базы
"""
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CACHE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'link_status.json')

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; KompasBot/1.0)'}
DEAD = (404, 410)


def status(url):
    """Код ответа или строка с причиной неудачи. HEAD часто запрещён, поэтому
    сразу GET, но читаем только начало — тело страницы нам не нужно."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read(2048)
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code
    except Exception as err:
        return type(err).__name__


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    scope = deals if '--all' in argv else [d for d in deals if len(d.get('src') or []) == 1]
    print('карточек в проверке: %d из %d' % (len(scope), len(deals)))

    urls, owner = [], {}
    for deal in scope:
        for src in deal.get('src') or []:
            if len(src) > 1 and str(src[1]).startswith('http'):
                urls.append(str(src[1]))
                owner.setdefault(str(src[1]), []).append(deal)
    urls = sorted(set(urls))

    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    todo = [u for u in urls if u not in cache]
    print('ссылок всего %d, к проверке %d (в кэше %d)' % (len(urls), len(todo), len(urls) - len(todo)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, (url, code) in enumerate(zip(todo, pool.map(status, todo)), 1):
            cache[url] = code
            if i % 100 == 0:
                print('  ... %d из %d' % (i, len(todo)))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    buckets = {}
    for url in urls:
        buckets.setdefault(cache.get(url), []).append(url)
    print('\nответы:')
    for code, group in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        print('   %-14s %4d' % (code, len(group)))

    dead = [u for u in urls if cache.get(u) in DEAD]
    print('\nМЁРТВЫХ ССЫЛОК (404/410): %d' % len(dead))
    hurt = sorted({d['id'] for u in dead for d in owner.get(u, []) if len(d.get('src') or []) == 1})
    print('карточек, у которых это ЕДИНСТВЕННЫЙ источник: %d' % len(hurt))
    by_id = {d['id']: d for d in deals}
    for deal_id in hurt[:25]:
        deal = by_id[deal_id]
        print('   %-13s %s  %s' % (deal_id, deal.get('date'), str(deal.get('title'))[:56]))
    if len(hurt) > 25:
        print('   ... и ещё %d' % (len(hurt) - 25))
    print('\nСкрипт ничего не изменил: это замер.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
