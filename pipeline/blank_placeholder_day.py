# -*- coding: utf-8 -*-
"""Дата-заглушка «1 января» превращается в честный «только год».

ЗАЧЕМ. У 238 карточек дата стоит ровно 1 января — это не день сделки, а след
компактного импорта: год из источника брали, месяц и день не брали. Пока такая
запись лежит в базе, сайт УТВЕРЖДАЕТ то, чего не знает: карточка показывает
«1 янв. 2024», лента ставит её первым числом, а помесячный график аналитики
рисует январский всплеск, которого на рынке не было (в январе 2025 — 52 сделки
против 12–37 в остальные месяцы, и 42 из них — эта заглушка).

ПОЧЕМУ НЕ ВОССТАНОВИТЬ. Пробовали и исчерпали: `fix_placeholder_dates.py`
скачивает дату публикации статьи-источника и применяет её, если ГОД статьи
совпадает с годом карточки. За два прогона так восстановлено 131 дата; на
последнем прогоне из 245 оставшихся нашлась ровно ОДНА. Остальным помочь
нечем: у 162 источник вообще не отдаёт дату публикации, у 82 год статьи не
совпадает с годом карточки — там неверен, возможно, и сам год, и слепая
подстановка перенесла бы сделку в другой год. Полная дата в адресе статьи
(`/2025/03/14/`) нашлась у 6 карточек, и лишь у 3 из них год совпал; в тексте
самих карточек полной даты нет ни у одной.

ЧТО ДЕЛАЕМ ВМЕСТО ЭТОГО. Убираем ложную точность: `2024-01-01` -> `2024`.
Год мы знаем и его не теряем — исчезает только выдуманный день. На экране
такая дата читается «2024 год», в помесячный график не попадает вовсе, а
подпись под графиком прямо говорит, у скольких сделок известен только год.
Это ровно то же решение, что и с суммой: пустое честнее правдоподобного.

ГРАНИЦА И ПРОВЕРКИ. Правим только `YYYY-01-01` и только там, где первое
января ничем не подтверждено:
  * ни один источник карточки не опубликован 1 января этого года
    (сверяется по кэшу `fix_placeholder_dates.py`);
  * в тексте самой карточки не написано «1 января».
Замер на текущей базе: подтверждённых нет ни одной, то есть под правку идут
все 238. Если завтра появится настоящая сделка первого января, скрипт её не
тронет. `unknown` не трогаем — там нет и года.

Запуск:
    python3 pipeline/blank_placeholder_day.py            # сухой прогон
    python3 pipeline/blank_placeholder_day.py --write    # записать
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CACHE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'source_dates.json')

PLACEHOLDER = re.compile(r'^(\d{4})-01-01$')
FIRST_OF_JANUARY = re.compile(r'\b1\s+января\s+20\d\d')


def urls_of(deal):
    return [s[1] for s in (deal.get('src') or [])
            if isinstance(s, (list, tuple)) and len(s) > 1 and isinstance(s[1], str)]


def confirmed_first_of_january(deal, cache):
    """Первое января подтверждено — трогать нельзя."""
    if any(cache.get(url) == deal['date'] for url in urls_of(deal)):
        return 'дата статьи-источника совпадает с 1 января'
    if FIRST_OF_JANUARY.search(json.dumps(deal, ensure_ascii=False)):
        return 'в тексте карточки написано «1 января»'
    return None


def _self_check():
    """Правило проверяется на себе, а не на глаз."""
    assert PLACEHOLDER.match('2024-01-01').group(1) == '2024'
    # Любой другой день — не заглушка и под правило не попадает.
    assert not PLACEHOLDER.match('2024-01-02')
    assert not PLACEHOLDER.match('2024-11-01')
    assert not PLACEHOLDER.match('2024')
    assert not PLACEHOLDER.match('unknown')
    # Подтверждение читается и из кэша, и из текста карточки.
    card = {'date': '2024-01-01', 'src': [['Ъ', 'http://x/1']], 'extra': ''}
    assert confirmed_first_of_january(card, {'http://x/1': '2024-01-01'})
    assert confirmed_first_of_january(card, {'http://x/1': '2024-03-05'}) is None
    assert confirmed_first_of_january({'date': '2024-01-01', 'src': [],
                                       'extra': 'закрыта 1 января 2024 года'}, {})


def main(write=False):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    if not cache:
        print('ВНИМАНИЕ: кэша дат статей нет (data/inbox/raw/source_dates.json).')
        print('Сначала `python3 pipeline/fix_placeholder_dates.py --fetch`, иначе')
        print('настоящее первое января отличить не от чего.')
        return 1

    plan, kept = [], []
    for deal in data['deals']:
        found = PLACEHOLDER.match(str(deal.get('date') or ''))
        if not found:
            continue
        why = confirmed_first_of_january(deal, cache)
        if why:
            kept.append((deal['id'], why, deal.get('title')))
        else:
            plan.append((deal, found.group(1)))

    print('Заглушек «1 января»: %d' % (len(plan) + len(kept)))
    print('  оставляем как есть (первое января подтверждено): %d' % len(kept))
    for deal_id, why, title in kept[:10]:
        print('     %-12s %s — %s' % (deal_id, why, str(title)[:60]))
    print('  снимаем выдуманный день: %d' % len(plan))
    for deal, year in plan[:8]:
        print('     %-12s %s -> %s  %s' % (deal['id'], deal['date'], year, str(deal.get('title'))[:56]))
    if len(plan) > 8:
        print('     ... и ещё %d' % (len(plan) - 8))

    years = {}
    for deal, year in plan:
        years[year] = years.get(year, 0) + 1
    print('  по годам: %s' % ', '.join('%s — %d' % kv for kv in sorted(years.items())))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    if not plan:
        print('\nЗаписывать нечего.')
        return 0

    for deal, year in plan:
        assert deal['date'].endswith('-01-01'), 'состояние поля изменилось: %r' % deal['date']
        deal['date'] = year
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s (карточек: %d)' % (os.path.relpath(DATA, ROOT), len(plan)))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
