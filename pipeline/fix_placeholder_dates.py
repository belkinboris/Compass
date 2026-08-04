# -*- coding: utf-8 -*-
"""Даты-заглушки «1 января» — восстановить по дате статьи-источника.

ЗАЧЕМ. У 368 карточек (24% базы) стоит дата ровно 1 января, и ещё у семи —
строка «unknown». Это след компактного импорта: год из источника брали, месяц
и день не брали. Дата — не украшение: по ней считается год в ленте и в
аналитике и строится порядок карточек, поэтому сделка июня 2023 года лежит в
1 января 2023-го, а все 131 сделка 2024 года навалены одной кучей на первое
число. Тот же дефект в единственном экземпляре уже чинился у карточки ЛУКОЙЛ
/ Carlyle, где заглушка 1 января 2022 года стояла на сделке 2026 года.

ОТКУДА БЕРЁТСЯ ДАТА. Из самой статьи по ссылке карточки — мета-поля
`article:published_time` или `datePublished`. Это не догадка и не память: у
каждой правки есть проверяемый источник, тот самый, что уже стоит в карточке.
Если у карточки несколько ссылок, берётся САМАЯ РАННЯЯ дата: первое сообщение
о сделке ближе к самой сделке, чем позднейший пересказ.

ГЛАВНАЯ ЗАЩИТА — ГОД. Дата публикации статьи не равна дате сделки: подборка
«Коммерсантъ — «Сделки года»» вышла 30 сентября и описывает сделки всего
года. Поэтому дата применяется ТОЛЬКО если год статьи совпадает с годом
карточки: тогда правка восстанавливает месяц и день внутри уже известного
года и ничего нового не утверждает. Расхождение по году не правится молча —
оно попадает в отчёт для чтения человеком. У карточек с датой «unknown» года
нет вообще, поэтому они тоже только в отчёт.

ПОЧЕМУ НЕ ПРОСТО «ПОСТАВИТЬ ДАТУ СТАТЬИ». Пробовали мысленно и отвергли:
из пяти проверенных вручную карточек у одной год статьи (2026) отличался от
года карточки (2025) — то есть у части записей неверен и год, и слепая
подстановка перенесла бы сделку в другой год вместо того, чтобы показать
человеку, что с карточкой что-то не так.

Запуск:
    python3 pipeline/fix_placeholder_dates.py --fetch     # скачать даты статей в кэш
    python3 pipeline/fix_placeholder_dates.py             # сухой прогон по кэшу
    python3 pipeline/fix_placeholder_dates.py --write     # записать
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CACHE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'source_dates.json')

# Дата публикации в разметке страницы. Оба поля — стандартные (Open Graph и
# schema.org), и их отдаёт большинство изданий из нашего реестра.
META = re.compile(
    r'(?:article:published_time|datePublished|"dateCreated")["\']?\s*[:=]\s*["\']'
    r'([0-9]{4}-[0-9]{2}-[0-9]{2})', re.I)

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; KompasBot/1.0)'}
MAX_SOURCES = 3        # больше трёх ссылок у карточки почти не бывает
TIMEOUT = 20


def placeholders(deals):
    """Карточки с датой-заглушкой: ровно 1 января или нераспознанная строка."""
    out = []
    for d in deals:
        date = str(d.get('date') or '')
        if date.endswith('-01-01') or not date[:4].isdigit():
            out.append(d)
    return out


def urls_of(deal):
    return [str(s[1]) for s in (deal.get('src') or [])
            if len(s) > 1 and str(s[1]).startswith('http')][:MAX_SOURCES]


def published(url):
    """Дата публикации страницы или None. Ошибка сети — тоже None: источник,
    который не ответил, ничего не доказывает и молча ничего не меняет."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=TIMEOUT).read()
    except Exception:
        return None
    m = META.search(html.decode('utf-8', 'ignore'))
    return m.group(1) if m else None


