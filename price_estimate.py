"""«Анализ Компаса»: сколько могла стоить сделка, цену которой не раскрыли.

Владелец 26 октября 2026: «если не раскрыта, пусть включается компас и
анализирует, сколько могла бы стоить эта доля, можно сравнить с другими в
этой отрасли». Оценки специалистов из открытых источников остаются в сумме
в скобках, как раньше (docs/card_money.md); этот модуль — отдельный расчет
Компаса рядом с ними, по нажатию кнопки на карточке.

Как устроено. ЧИСЛА считает этот модуль, а не модель: отчетность ФНС
покупаемой компании за последний год до сделки × медианный мультипликатор
отрасли из той же таблицы, что на странице «Аналитика»
(deal_multiples.compute_sector_table), × купленная доля. Модель только
объясняет готовую сводку словами; ответ, в котором есть число, которого нет
в сводке, отбрасывается, и показывается текст по шаблону (`template_text`).

Чистые функции без БД и сети — `build`, `template_text`, `numbers_ok`;
сбор отчета и вызов модели — в main.py (`/api/deals/{id}/price-estimate`).
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import deal_multiples as dm

# Внешние отраслевые мультипликаторы (партнер, 28 октября 2026: «не только по
# базе смотрим мультипликаторы, но и просто по интернету»; владелец утвердил
# источники по docs/price_estimate_sources.md: «давай делать»). Файл
# заполняется руками, у каждого числа — источник и год; «deals» и «exchange»
# входят в расчет, «global» — только ориентир в сводке.
EXTERNAL_PATH = pathlib.Path(__file__).resolve().parent / 'static' / 'data' / 'sector_multiples_external.json'
_external_cache: dict | None = None
EXT_KINDS_IN_RANGE = ('deals', 'exchange')
# метрика → (поле отчета, код строки, база словами, это EV (вычитать чистый долг))
EXT_BASE = {
    'ev_ebitda': ('operating_profit_rub', '2200', 'операционная прибыль', True),
    'ev_sales': ('revenue_rub', '2110', 'выручка', True),
    'pe': ('net_profit_rub', '2400', 'чистая прибыль', False),
    'pb': ('equity_rub', '1300', 'капитал', False),
}
EXT_LABEL = {'ev_ebitda': 'EV/EBITDA', 'ev_sales': 'EV/Sales', 'pe': 'P/E', 'pb': 'P/B'}


def external_multiples(path: pathlib.Path | None = None) -> dict:
    global _external_cache
    if path is not None:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    if _external_cache is None:
        _external_cache = json.loads(EXTERNAL_PATH.read_text(encoding='utf-8')) if EXTERNAL_PATH.exists() else {}
    return _external_cache


def external_methods(ind: str | None, report: dict | None, net_debt: float | None, stake: float | None,
                     data: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Методы по внешним мультипликаторам отрасли и мировые ориентиры.
    Сделочные (deals) и биржевые (exchange) — в методы и в диапазон; мировые
    (global) — отдельным списком, в диапазон не входят. Без отчетности или без
    записей по отрасли — пусто (пустое честнее подбора соседнего сектора)."""
    data = external_multiples() if data is None else data
    recs = (data.get('industries') or {}).get(ind or '') or []
    sources = data.get('sources') or {}
    methods, benchmarks = [], []
    for rec in recs:
        src = sources.get(rec.get('source')) or {}
        kind = src.get('kind')
        ext = {'source': src.get('short') or rec.get('source'), 'name': src.get('name'), 'url': src.get('url'),
               'kind': kind, 'label': rec.get('label'), 'year': rec.get('year'), 'note': rec.get('note')}
        if kind == 'global':
            benchmarks.append({'metric': rec['metric'], 'label': EXT_LABEL.get(rec['metric'], rec['metric']),
                               'value': float(rec['value']), **ext})
            continue
        if kind not in EXT_KINDS_IN_RANGE or not report:
            continue
        key, code, base_name, is_ev = EXT_BASE.get(rec['metric'], (None, None, None, False))
        if not key:
            continue
        base = _pick(report, key, code)
        if rec['metric'] == 'ev_ebitda':
            import company_finance as cf
            base, _ = cf.operating_profit_estimate(report.get('operating_profit_rub'), report.get('lines') or {})
        if base is None or base <= 0:
            continue
        full = base * float(rec['value'])
        if is_ev and net_debt is not None:
            full -= net_debt
        if full <= 0:
            continue
        methods.append({
            'metric': rec['metric'], 'label': EXT_LABEL.get(rec['metric'], rec['metric']),
            'base_name': base_name, 'base_rub': base, 'report_year': report['year'],
            'median': float(rec['value']), 'q1': None, 'q3': None, 'count': None,
            'scope': 'внешний', 'industry': ind, 'external': ext,
            'full_rub': full, 'stake_rub': full * stake / 100 if stake else None,
        })
    return methods, benchmarks

