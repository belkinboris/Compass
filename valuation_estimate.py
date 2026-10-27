# -*- coding: utf-8 -*-
"""Оценка цены сделки, когда она не раскрыта (прототип, 24 октября 2026).

Идея партнера: там, где в карточке «Не раскрыта», — кнопка «Оценить с
ассистентом». Нажал — получил вилку цены, расчет и все оговорки. Это НЕ факт
и в базу не пишется: оценка считается по запросу и подписана как оценка.

Кто что делает. Числа считает этот модуль — детерминированно, по
отчетности проданной компании и мультипликаторам сделок, где цена известна
(таблица `deal_multiples.compute_sector_table`, методика —
`docs/analytics_acceptance.md#мультипликаторы-по-отраслям-методика-таблицы-19-октября-2026`).
Ассистент только пересказывает результат по-человечески: модель не умеет
считать надежно, а выдуманная цифра в карточке ударит по доверию ко всей
базе.

Когда кнопки нет (`eligibility`): проданное не опознано как юрлицо с ИНН;
нет отчетности за год до сделки; выручки нет; продано имущество, а не
компания; банк, страховщик, фонд, холдинг без операционной выручки;
финансирование, IPO, временное управление. Партнер: «чтобы он совсем
какую-то бредятину не говорил, чтобы это было хотя бы сколько-то достоверно».
"""
from __future__ import annotations

import statistics
from typing import Any

METRICS = {
    # ключ: (поле отчетности-знаменатель, подпись, считается ли через EV)
    'ps': ('revenue_rub', 'цена к выручке', False),
    'ev_op': ('operating_profit_rub', 'стоимость бизнеса к прибыли от продаж', True),
    'pe': ('net_profit_rub', 'цена к чистой прибыли', False),
    'pbv': ('equity_rub', 'цена к собственному капиталу', False),
}
MIN_SAMPLE = 3              # меньше трех сделок в отрасли — берем все отрасли
# Отрасли и коды ОКВЭД, где оценка по выручке и прибыли вводит в заблуждение.
NOT_BY_MULTIPLES_IND = {'Банки', 'Страхование', 'Рынок ценных бумаг', 'Финансовые услуги'}
NOT_BY_MULTIPLES_OKVED = ('64.', '65.', '66.')      # финансы, страхование, фонды и холдинги
# Государство забрало актив по суду или указу — цены нет по определению.
NO_PRICE_BY_NATURE = ('в доход государства', 'национализ', 'изъят', 'временное управление')
NOT_A_SALE_TYPES = {'Временное управление', 'Финансирование · структурная сделка', 'IPO',
                    'Реорганизация', 'Создание СП', 'Инвестиция'}
MIN_REVENUE_RUB = 30_000_000   # меньше — отчетность слишком мала, мультипликатор бессмыслен
# Цена к выручке — только по сделкам СВОЕЙ отрасли: маржа у отраслей разная в
# разы, и выручка туроператора, умноженная на медиану всех отраслей, дала
# «Библио-Глобусу» 375 млрд ₽ (прогон 24 октября 2026). Цена к капиталу — только
# там, где бизнес и есть его активы.
SECTOR_ONLY = {'ps'}
ASSET_HEAVY = {'Недвижимость', 'ГМК и добыча', 'Нефть и газ', 'Уголь', 'Энергетика',
               'Порты и инфраструктура', 'Гостиницы и туризм', 'Агро', 'Лесопром'}


# ВНЕШНИЕ ОРИЕНТИРЫ (24 октября 2026). Своих сделок с ценой, долей и
# отчетностью у нас около тридцати — медиана по отрасли почти нигде не
# складывается. Поэтому главный способ — средний EV/EBITDA сделок отрасли из
# обзора рынка M&A Б1 и Mergers.ru (данные Advance Capital), ИТ — из обзора
# Tech M&A 2025. Полный список с цитатами и адресами —
# data/inbox/valuation/benchmarks.json, разбор — benchmarks.md.
SURVEY_2024 = ('Б1 и Mergers.ru, «Исследование рынка M&A: итоги 2024 года» (данные Advance Capital)',
               'https://mergers.ru')
