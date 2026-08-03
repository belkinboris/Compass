# -*- coding: utf-8 -*-
"""Мёртвые ссылки на источники — починить те, что чинятся разбором адреса.

ЗАЧЕМ. Проверка 1070 ссылок у карточек с единственным источником дала 11
мёртвых (404). У карточки с единственной мёртвой ссылкой обещание продукта —
«со ссылкой на первоисточник» — не выполнено: подтвердить факт нечем.

ЧТО ЗДЕСЬ ЧИНИТСЯ БЕЗ ПОИСКА. Оказалось, что часть адресов не «умерла», а
никогда и не была адресом статьи:

  * `connect.ok.ru/offer?url=…` — кнопка «поделиться», внутри которой
    настоящий адрес статьи лежит query-параметром. Ровно тот же дефект, что
    уже записан в CLAUDE.md про `wa.me/?text=…`;
  * `forbes-ru.turbopages.org/turbo/forbes.ru/s/…` — turbo-зеркало Яндекса, а
    не сайт издания; настоящий адрес выводится из пути;
  * `tadviser.ru/index.php/%25D0%259A…` — путь закодирован ДВАЖДЫ, и сервер
    ищет страницу с процентами в имени;
  * `tadviser.ru/index.php/Ozon%22%20%5Co%20%22Ozon` — в адрес попал кусок
    HTML-атрибута (`" title="`), то есть ссылку вырезали из разметки вместе с
    хвостом.

ЧЕГО ЗДЕСЬ НАМЕРЕННО НЕ ЧИНИМ. Две ссылки ведут на Википедию и «чинятся»
теми же приёмами — но у карточки Kellogg / «Черноголовка» это статья
«Нью-Йоркская фондовая биржа», а у «Северстали» — статья о самой компании.
Восстановив адрес, мы получили бы РАБОЧУЮ ссылку на страницу, которая сделку
не подтверждает; видимый 404 честнее. Такие карточки идут в список для живого
поиска.

ГРАНИЦА. Ни один восстановленный адрес не записывается «на веру»: каждый
кандидат сначала запрашивается, и в базу идёт только тот, что ответил 200.
Что не починилось разбором — остаётся в отчёте для живого поиска; выдумывать
ссылку нельзя, а стирать её нельзя тем более (тест
`test_every_deal_has_a_source_link` требует хотя бы одну http-ссылку у каждой
карточки, и пустой список — не более честное решение, а другое нарушение).

Запуск:
    python3 pipeline/fix_dead_source_links.py            # сухой прогон
    python3 pipeline/fix_dead_source_links.py --write    # записать
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STATUS = os.path.join(ROOT, 'data', 'inbox', 'raw', 'link_status.json')

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; KompasBot/1.0)'}
DEAD = (404, 410)
TURBO = re.compile(r'^https?://([a-z0-9-]+)\.turbopages\.org/turbo/([^/]+)/s/(.*)$', re.I)


def candidates(url):
    """Возможные настоящие адреса — по убыванию доверия. Ничего не выдумываем:
    все они выводятся ИЗ САМОГО адреса."""
    out = []
    parsed = urllib.parse.urlparse(url)

    # Кнопка «поделиться»: настоящий адрес лежит параметром.
    query = urllib.parse.parse_qs(parsed.query)
    for name in ('url', 'u', 'link'):
        for value in query.get(name, []):
            if value.startswith('http'):
                out.append(value)

    # Turbo-зеркало Яндекса: /turbo/<хост>/s/<путь>.
    turbo = TURBO.match(url)
    if turbo:
        out.append('https://%s/%s' % (turbo.group(2), turbo.group(3)))

    # Двойное кодирование: «%25D0%259A» вместо «%D0%9A».
    if '%25' in url:
        out.append(urllib.parse.unquote(url))

    # Хвост HTML-атрибута, попавший в адрес вместе со ссылкой.
    cut = re.split(r'%22|%5[Cc]o|&amp;|&quot;', url)[0].rstrip('%')
    if cut != url and cut.startswith('http'):
        out.append(cut)

    # Википедия источником сделки не бывает. У карточки Kellogg / «Черноголовка»
    # ссылка вела на статью «Нью-Йоркская фондовая биржа», у «Северстали» — на
    # статью о самой компании: починив адрес, мы получили бы РАБОЧУЮ ссылку на
    # страницу, которая сделку не подтверждает. Это хуже видимого 404 — тот
    # хотя бы честно показывает, что источника нет. Такие карточки уходят в
    # список для живого поиска.
    return [u for u in dict.fromkeys(out)
            if u != url and 'wikipedia.org' not in urllib.parse.urlparse(u).netloc]


def code(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read(512)
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code
    except Exception as err:
        return type(err).__name__


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    status = json.load(open(STATUS, encoding='utf-8')) if os.path.exists(STATUS) else {}
    dead = {u for u, c in status.items() if c in DEAD}
    assert dead, 'нет данных о мёртвых ссылках — сначала check_source_links.py'

    fixes, left = [], []
    for deal in data['deals']:
        for i, src in enumerate(deal.get('src') or []):
            if len(src) < 2 or str(src[1]) not in dead:
                continue
            found = None
            for candidate in candidates(str(src[1])):
                if code(candidate) == 200:
                    found = candidate
                    break
            if found:
                fixes.append((deal, i, str(src[1]), found))
            else:
                left.append((deal, str(src[1])))

    print('ПОЧИНЕНО РАЗБОРОМ АДРЕСА: %d' % len(fixes))
    for deal, _, old, new in fixes:
        print('   %-13s %s' % (deal['id'], str(deal.get('title'))[:56]))
        print('       было : %s' % old[:96])
        print('       стало: %s' % new[:96])
    print('\nНЕ ЧИНИТСЯ РАЗБОРОМ, нужен живой поиск: %d' % len(left))
    for deal, old in left:
        print('   %-13s %-52s %s' % (deal['id'], str(deal.get('title'))[:52], old[:60]))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, i, old, new in fixes:
        assert str(deal['src'][i][1]) == old, '%s: ссылка уже другая' % deal['id']
        deal['src'][i][1] = new
        # Подпись источника — имя издания по домену, а не «как узнали»:
        # у turbo-зеркала и кнопки «поделиться» она была бессмысленной.
        host = urllib.parse.urlparse(new).netloc.lower().replace('www.', '')
        if not str(deal['src'][i][0] or '').strip() or 'turbo' in str(deal['src'][i][0]).lower():
            deal['src'][i][0] = host
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s (ссылок восстановлено: %d)' % (os.path.relpath(DATA, ROOT), len(fixes)))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
