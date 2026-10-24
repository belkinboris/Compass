# -*- coding: utf-8 -*-
"""Оценка цены сделки, когда она не раскрыта (прототип, 24 октября 2026).

Идея партнёра: там, где в карточке «Не раскрыта», — кнопка «Оценить с
ассистентом». Нажал — получил вилку цены, расчёт и все оговорки. Это НЕ факт
и в базу не пишется: оценка считается по запросу и подписана как оценка.

Кто что делает. Числа считает этот модуль — детерминированно, по
отчётности проданной компании и мультипликаторам сделок, где цена известна
(таблица `deal_multiples.compute_sector_table`, методика —
`docs/analytics_acceptance.md#мультипликаторы-по-отраслям-методика-таблицы-19-октября-2026`).
Ассистент только пересказывает результат по-человечески: модель не умеет
считать надёжно, а выдуманная цифра в карточке ударит по доверию ко всей
базе.

Когда кнопки нет (`eligibility`): проданное не опознано как юрлицо с ИНН;
нет отчётности за год до сделки; выручки нет; продано имущество, а не
компания; банк, страховщик, фонд, холдинг без операционной выручки;
финансирование, IPO, временное управление. Партнёр: «чтобы он совсем
какую-то бредятину не говорил, чтобы это было хотя бы сколько-то достоверно».
"""
from __future__ import annotations

import statistics
from typing import Any

METRICS = {
    # ключ: (поле отчётности-знаменатель, подпись, считается ли через EV)
    'ps': ('revenue_rub', 'цена к выручке', False),
    'ev_op': ('operating_profit_rub', 'стоимость бизнеса к прибыли от продаж', True),
    'pe': ('net_profit_rub', 'цена к чистой прибыли', False),
    'pbv': ('equity_rub', 'цена к собственному капиталу', False),
}
MIN_SAMPLE = 3              # меньше трёх сделок в отрасли — берём все отрасли
# Отрасли и коды ОКВЭД, где оценка по выручке и прибыли вводит в заблуждение.
NOT_BY_MULTIPLES_IND = {'Банки', 'Страхование', 'Рынок ценных бумаг', 'Финансовые услуги'}
NOT_BY_MULTIPLES_OKVED = ('64.', '65.', '66.')      # финансы, страхование, фонды и холдинги
# Государство забрало актив по суду или указу — цены нет по определению.
NO_PRICE_BY_NATURE = ('в доход государства', 'национализ', 'изъят', 'временное управление')
NOT_A_SALE_TYPES = {'Временное управление', 'Финансирование · структурная сделка', 'IPO',
                    'Реорганизация', 'Создание СП', 'Инвестиция'}
MIN_REVENUE_RUB = 30_000_000   # меньше — отчётность слишком мала, мультипликатор бессмыслен
# Цена к выручке — только по сделкам СВОЕЙ отрасли: маржа у отраслей разная в
# разы, и выручка туроператора, умноженная на медиану всех отраслей, дала
# «Библио-Глобусу» 375 млрд ₽ (прогон 24 октября 2026). Цена к капиталу — только
# там, где бизнес и есть его активы.
SECTOR_ONLY = {'ps'}
ASSET_HEAVY = {'Недвижимость', 'ГМК и добыча', 'Нефть и газ', 'Уголь', 'Энергетика',
               'Порты и инфраструктура', 'Гостиницы и туризм', 'Агро', 'Лесопром'}


def _n(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def report_before(reports: list[dict], deal_year: int | None) -> dict | None:
    """Отчёт за последний полный год ДО сделки (год сделки — нет: аудит
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
        return 'актив перешёл государству — цены у такой сделки нет'
    if deal.get('type') in NOT_A_SALE_TYPES:
        return 'это не продажа компании (%s)' % deal.get('type')
    if deal.get('ind') in NOT_BY_MULTIPLES_IND:
        return 'банки, страховщиков и фонды оценивают по капиталу и активам, а не по выручке'
    if not target_entity:
        return 'проданная компания не опознана как юрлицо с ИНН'
    if str(target_entity.get('okved') or '').startswith(NOT_BY_MULTIPLES_OKVED):
        return 'вид деятельности проданной компании — финансы или холдинг, оценка по выручке не годится'
    if not report:
        return 'нет отчётности проданной компании за год до сделки'
    if (_n(report.get('revenue_rub')) or 0) < MIN_REVENUE_RUB:
        return 'выручка проданной компании слишком мала или её нет — оценка по мультипликаторам бессмысленна'
    return None


def estimate(deal: dict, report: dict, comps: dict[str, dict], stake_pct: float | None) -> dict:
    """Вилка цены за 100% и за купленную долю по каждому применимому методу."""
    net_debt = (_n(report.get('borrowings_rub')) or 0) - (_n(report.get('cash_rub')) or 0)
    methods = []
    for m, (field, label, via_ev) in METRICS.items():
        base = _n(report.get(field))
        c = comps.get(m)
        if not c or base is None:
            continue
        if m in SECTOR_ONLY and c['scope'] != 'отрасль':
            methods.append({'metric': m, 'label': label,
                            'skipped': 'в отрасли меньше трёх сделок с известной ценой, а по чужим отраслям выручку сравнивать нельзя'})
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
    agree = len(used) >= 2 and mids[-1] <= 2 * mids[0]
    own = any(x['scope'] == 'отрасль' for x in used)
    confidence = 'средняя' if agree and own else 'низкая'
    share = (stake_pct or 100) / 100.0
    return {'ok': True, 'report_year': report['year'], 'net_debt_rub': net_debt,
            'full_rub': full, 'stake_pct': stake_pct, 'deal_rub': tuple(v * share for v in full),
            'methods': methods, 'confidence': confidence,
            'spread': round(full[2] / full[0], 1) if full[0] > 0 else None}


# --- Публичная компания: цена по бирже, а не по мультипликаторам ------------
# Если проданная компания торгуется на Мосбирже, её стоимость на дату сделки
# известна точно: число акций × цена закрытия. Мультипликаторы чужих сделок
# дали «Самолёту» 17 млрд ₽ — биржа в тот же день оценивала его в несколько
# раз дороже. Данные ISS Мосбиржи открыты и не требуют ключа.
ISS = 'https://iss.moex.com/iss'


def _iss(path: str, fetch) -> dict:
    import json as _json
    return _json.loads(fetch(ISS + path))


def listed_share(inn: str, fetch) -> dict | None:
    """Обыкновенная акция эмитента на основном режиме торгов (TQBR) по ИНН."""
    j = _iss('/securities.json?q=%s&iss.meta=off&securities.columns=secid,shortname,emitent_inn,is_traded,primary_boardid' % inn, fetch)
    for secid, name, e_inn, traded, board in j['securities']['data']:
        if str(e_inn) == str(inn) and board == 'TQBR' and traded:
            return {'secid': secid, 'name': name}
    return None


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
