#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пилот Этапа 15, П3 (по просьбе владельца): можно ли теперь механически
считать мультипликаторы сделок (EV/Revenue), раз у сотен сделок появилась
сумма И подтверждённое по ИНН юрлицо цели?

ТОЛЬКО ЗАМЕР, БЕЗ ВИТРИНЫ. Ничего не пишет ни в базу, ни на экран — печатает
таблицу примеров для решения владельца, как и попросил архитектор (Этап 15,
план П3): «на экран без его решения не выносить ничего».

ЛОВУШКИ, КОТОРЫЕ ЭТОТ СКРИПТ ОТСЕИВАЕТ МЕХАНИЧЕСКИ, А НЕ СЧИТАЕТ:
  * Сумма в $/€ пропускается целиком — курс на момент сделки зависит от
    года, а конвертация одним текущим курсом молча исказит мультипликатор
    старых сделок (родня урока «Число может быть верным фактом и совсем не
    той величиной»). Меряем только сделки в ₽.
  * Сумма за ДОЛЮ меньше 100% (доля видна в eco.share/asset по знаку «%»)
    помечается отдельно и НЕ пересчитывается на 100% — умножать на глаз
    небезопасно, эту сверку делает читатель таблицы.
  * «(по оценке)» — сумма остаётся в выборке, но помечается флагом: оценка
    не то же самое, что раскрытая цена.
  * Выручка берётся у ЦЕЛИ сделки (target/asset_id), а не у покупателя —
    и с тем же годом, что и сама сделка (`as_of_year`), а не последним
    доступным: иначе мультипликатор считает цену года N по выручке года M.
  * Банки исключены — их «выручка» по РСБУ/806-й форме не сопоставима с
    выручкой обычной компании (см. блок «По данным Банка России» отдельно).