def fetch(deals):
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    todo = [u for d in deals for u in urls_of(d) if u not in cache]
    print('ссылок к загрузке: %d (в кэше уже %d)' % (len(todo), len(cache)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, (url, date) in enumerate(zip(todo, pool.map(published, todo)), 1):
            cache[url] = date
            if i % 50 == 0:
                print('  ... %d из %d' % (i, len(todo)))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    got = sum(1 for v in cache.values() if v)
    print('дат получено: %d из %d ссылок (%.0f%%)' % (got, len(cache), 100.0 * got / max(len(cache), 1)))
    return cache


YEAR = re.compile(r'\b(20[12]\d)\b')


def card_text(deal):
    """Всё, что написано на карточке словами, — для проверки года по тексту."""
    eco, law = deal.get('eco') or {}, deal.get('law') or {}
    parts = [deal.get('title'), deal.get('extra')]
    parts += [eco.get(k) for k in ('share', 'rationale', 'context', 'val', 'target_fin')]
    parts += [law.get(k) for k in ('struct', 'appr', 'terms')]
    return ' '.join(str(p or '') for p in parts)


def corroborated(deal, date):
    """Подтверждает ли ТЕКСТ САМОЙ КАРТОЧКИ год статьи вместо года карточки.

    Расхождение по году правится только так. Замер по 86 расхождениям: текст
    карточки называет год статьи у 5, год карточки — у 7, у 74 года нет вовсе,
    и ни у одной оба года сразу. Правило берёт только первые пять: там дата
    статьи подтверждена вторым, независимым от неё свидетельством — словами
    самой карточки. Остальные 81 остаются как есть: у них нет ничего, кроме
    даты публикации, а она не равна дате сделки (подборка «Сделки года»
    выходит в сентябре и описывает весь год).
    """
    years = set(YEAR.findall(card_text(deal)))
    return date[:4] in years and str(deal.get('date') or '')[:4] not in years


def plan(deals, cache):
    """(правки, расхождения по году, без даты). Ничего не пишет."""
    fixes, conflicts, blank = [], [], []
    for d in deals:
        dates = sorted(x for x in (cache.get(u) for u in urls_of(d)) if x)
        if not dates:
            blank.append(d)
            continue
        best = dates[0]                      # самая ранняя публикация
        year = str(d.get('date') or '')[:4]
        if year.isdigit() and best[:4] == year:
            if best != d.get('date'):
                fixes.append((d, best))
        else:
            conflicts.append((d, best))
    return fixes, conflicts, blank


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    targets = placeholders(data['deals'])
    print('карточек с датой-заглушкой: %d' % len(targets))

    if '--fetch' in argv:
        fetch(targets)
        return 0

    if not os.path.exists(CACHE):
        print('Кэша нет. Сначала: python3 pipeline/fix_placeholder_dates.py --fetch')
        return 1
    cache = json.load(open(CACHE, encoding='utf-8'))
    fixes, conflicts, blank = plan(targets, cache)

    print('\nВОССТАНАВЛИВАЕТСЯ (год совпал, уточняются месяц и день): %d' % len(fixes))
    for d, date in fixes[:12]:
        print('   %-13s %s -> %s  %s' % (d['id'], d['date'], date, str(d.get('title'))[:52]))
    if len(fixes) > 12:
        print('   ... и ещё %d' % (len(fixes) - 12))

    backed = [(d, date) for d, date in conflicts if corroborated(d, date)]
    rest = [(d, date) for d, date in conflicts if not corroborated(d, date)]
    print('\nГОД СТАТЬИ ДРУГОЙ, НО ПОДТВЕРЖДЁН ТЕКСТОМ КАРТОЧКИ: %d' % len(backed))
    for d, date in backed:
        print('   %-13s %s -> %s  годы в тексте: %s  %s'
              % (d['id'], d.get('date'), date,
                 sorted(set(YEAR.findall(card_text(d)))), str(d.get('title'))[:40]))

    print('\nНЕ ПРАВИТСЯ, ГОД СТАТЬИ ДРУГОЙ И НИЧЕМ НЕ ПОДТВЕРЖДЁН: %d' % len(rest))
    for d, date in rest[:8]:
        print('   %-13s %s vs статья %s  %s' % (d['id'], d.get('date'), date, str(d.get('title'))[:46]))
    if len(rest) > 8:
        print('   ... и ещё %d' % (len(rest) - 8))

    print('\nИСТОЧНИК НЕ ОТДАЛ ДАТУ, карточка остаётся как есть: %d' % len(blank))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for d, date in fixes:
        deal = by_id[d['id']]
        # Проверка исходного состояния: правим только заглушку, а не дату,
        # которую кто-то уже уточнил между прогонами.
        assert str(deal.get('date') or '').endswith('-01-01'), \
            '%s: дата уже не заглушка (%r)' % (deal['id'], deal.get('date'))
        assert date[:4] == str(deal['date'])[:4], '%s: год разошёлся' % deal['id']
        deal['date'] = date
    for d, date in backed:
        deal = by_id[d['id']]
        old = str(deal.get('date') or '')
        assert old.endswith('-01-01') or not old[:4].isdigit(), \
            '%s: дата уже не заглушка (%r)' % (deal['id'], old)
        assert corroborated(deal, date), '%s: год статьи больше не подтверждён текстом' % deal['id']
        deal['date'] = date
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s (исправлено дат: %d)' % (os.path.relpath(DATA, ROOT), len(fixes) + len(backed)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