# Сумма «известна» — анализ не нужен: цену назвали стороны или ее пересчитали из валюты.
KNOWN_MEANINGS = ('disclosed', 'foreign_currency')

# Мультипликатор → строка отчета, подпись и как назвать базу словами.
METHODS = (
    ('ps', 'revenue_rub', '2110', 'P/S', 'выручка'),
    ('pe', 'net_profit_rub', '2400', 'P/E', 'чистая прибыль'),
    ('ev_op', 'operating_profit_rub', '2200', 'EV / операционная прибыль', 'операционная прибыль'),
)
COMPARABLES_MAX = 5
# Похожая сделка в 6 раз крупнее или мельче — уже не похожая: 5Yes! (выручка
# 521 млн ₽) сравнивали с Росспиртпромом за 8,3 млрд ₽ (владелец, 27 октября
# 2026: «они вообще несопоставимы»).
SIZE_RATIO_MAX = 6.0
_CARD_REVENUE = re.compile(r'выручк\w*[^.;]{0,80}?(\d+(?:[.,]\d+)?)\s*(млрд|млн)\s*(?:₽|руб)', re.I)


def revenue_from_card(deal: dict) -> float | None:
    """Выручка покупаемой компании из текста карточки (eco.target_fin, eco.fin),
    когда отчетности ФНС в базе нет: «выручка за 2025 год — 521 млн ₽»."""
    eco = deal.get('eco') or {}
    for text in (eco.get('target_fin'), eco.get('fin')):
        m = _CARD_REVENUE.search(str(text or ''))
        if m:
            return float(m.group(1).replace(',', '.')) * (1e9 if m.group(2).lower() == 'млрд' else 1e6)
    return None


def needs_estimate(deal: dict) -> bool:
    """Анализ показывается, когда цену не назвали стороны. Торги — нет: у лота
    есть стартовая цена, и смысл у нее другой."""
    price = (deal.get('facts') or {}).get('price') or {}
    if price.get('meaning') in KNOWN_MEANINGS or price.get('meaning') == 'auction_start':
        return False
    return 'торг' not in str(deal.get('type') or '').lower()