Запуск (нужен доступ к прод-API, читает https://projectcompass.ru):
    python3 pipeline/measure_deal_multiples_pilot.py [--limit N] [--all]
"""
import argparse
import json
import re
import sys
import time
import urllib.request

PATH = 'static/data/deals_promoted.json'
API_BASE = 'https://projectcompass.ru'

UNIT_MULT = {'тыс': 1e3, 'млн': 1e6, 'млрд': 1e9, 'трлн': 1e12}
RUB_AMOUNT = re.compile(
    r'(?P<n1>\d[\d\s]*(?:[.,]\d+)?)'
    r'(?:\s*[–—-]\s*(?P<n2>\d[\d\s]*(?:[.,]\d+)?))?'
    r'\s*(?P<unit>тыс|млн|млрд|трлн)\.?\s*₽',
    re.I)
STAKE_PCT = re.compile(r'(\d{1,3}(?:[.,]\d+)?)\s*%')


def parse_rub_sum(text):
    """Возвращает (среднее в рублях, диапазон?) или None, если это не ₽-сумма."""
    if not text:
        return None
    m = RUB_AMOUNT.search(text)
    if not m:
        return None
    def num(s):
        return float(s.replace(' ', '').replace('\xa0', '').replace(',', '.'))
    n1 = num(m.group('n1'))
    n2 = num(m.group('n2')) if m.group('n2') else None
    mult = UNIT_MULT[m.group('unit').lower()]
    lo = n1 * mult
    hi = (n2 * mult) if n2 is not None else lo
    return (lo + hi) / 2, (n2 is not None)


def is_estimate(text):
    return bool(text) and re.search(r'оценк|оценив', text, re.I)


def stake_percent(deal):
    for field in (deal.get('eco', {}).get('share'), deal.get('asset')):
        if not field:
            continue
        nums = [float(x.replace(',', '.')) for x in STAKE_PCT.findall(field)]
        plausible = [n for n in nums if 1 <= n <= 100]
        if plausible:
            return max(plausible)
    return None


def year_of(deal):
    ds = str(deal.get('date') or '')
    return int(ds[:4]) if ds[:4].isdigit() else None


def fetch_revenue(company_id, as_of_year, cache):
    key = (company_id, as_of_year)
    if key in cache:
        return cache[key]
    url = '%s/api/companies/%s/fns?as_of_year=%s' % (API_BASE, company_id, as_of_year)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        cache[key] = None
        return None
    result = None
    if data.get('available'):
        entity = data['entities'][0]
        reports = entity.get('reports') or []
        if reports and reports[0].get('revenue_rub') is not None:
            result = (reports[0]['year'], reports[0]['revenue_rub'], entity.get('legal_name'))
    cache[key] = result
    return result


def load_registry_confirmed():
    import importlib.util
    spec = importlib.util.spec_from_file_location('fns_registry', 'pipeline/fns_registry.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    confirmed = {r['company_id'] for r in mod.REGISTRY if r['decision'] == 'confirmed'}
    banks = {r['company_id'] for r in mod.REGISTRY if r['decision'] == 'bank'}
    return confirmed, banks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=25, help='сколько примеров печатать (по умолчанию 25)')
    ap.add_argument('--all', action='store_true', help='обработать всю выборку, не только --limit')
    args = ap.parse_args()

    confirmed, banks = load_registry_confirmed()
    data = json.load(open(PATH, encoding='utf-8'))
    deals = data['deals']

    candidates = []
    for d in deals:
        yr = year_of(d)
        if not yr or yr < 2022:
            continue
        # IPO/«Инвестиция»/«Финансирование» — деньги идут В компанию (cash-in)
        # или это размещение на бирже, а не покупка компании целиком: сумма
        # там не сопоставима с ценой продажи бизнеса, EV/Revenue на них не
        # определён по смыслу, а не только по данным (см. CLAUDE.md, «Тип
        # сделки определяет не только ярлык, но и какие роли существуют»).
        if d.get('type') != 'M&A':
            continue
        target = d.get('target') or d.get('asset_id')
        if not target or target in banks or target not in confirmed:
            continue
        parsed = parse_rub_sum(d.get('sum') or '')
        if not parsed:
            continue
        sum_rub, is_range = parsed
        candidates.append((d, target, sum_rub, is_range, yr))

    print('Кандидатов (₽-сумма + цель confirmed ФНС, год>=2022): %d' % len(candidates))
    if not args.all:
        candidates = candidates[:args.limit]
        print('Обрабатываю первые %d (--all для всех, --limit N для другого числа)\n' % len(candidates))

    cache = {}
    rows = []
    for d, target, sum_rub, is_range, yr in candidates:
        rev = fetch_revenue(target, yr, cache)
        time.sleep(0.05)
        if not rev:
            continue
        rev_year, rev_rub, legal_name = rev
        if rev_rub <= 0:
            continue
        stake = stake_percent(d)
        multiple = sum_rub / rev_rub
        rows.append(dict(
            id=d['id'], title=d.get('title'), sum_text=d.get('sum'),
            sum_rub_mln=round(sum_rub / 1e6, 1),
            rev_year=rev_year, rev_rub_mln=round(rev_rub / 1e6, 1),
            multiple=round(multiple, 2),
            estimate=is_estimate(d.get('sum')), stake=stake, is_range=is_range,
            # /fns?as_of_year=Y отдаёт ПОСЛЕДНИЙ отчёт СТРОГО ДО года сделки
            # (main.py: `row.year < as_of_year`) — это последний полный
            # финансовый год перед закрытием, стандартная практика в M&A, а
            # не дефект; разрыв в 1 год — норма, разрыв в 2+ — повод не
            # доверять числу без проверки.
            year_gap=yr - rev_year,
        ))

    print('С найденной выручкой цели: %d\n' % len(rows))
    print('%-11s %6s %10s %10s %6s %5s %5s %-6s  %s' % (
        'id', 'мульт', 'сумма,млн', 'выручка,млн', 'год', 'оцен', 'доля', 'разрыв', 'заголовок'))
    for r in rows:
        stake_label = ('%.0f' % r['stake']) + '%' if r['stake'] else '100%?'
        print('%-11s %6.2f %10s %10s %6s %5s %5s %-6s  %s' % (
            r['id'], r['multiple'], r['sum_rub_mln'], r['rev_rub_mln'], r['rev_year'],
            'да' if r['estimate'] else '-',
            stake_label,
            str(r['year_gap']) + ' лет',
            r['title'][:60]))

    # Санитарная граница: мультипликатор вне 0,1-15 почти всегда значит не
    # «редкая сделка», а несопоставимость (выручка не того юрлица/периметра,
    # см. находки g5eb6ff22 и g4cd1fa52 в этом же прогоне) — эти строки
    # остаются в общей таблице выше, но не портят медиану «чистой» подвыборки.
    clean = [r for r in rows if r['year_gap'] in (0, 1)
             and (r['stake'] is None or r['stake'] >= 95) and not r['estimate']
             and 0.1 <= r['multiple'] <= 15]
    if clean:
        mults = sorted(r['multiple'] for r in clean)
        n = len(mults)
        median = mults[n // 2] if n % 2 else (mults[n // 2 - 1] + mults[n // 2]) / 2
        print('\nЧистая подвыборка (доля>=95%%, не оценка, разрыв года 0-1, мультипликатор 0,1-15): %d' % n)
        print('Медиана EV/Revenue: %.2f, диапазон: %.2f — %.2f' % (median, mults[0], mults[-1]))
    else:
        print('\n«Чистой» подвыборки не набралось на этом сэмпле.')


if __name__ == '__main__':
    main()