TECH_2025 = ('«2025 Tech M&A» (Б1 и Advance Capital, апрель 2026)', 'https://b1.ru')
BENCHMARK_EV_EBITDA = {
    # отрасль сайта: (EV/EBITDA, год, источник)
    'ИТ и интернет': (6.1, 2025, TECH_2025), 'Искусственный интеллект': (6.1, 2025, TECH_2025),
    'Телеком': (6.1, 2024, SURVEY_2024), 'Медиа': (7.1, 2025, TECH_2025), 'E-commerce': (6.1, 2024, SURVEY_2024),
    'Здравоохранение': (5.5, 2024, SURVEY_2024), 'Гостиницы и туризм': (5.5, 2024, SURVEY_2024),
    'Образование': (5.5, 2024, SURVEY_2024), 'Развлечения': (5.5, 2024, SURVEY_2024),
    'Транспорт и логистика': (5.4, 2024, SURVEY_2024), 'Порты и инфраструктура': (5.4, 2024, SURVEY_2024),
    'Агро': (5.2, 2024, SURVEY_2024), 'Ритейл': (5.0, 2024, SURVEY_2024),
    'Пищепром и напитки': (4.3, 2024, SURVEY_2024), 'Потребительские товары': (4.3, 2024, SURVEY_2024),
    'Фармацевтика': (4.3, 2024, SURVEY_2024), 'Производство тары': (4.3, 2024, SURVEY_2024),
    'ГМК и добыча': (3.8, 2024, SURVEY_2024), 'Машиностроение': (3.8, 2024, SURVEY_2024),
    'Химия и удобрения': (3.8, 2024, SURVEY_2024), 'Уголь': (3.8, 2024, SURVEY_2024),
    'Лесопром': (3.8, 2024, SURVEY_2024), 'Автопром': (3.8, 2024, SURVEY_2024),
    'Нефть и газ': (3.8, 2024, SURVEY_2024), 'Строительство': (3.8, 2024, SURVEY_2024),
    'Энергетика': (3.6, 2024, SURVEY_2024),
}
MARKET_EV_EBITDA = (4.8, 2024, ('РБК по данным Advance Capital: медиана EV/EBITDA сделок 2024 года', 'https://www.rbc.ru'))
BENCH_BAND = (0.75, 1.25)    # вилка вокруг средней — средняя по нескольким десяткам сделок, не точка
MINORITY_FACTOR = (0.6, 1.0)  # доля меньше 50%: без контроля стоит дешевле (НЦПО — нижняя граница)
FOREIGN_EXIT_FACTOR = (0.35, 0.45)  # выход иностранца: дисконт не меньше 60% к рыночной оценке с октября 2024


def is_foreign_exit(deal: dict, seller_decision: str | None) -> bool:
    """Продает иностранный владелец, уходящий из России: продавец в реестре —
    иностранное юрлицо, или в заголовке «российский бизнес» компании. Такие
    сделки с октября 2024 года идут через правкомиссию с дисконтом не меньше
    60% к рыночной оценке — средний мультипликатор рынка к ним не подходит."""
    title = str(deal.get('title') or '').lower()
    return seller_decision == 'foreign' or 'российского бизнеса' in title or 'российский бизнес' in title


def benchmark_method(deal: dict, report: dict, net_debt: float) -> dict | None:
    """Главный способ: прибыль от продаж × средний EV/EBITDA сделок отрасли.

    Прибыль от продаж (строка 2200) — это EBITDA за вычетом амортизации,
    поэтому оценка выходит ниже настоящей, сильнее всего в капиталоемких
    отраслях. Так и пишем: это нижняя часть вилки, а не середина рынка."""
    op = _n(report.get('operating_profit_rub'))
    if op is None or op <= 0:
        return None
    mult, year, src = BENCHMARK_EV_EBITDA.get(deal.get('ind')) or MARKET_EV_EBITDA
    scope = 'отрасль' if deal.get('ind') in BENCHMARK_EV_EBITDA else 'весь рынок'
    vals = [op * mult * k - net_debt for k in (BENCH_BAND[0], 1.0, BENCH_BAND[1])]
    if vals[2] <= 0:
        return None
    return {'metric': 'bench_ev_ebitda', 'label': 'средний EV/EBITDA сделок отрасли (обзор рынка)',
            'base_rub': op, 'scope': scope, 'multiple': (round(mult * BENCH_BAND[0], 1), mult, round(mult * BENCH_BAND[1], 1)),
            'full_rub': (max(vals[0], 0), vals[1], vals[2]), 'source': src, 'source_year': year,
            'note': 'по прибыли от продаж: амортизация в отчетности ФНС не видна, оценка занижена'}