def _q(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _cell_values(table: dict, cell: dict, metric: str) -> list[float]:
    ids = set(cell.get('ids') or [])
    out = []
    for r in table.get('rows') or []:
        if r['id'] in ids:
            v = (r.get('metrics') or {}).get(metric) or {}
            if v.get('status') == 'ok' and v.get('value') is not None:
                out.append(float(v['value']))
    return out


def _pick(report: dict, key: str, code: str) -> float | None:
    v = report.get(key)
    if v is None:
        v = (report.get('lines') or {}).get(code)
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def money(rub: float | None) -> str:
    """1 234 567 890 → «1,2 млрд ₽»; две значащие цифры — точнее оценка не бывает."""
    if rub is None:
        return '—'
    a = abs(rub)
    for div, unit in ((1e12, 'трлн'), (1e9, 'млрд'), (1e6, 'млн'), (1e3, 'тыс.')):
        if a >= div:
            v = rub / div
            digits = 0 if abs(v) >= 10 else 1
            s = f'{v:.{digits}f}'.replace('.', ',')
            if s.endswith(',0'):
                s = s[:-2]
            return f'{s} {unit} ₽'
    return f'{rub:.0f} ₽'


def _round2(x: float) -> float:
    if x <= 0:
        return x
    import math
    p = 10 ** (math.floor(math.log10(x)) - 1)
    return round(x / p) * p


def build(deal: dict, report: dict | None, table: dict, deals: dict[str, dict],
          industry: str | None, company_name: str | None = None, external: dict | None = None) -> dict[str, Any]:
    """Сводка для карточки: методы с числами, похожие сделки, оценки из
    источников, итоговый диапазон. Ничего не придумывает: нет данных — пусто."""
    year = dm.multiple_year(deal)[0]
    stake = dm.stake_established(deal)
    ind = industry if industry and industry != 'Не определена' else None

    methods = []
    report_note = None
    net_debt = None
    if report and report.get('assets_rub') is not None:
        net_debt = (_pick(report, 'borrowings_rub', '1410') or 0.0) - (_pick(report, 'cash_rub', '1250') or 0.0)
    if report and report.get('year') and year:
        gap = year - int(report['year'])
        if gap < dm.MIN_YEAR_GAP or gap > dm.MAX_YEAR_GAP + 1:
            report_note = f'последний отчет — за {report["year"]} год, далеко от года сделки'
        for metric, key, code, label, base_name in METHODS:
            base = _pick(report, key, code)
            if metric == 'ev_op':
                import company_finance as cf
                base, _ = cf.operating_profit_estimate(report.get('operating_profit_rub'), report.get('lines') or {})
            if base is None or base <= 0:
                continue
            scope = 'отрасль'
            cell = dm.find_cell(table, metric, ind, None) if ind else None
            if not cell or cell.get('median') is None:
                cell, scope = dm.find_cell(table, metric, None, None), 'все отрасли'
            if not cell or cell.get('median') is None:
                continue
            vals = _cell_values(table, cell, metric)
            med = float(cell['median'])
            full = base * med
            if metric == 'ev_op' and net_debt is not None:
                full -= net_debt
            if full <= 0:
                continue
            q1, q3 = _q(vals, 0.25), _q(vals, 0.75)
            methods.append({
                'metric': metric, 'label': label, 'base_name': base_name, 'base_rub': base,
                'report_year': report['year'], 'median': med, 'q1': q1, 'q3': q3,
                'count': cell.get('count'), 'scope': scope, 'industry': ind if scope == 'отрасль' else None,
                'full_rub': full, 'stake_rub': full * stake / 100 if stake else None,
            })

    # Внешние мультипликаторы отрасли — после методов по базе, в тот же диапазон.
    ext_methods, benchmarks = external_methods(ind, report if report and report.get('year') else None,
                                               net_debt, stake, external)
    methods.extend(ext_methods)

    # Отчетности нет, но карточка называет выручку: метод P/S считается по ней,
    # с оговоркой — это цифра из источника, а не из реестра.
    card_revenue = None
    if not methods and not (report and report.get('year')):
        card_revenue = revenue_from_card(deal)
        cell, scope = (dm.find_cell(table, 'ps', ind, None) if ind else None), 'отрасль'
        if not cell or cell.get('median') is None:
            cell, scope = dm.find_cell(table, 'ps', None, None), 'все отрасли'
        if card_revenue and cell and cell.get('median') is not None:
            vals = _cell_values(table, cell, 'ps')
            med = float(cell['median'])
            methods.append({
                'metric': 'ps', 'label': 'P/S', 'base_name': 'выручка по данным источника', 'base_rub': card_revenue,
                'report_year': None, 'median': med, 'q1': _q(vals, 0.25), 'q3': _q(vals, 0.75),
                'count': cell.get('count'), 'scope': scope, 'industry': ind if scope == 'отрасль' else None,
                'full_rub': card_revenue * med, 'stake_rub': card_revenue * med * stake / 100 if stake else None,
            })

    # Похожие сделки: та же отрасль, цена названа сторонами, ближе по году.
    comps = []
    rows_by_id = {r['id']: r for r in table.get('rows') or []}
    for cid, d in deals.items():
        if cid == deal.get('id') or not ind or (d.get('ind') or '') != ind:
            continue
        price = (d.get('facts') or {}).get('price') or {}
        nature = (d.get('facts') or {}).get('nature') or {}
        if price.get('meaning') not in KNOWN_MEANINGS or not price.get('value_rub'):
            continue
        # Покупки, а не раунды, IPO, торги и финансирование: цена у них про другое.
        if d.get('type') != 'M&A' or any(nature.get(k) for k in ('cash_in', 'financing', 'auction', 'reorganization', 'own_shares')):
            continue
        # Оферта миноритариям и выкуп своих акций — не покупка бизнеса.
        if re.search(r'тендерн|оферт|миноритари|обратн\w* выкуп|байбэк', str(d.get('title') or ''), re.I):
            continue
        y = dm.year_of(d)
        if not y or (year and abs(y - year) > 3):
            continue
        r = rows_by_id.get(cid) or {}
        mult = {m: ((r.get('metrics') or {}).get(m) or {}).get('value') for m in ('ps', 'pe')
                if ((r.get('metrics') or {}).get(m) or {}).get('status') == 'ok'}
        comps.append({'id': cid, 'title': d.get('title') or cid, 'year': y,
                      'price_rub': float(price['value_rub']), 'stake': dm.stake_established(d),
                      'multiples': mult})
    # Ближе по размеру важнее, чем ближе по году: клинику за 77 млн ₽ не с чем
    # сравнивать в сети за 18 млрд ₽. Размер — выручка компании, если она есть.
    import math
    size = (_pick(report, 'revenue_rub', '2110') if report else None) or card_revenue
    for c in comps:
        full = c['price_rub'] * 100 / c['stake'] if c['stake'] else c['price_rub']
        ps = c['multiples'].get('ps')
        their_size = full / ps if ps else full / 1.81
        c['_dist'] = abs(math.log(max(their_size, 1) / size)) if size and size > 0 else 0
    comps.sort(key=lambda c: (round(c['_dist']), -len(c['multiples']), abs((c['year'] or 0) - (year or 0))))
    # Размер известен — сделки другого масштаба в сравнение не идут. Размер
    # неизвестен — похожих сделок НЕТ ВОВСЕ (владелец, 29 октября 2026, Velle
    # рядом с Росспиртпромом за 8,3 млрд ₽: «это как если будет продаваться
    # нефтебаза с двумя заправками и сравнят со сделкой с Роснефтью — смешно
    # и глупо для разбирающихся людей»). До этого они показывались с
    # оговоркой «могут быть несопоставимы» — оговорка не спасала.
    size_unknown = not (size and size > 0)
    hidden_for_size = 0
    if size_unknown:
        hidden_for_size, comps = len(comps), []
    else:
        comps = [c for c in comps if c['_dist'] <= math.log(SIZE_RATIO_MAX)]
    comps = [{k: v for k, v in c.items() if k != '_dist'} for c in comps[:COMPARABLES_MAX]]

    experts = None
    val = str((deal.get('eco') or {}).get('val') or '').strip()
    if re.search(r'\d', val) and val not in ('—', '-'):
        experts = val[:900]
    sum_text = str(deal.get('sum') or '')
    if 'оценк' in sum_text.lower():
        experts = (sum_text + ('. ' + experts if experts else ''))[:900]

    rng = None
    centrals = [m['stake_rub'] if stake else m['full_rub'] for m in methods]
    if len(centrals) >= 2:
        rng = (min(centrals), max(centrals))
    elif len(centrals) == 1:
        m = methods[0]
        k = (stake / 100) if stake else 1.0
        lo = m['base_rub'] * (m['q1'] or m['median']) * k
        hi = m['base_rub'] * (m['q3'] or m['median']) * k
        rng = (min(lo, hi), max(lo, hi)) if hi > 0 else None
    if rng:
        rng = (_round2(rng[0]), _round2(rng[1]))

    return {
        'deal_id': deal.get('id'), 'title': deal.get('title'), 'year': year,
        'company': company_name, 'industry': ind, 'stake': stake,
        'report_year': (report or {}).get('year'), 'report_note': report_note,
        'revenue_rub': _pick(report, 'revenue_rub', '2110') if report else None,
        'net_profit_rub': _pick(report, 'net_profit_rub', '2400') if report else None,
        'methods': methods, 'benchmarks': benchmarks, 'comparables': comps, 'experts': experts,
        'card_revenue_rub': card_revenue, 'size_unknown': size_unknown, 'hidden_for_size': hidden_for_size,
        'range': rng, 'range_text': range_text(rng, stake),
    }


def can_estimate(s: dict) -> bool:
    """Есть чем считать: хотя бы один метод, похожая сделка по размеру или
    оценка из источников. Иначе кнопки «Посчитать» на карточке нет вовсе
    (владелец, 29 октября 2026: «где мы знаем, что оценку дать нельзя —
    вообще не будем даже кнопку добавлять»)."""
    return bool(s.get('methods') or s.get('comparables') or s.get('experts'))


def range_text(rng, stake) -> str | None:
    if not rng:
        return None
    lo, hi = money(rng[0]), money(rng[1])
    core = lo if lo == hi else _join_range(rng)
    what = f'за {_pct(stake)}' if stake and stake < 99.5 else 'за 100%'
    return f'≈ {core} {what}'


def _join_range(rng) -> str:
    a, b = money(rng[0]), money(rng[1])
    ua, ub = a.rsplit(' ', 2)[-2:], b.rsplit(' ', 2)[-2:]
    if ua == ub:  # «1,2–1,8 млрд ₽»
        return a.rsplit(' ', 2)[0] + '–' + b
    return f'{a} – {b}'


def deals_word(n: int | None) -> str:
    n = int(n or 0)
    word = 'сделка' if n % 10 == 1 and n % 100 != 11 else (
        'сделки' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'сделок')
    return f'{n} {word}'


def _pct(p: float | None) -> str:
    if p is None:
        return ''
    s = f'{p:.2f}'.rstrip('0').rstrip('.').replace('.', ',')
    return s + '%'


def facts_text(s: dict) -> str:
    """Сводка для модели — та же, по которой проверяются числа ответа."""
    lines = [f'Сделка: {s["title"]}', f'Год сделки: {s["year"] or "не установлен"}']
    if s['company']:
        lines.append(f'Покупаемая компания по реестру ФНС: {s["company"]}')
    lines.append(f'Отрасль: {s["industry"] or "не определена"}')
    lines.append(f'Купленная доля: {_pct(s["stake"]) if s["stake"] else "не установлена — оценка за 100% компании"}')
    if s['report_year']:
        np_ = s["net_profit_rub"]
        profit = ('чистая прибыль ' + money(np_)) if np_ is None or np_ >= 0 else ('чистый убыток ' + money(-np_))
        lines.append(f'Отчетность ФНС за {s["report_year"]} год: выручка {money(s["revenue_rub"])}, {profit}')
        if s['report_note']:
            lines.append(f'Оговорка: {s["report_note"]}')
    elif s.get('card_revenue_rub'):
        lines.append(f'Отчетности покупаемой компании в базе нет; по данным источника ее выручка — {money(s["card_revenue_rub"])}')
    else:
        lines.append('Отчетности покупаемой компании в базе нет')
    if s.get('hidden_for_size'):
        lines.append('Размер покупаемой компании неизвестен (ни выручки, ни активов) — сделки отрасли с известной '
                     'ценой есть, но их не приводить вовсе: сравнение без масштаба вводит в заблуждение; так и сказать')
    for m in s['methods']:
        if m.get('external'):
            e = m['external']
            what = 'цены сделок' if e['kind'] == 'deals' else 'биржа'
            lines.append(
                f'Метод {m["label"]} по данным {e["source"]} ({what}, сектор «{e["label"]}», {e["year"]} год): '
                f'{m["base_name"]} {money(m["base_rub"])} × {str(m["median"]).replace(".", ",")}× = {money(m["full_rub"])} за 100%'
                + (f', за долю {_pct(s["stake"])} — {money(m["stake_rub"])}' if m['stake_rub'] else ''))
            continue
        where = f'отрасль «{m["industry"]}»' if m['industry'] else 'все отрасли (в отрасли мало сделок)'
        lines.append(
            f'Метод {m["label"]} по базе Компаса: {m["base_name"]} {money(m["base_rub"])} × медиана {str(m["median"]).replace(".", ",")}× '
            f'({where}, {deals_word(m["count"])}) = {money(m["full_rub"])} за 100%'
            + (f', за долю {_pct(s["stake"])} — {money(m["stake_rub"])}' if m['stake_rub'] else ''))
    if any(m.get('external') and m['metric'] == 'ev_ebitda' for m in s['methods']):
        lines.append('Оговорка: EBITDA в отчетности ФНС нет, мультипликатор EV/EBITDA применен к операционной прибыли '
                     '(без амортизации), поэтому такая оценка скорее занижена')
    for b in s.get('benchmarks') or []:
        lines.append(f'Мировой ориентир, {b["source"]}, сектор «{b["label"]}», {b["year"]} год: {EXT_LABEL.get(b["metric"], b["metric"])} '
                     f'{str(b["value"]).replace(".", ",")}× — уровни там в 2–3 раза выше российских, это верхняя граница, в диапазон не входит')
    if s['range_text']:
        lines.append(f'Итоговый диапазон Компаса: {s["range_text"]}')
    for c in s['comparables']:
        mult = ', '.join(f'{k.upper().replace("PS", "P/S").replace("PE", "P/E")} {str(round(v, 1)).replace(".", ",")}×'
                         for k, v in c['multiples'].items())
        lines.append(f'Похожая сделка {c["year"]}: {c["title"]} — {money(c["price_rub"])}'
                     + (f' за {_pct(c["stake"])}' if c['stake'] else '') + (f'; {mult}' if mult else ''))
    if s['experts']:
        lines.append(f'Оценки из открытых источников: {s["experts"]}')
    return '\n'.join(lines)


def template_text(s: dict) -> list[str]:
    """Объяснение без модели: модель недоступна или назвала лишнее число."""
    out = []
    if s['range_text']:
        out.append(f'По расчету Компаса сделка могла стоить {s["range_text"].replace("≈ ", "около ")}. '
                   'Это прикидка по отчетности и мультипликаторам похожих сделок, а не цена договора.')
    elif s['comparables'] or s['experts']:
        out.append('Посчитать цену по отчетности не получилось: '
                   + ('нет отчетности покупаемой компании за год до сделки.' if not s['report_year']
                      else 'у компании убыток или в отрасли мало сделок с известной ценой.')
                   + ' Ниже — с чем можно сравнить.')
    if s['methods']:
        names = ', '.join(dict.fromkeys(m['label'] for m in s['methods']))
        if s['methods'][0]['report_year']:
            ext_names = sorted({m['external']['source'] for m in s['methods'] if m.get('external')})
            own = any(not m.get('external') for m in s['methods'])
            parts = (['медианы по сделкам с известной ценой из базы Компаса'] if own else []) \
                + ([f'отраслевые ориентиры из открытых исследований ({", ".join(ext_names)})'] if ext_names else [])
            out.append(f'Взяли отчетность компании за {s["methods"][0]["report_year"]} год и мультипликаторы '
                       f'({names}): {" и ".join(parts)}. Разные методы дают разный результат — '
                       'отсюда ширина диапазона; ниже видно, что дает каждый.')
        else:
            out.append(f'Отчетности компании в базе нет, взяли выручку по данным источника и медианный '
                       f'мультипликатор {names} по сделкам отрасли с известной ценой.')
    if s.get('hidden_for_size') and not s['range_text']:
        out.append('Размер покупаемой компании неизвестен: ни выручки, ни активов в открытых данных нет. '
                   'Сделки отрасли с известной ценой есть, но без масштаба их не приводим — сравнение было бы не по делу.')
    if not out:
        out.append('Исходя из публичных данных, достоверно определить сумму сделки невозможно.')
    return out


_NUM = re.compile(r'\d+(?:[.,]\d+)?')


def _norm(n: str) -> str:
    n = n.replace('.', ',')
    return n[:-2] if n.endswith(',0') else n


def numbers_ok(answer: str, facts: str) -> bool:
    """Каждое число ответа есть в сводке. Мелкие порядковые (1–10) и годы
    пропускаются, если за ними нет денег, процентов или «раз»."""
    allowed = {_norm(x) for x in _NUM.findall(facts.replace('\u00a0', ' ').replace('\u202f', ' '))}
    text = answer.replace('\u00a0', ' ').replace('\u202f', ' ')
    for m in _NUM.finditer(text):
        n = _norm(m.group(0))
        if n in allowed:
            continue
        # «три метода» и «в 2025 году» сводке не противоречат, а «9 млрд ₽»,
        # «7%» и «в 3 раза» — уже величина, ее в сводке быть обязано.
        if n.isdigit() and not _UNIT.match(text, m.end()) and (int(n) <= 10 or 2015 <= int(n) <= 2030):
            continue
        return False
    return True


_UNIT = re.compile(r'\s*(?:трлн|млрд|млн|тыс|₽|руб|\$|€|%|×|x\b|раз)', re.I)


# Число словами («трехсот миллионов», «полтора миллиарда») проверку цифр
# обходит: на боевом сайте 26 октября 2026 модель так написала «полтора с
# половиной миллиарда» вместо 1,6 млрд. Такое предложение выбрасывается.
_SPELLED_BIG = re.compile(r'(?<!\d)(?<!\d[\s\u00a0\u202f])\b(?:миллион|миллиард|тысяч|млрд|млн|трлн)\w*|\bполтор\w*|\bполутор\w*', re.I)
_SENT = re.compile(r'(?<=[.!?])\s+(?=[А-ЯЁA-Z«(])')


def clean_answer(text: str, facts: str, min_paragraphs: int = 2) -> list[str] | None:
    """Абзацы ответа без предложений с числом не из сводки и с числами словами.
    Вычищено так много, что абзацев меньше `min_paragraphs`, — None."""
    out = []
    for para in [p.strip() for p in re.split(r'\n\s*\n', text or '') if p.strip()]:
        parts = _SENT.split(para)
        kept = [x for x in parts if numbers_ok(x, facts) and not _SPELLED_BIG.search(x)]
        # Выпало все, кроме заголовка абзаца («Для продавца.»), — абзаца нет.
        if len(kept) < len(parts) and all(len(x.split()) <= 4 and not re.search(r'\d', x) for x in kept):
            continue
        joined = ' '.join(kept).strip()
        if joined and len(re.sub(r'[^а-яa-z]', '', joined.lower())) > 6:
            out.append(joined)
    return out if len(out) >= min_paragraphs else None


SYSTEM = (
    'Ты — аналитик сервиса «Компас» о сделках M&A в России. Цену этой сделки стороны не раскрыли. '
    'Объясни читателю, сколько она могла стоить и почему, — только по сводке ниже. '
    'Правила: никаких чисел, которых нет в сводке; не пересчитывай и не придумывай мультипликаторы; '
    'итоговый диапазон бери ровно из сводки. Пиши по-русски, просто и по-деловому, как аналитик '
    'объяснял бы партнеру вслух: без заголовков, списков, markdown и вводных слов. Все числа — цифрами и ровно в том виде, как в сводке (1,6 млрд ₽, а не «полтора миллиарда»); не досчитывай доли и проценты сам. '
    'Три-четыре коротких абзаца, разделенных пустой строкой: 1) итоговая оценка и что она за долю; '
    '2) из чего она получилась — отчетность и мультипликаторы: по базе Компаса и по открытым исследованиям, '
    'источник называй так, как он назван в сводке; мировой ориентир, если он есть, упомяни одной фразой как верхнюю границу; 3) с чем сравнить — назови одну-две похожие сделки с ценой без выводов «выше» или «ниже» диапазона, '
    'и оценки специалистов, если они есть, и сходятся ли они с расчетом; 4) одна фраза — чего расчет не '
    'учитывает (долг, премия за контроль, особые условия сделки). Если диапазона нет — объясни, '
    'каких данных не хватает, и что можно сказать по похожим сделкам. Не давай инвестиционных советов.'
)