def _n(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def report_before(reports: list[dict], deal_year: int | None) -> dict | None:
    """Отчет за последний полный год ДО сделки (год сделки — нет: аудит
    5 сентября 2026); если такого нет — None, а не ближайший после."""
    rows = [r for r in reports or [] if r.get('year') and _n(r.get('revenue_rub')) is not None]
    if deal_year:
        rows = [r for r in rows if r['year'] < deal_year]
    return max(rows, key=lambda r: r['year']) if rows else None


def comparables(rows: list[dict], industry: str | None) -> dict[str, dict]:
    """По каждому мультипликатору — значения сделок отрасли (если их ≥ 3) или
    всех отраслей, с перечнем сделок для ссылок."""
    out = {}
    for m in METRICS:
        def pick(pool):
            return [(r, r['metrics'][m]['value']) for r in pool
                    if (r.get('metrics') or {}).get(m, {}).get('status') == 'ok'
                    and r['metrics'][m].get('value')]
        same = pick([r for r in rows if industry and r.get('industry') == industry])
        scope, vals = ('отрасль', same) if len(same) >= MIN_SAMPLE else ('все отрасли', pick(rows))
        if len(vals) < MIN_SAMPLE:
            continue
        nums = sorted(v for _, v in vals)
        q = statistics.quantiles(nums, n=4) if len(nums) >= 4 else [nums[0], statistics.median(nums), nums[-1]]
        out[m] = {'scope': scope, 'n': len(nums), 'p25': q[0], 'median': statistics.median(nums), 'p75': q[-1],
                  'deals': [{'id': r['id'], 'title': r['title'], 'value': v} for r, v in vals]}
    return out


def eligibility(deal: dict, target_entity: dict | None, report: dict | None) -> str | None:
    """None — оценивать можно; иначе причина по-человечески."""
    if any(w in str(deal.get('title') or '').lower() for w in NO_PRICE_BY_NATURE):
        return 'актив перешел государству — цены у такой сделки нет'
    if deal.get('type') in NOT_A_SALE_TYPES:
        return 'это не продажа компании (%s)' % deal.get('type')
    if deal.get('ind') in NOT_BY_MULTIPLES_IND:
        return 'банки, страховщиков и фонды оценивают по капиталу и активам, а не по выручке'
    if not target_entity:
        return 'проданная компания не опознана как юрлицо с ИНН'
    if str(target_entity.get('okved') or '').startswith(NOT_BY_MULTIPLES_OKVED):
        return 'вид деятельности проданной компании — финансы или холдинг, оценка по выручке не годится'
    if not report:
        return 'нет отчетности проданной компании за год до сделки'
    if (_n(report.get('revenue_rub')) or 0) < MIN_REVENUE_RUB:
        return 'выручка проданной компании слишком мала или ее нет — оценка по мультипликаторам бессмысленна'
    return None


def estimate(deal: dict, report: dict, comps: dict[str, dict], stake_pct: float | None,
             foreign_exit: bool = False) -> dict:
    """Вилка цены за 100% и за купленную долю по каждому применимому методу."""
    # У малых компаний (упрощенная форма) строки 2200 нет — прибыль от продаж
    # считается из строк выручки и расходов, как в карточке компании.
    if _n(report.get('operating_profit_rub')) is None:
        import company_finance
        op, _basis = company_finance.operating_profit_estimate(
            None, company_finance.lines_from_full(report.get('full_lines')))
        report = dict(report, operating_profit_rub=op)
    net_debt = (_n(report.get('borrowings_rub')) or 0) - (_n(report.get('cash_rub')) or 0)
    methods = []
    for m, (field, label, via_ev) in METRICS.items():
        base = _n(report.get(field))
        c = comps.get(m)
        if not c or base is None:
            continue
        if m in SECTOR_ONLY and c['scope'] != 'отрасль':
            methods.append({'metric': m, 'label': label,
                            'skipped': 'в отрасли меньше трех сделок с известной ценой, а по чужим отраслям выручку сравнивать нельзя'})
            continue
        if m == 'pbv' and deal.get('ind') not in ASSET_HEAVY:
            continue
        if base <= 0:
            methods.append({'metric': m, 'label': label, 'skipped': 'показатель отрицательный или нулевой'})
            continue
        lo, mid, hi = (base * c[k] - (net_debt if via_ev else 0) for k in ('p25', 'median', 'p75'))
        if hi <= 0:
            methods.append({'metric': m, 'label': label, 'skipped': 'долг больше оценки бизнеса'})
            continue
        methods.append({'metric': m, 'label': label, 'base_rub': base, 'scope': c['scope'], 'n': c['n'],
                        'multiple': (round(c['p25'], 2), round(c['median'], 2), round(c['p75'], 2)),
                        'full_rub': (max(lo, 0), mid, hi), 'deals': c['deals'][:8]})
    bench = benchmark_method(deal, report, net_debt)
    if bench:
        methods.insert(0, bench)
    used = [x for x in methods if 'full_rub' in x]
    if not used:
        return {'ok': False, 'reason': 'ни один способ не применим', 'methods': methods}
    mids = sorted(x['full_rub'][1] for x in used)
    lows = sorted(x['full_rub'][0] for x in used)
    highs = sorted(x['full_rub'][2] for x in used)
    full = (statistics.median(lows), statistics.median(mids), statistics.median(highs))
    # Насколько верить: способов два и больше, их середины сходятся в пределах
    # двух раз, и хоть один считан по своей отрасли — «средняя»; иначе «низкая».
    # «Высокой» у оценки по чужим сделкам не бывает.
    # Середина — по главному способу, если он есть: свои сделки служат
    # проверкой, а не голосом наравне (их слишком мало).
    if bench:
        full = bench['full_rub']
    agree = len(used) >= 2 and mids[-1] <= 2.5 * mids[0]
    own = bool(bench and bench['scope'] == 'отрасль') or any(x['scope'] == 'отрасль' for x in used)
    confidence = 'средняя' if agree and own else 'низкая'
    factors = []
    share_pct = stake_pct or 100
    if stake_pct and stake_pct < 50:
        factors.append(('доля без контроля (меньше 50%)', MINORITY_FACTOR))
    if foreign_exit:
        factors.append(('выход иностранного владельца: по правилам правкомиссии дисконт не меньше 60%', FOREIGN_EXIT_FACTOR))
    share = share_pct / 100.0
    lo_k = hi_k = 1.0
    for _, (a, b) in factors:
        lo_k *= a
        hi_k *= b
    deal_rub = (full[0] * share * lo_k, full[1] * share * (lo_k + hi_k) / 2, full[2] * share * hi_k)
    return {'ok': True, 'report_year': report['year'], 'net_debt_rub': net_debt, 'factors': [f[0] for f in factors],
            'full_rub': full, 'stake_pct': stake_pct, 'deal_rub': deal_rub,
            'methods': methods, 'confidence': confidence,
            'spread': round(full[2] / full[0], 1) if full[0] > 0 else None}


# --- Публичная компания: цена по бирже, а не по мультипликаторам ------------
# Если проданная компания торгуется на Мосбирже, ее стоимость на дату сделки
# известна точно: число акций × цена закрытия. Мультипликаторы чужих сделок
# дали «Самолету» 17 млрд ₽ — биржа в тот же день оценивала его в несколько
# раз дороже. Данные ISS Мосбиржи открыты и не требуют ключа.
ISS = 'https://iss.moex.com/iss'


def _iss(path: str, fetch) -> dict:
    import json as _json
    return _json.loads(fetch(ISS + path))


def listed_share(inn: str, fetch) -> dict | None:
    """Обыкновенная акция эмитента на основном режиме торгов (TQBR) по ИНН."""
    j = _iss('/securities.json?q=%s&iss.meta=off&securities.columns=secid,shortname,emitent_inn,is_traded,primary_boardid' % inn, fetch)
    found = [{'secid': secid, 'name': name} for secid, name, e_inn, traded, board in j['securities']['data']
             if str(e_inn) == str(inn) and board == 'TQBR' and traded]
    # Обыкновенная акция, а не привилегированная («BANEP» у «Башнефти»):
    # привилегированных обычно меньше, и капитализация по ним — часть компании.
    found.sort(key=lambda r: (r['secid'].endswith('P') and len(r['secid']) == 5, r['secid']))
    return found[0] if found else None


def market_value(secid: str, on_date: str, fetch) -> dict | None:
    """Капитализация на ближайший торговый день до даты сделки включительно."""
    from datetime import date, timedelta
    end = date.fromisoformat(on_date[:10])
    start = end - timedelta(days=10)
    hist = _iss('/history/engines/stock/markets/shares/boards/TQBR/securities/%s.json?from=%s&till=%s'
                '&iss.meta=off&history.columns=TRADEDATE,CLOSE' % (secid, start, end), fetch)['history']['data']
    hist = [h for h in hist if h[1]]
    if not hist:
        return None
    day, close = hist[-1]
    desc = _iss('/securities/%s.json?iss.meta=off&iss.only=description' % secid, fetch)['description']['data']
    size = next((float(row[2]) for row in desc if row[0] == "ISSUESIZE"), None)
    if not size:
        return None
    return {'secid': secid, 'date': day, 'close': close, 'shares': size, 'cap_rub': close * size}


def rub(v: float | None) -> str:
    if v is None:
        return '—'
    if abs(v) >= 1e9:
        return ('%.1f млрд ₽' % (v / 1e9)).replace('.', ',')
    return ('%.0f млн ₽' % (v / 1e6))
