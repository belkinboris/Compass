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
    'ev_ebit': ('operating_profit_rub', '2200', 'операционная прибыль', True),
    'ev_sales': ('revenue_rub', '2110', 'выручка', True),
    'pe': ('net_profit_rub', '2400', 'чистая прибыль', False),
    'pb': ('equity_rub', '1300', 'капитал', False),
}
EXT_LABEL = {'ev_ebitda': 'EV/EBITDA', 'ev_ebit': 'EV/EBIT', 'ev_sales': 'EV/Sales', 'pe': 'P/E', 'pb': 'P/B'}
# У мирового ориентира (global) EV/EBITDA к нашей базе не прикладывается: EBITDA
# в отчетности ФНС нет (владелец, 29 октября 2026). К операционной прибыли —
# его EV/EBIT, к выручке — EV/Sales, к капиталу — P/B, к прибыли — P/E.
GLOBAL_METRICS = ('ev_ebit', 'ev_sales', 'pb', 'pe')


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
    (global) — в `benchmarks` (список ориентиров) и, если их можно приложить к
    отчетности по совпадающей базе (`GLOBAL_METRICS`), — в третий список
    `global_methods`: `build` берет их, только когда российских методов нет
    (владелец, 29 октября 2026). Без отчетности или без записей по отрасли —
    пусто (пустое честнее подбора соседнего сектора).

    Возвращает (methods, benchmarks, global_methods); старые вызовы с двумя
    значениями — через `external_methods(...)[:2]`."""
    data = external_multiples() if data is None else data
    recs = (data.get('industries') or {}).get(ind or '') or []
    sources = data.get('sources') or {}
    methods, benchmarks, global_methods = [], [], []
    for rec in recs:
        src = sources.get(rec.get('source')) or {}
        kind = src.get('kind')
        ext = {'source': src.get('short') or rec.get('source'), 'name': src.get('name'), 'url': src.get('url'),
               'kind': kind, 'label': rec.get('label'), 'year': rec.get('year'), 'note': rec.get('note')}
        if kind == 'global':
            benchmarks.append({'metric': rec['metric'], 'label': EXT_LABEL.get(rec['metric'], rec['metric']),
                               'value': float(rec['value']), **ext})
            if rec['metric'] not in GLOBAL_METRICS or not report:
                continue
        elif kind not in EXT_KINDS_IN_RANGE or not report:
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
        (global_methods if kind == 'global' else methods).append({
            'metric': rec['metric'], 'label': EXT_LABEL.get(rec['metric'], rec['metric']),
            'base_name': base_name, 'base_rub': base, 'report_year': report['year'],
            'median': float(rec['value']), 'q1': None, 'q3': None, 'count': None,
            'scope': 'внешний', 'industry': ind, 'external': ext,
            'full_rub': full, 'stake_rub': full * stake / 100 if stake else None,
        })
    return methods, benchmarks, global_methods

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
_CARD_REVENUE = re.compile(r'выручк\w*[^.;]{0,120}?(\d+(?:[.,]\d+)?)\s*(млрд|млн)\s*(?:₽|руб)', re.I)
# Предложение о выручке ПОКУПАТЕЛЯ — не размер покупаемой компании: у «Гранд
# Премьер» (gd66af0f7) «рост выручки… до 8,48 млрд ₽… относится к покупателю
# Nelt» читался как выручка цели и уводил расчет в 20 раз вверх (6 ноября 2026).
_CARD_REVENUE_NOT_TARGET = re.compile(r'покупател', re.I)


def revenue_from_card(deal: dict) -> float | None:
    """Выручка покупаемой компании из текста карточки (eco.target_fin, eco.fin):
    «выручка за 2025 год — 521 млн ₽». Нужна, когда отчетности ФНС в базе нет
    или она не той компании (`report_mismatch`)."""
    eco = deal.get('eco') or {}
    for text in (eco.get('target_fin'), eco.get('fin')):
        for sent in _SENTENCE.split(str(text or '')):
            if _CARD_REVENUE_NOT_TARGET.search(sent):
                continue
            m = _CARD_REVENUE.search(sent)
            if m:
                return float(m.group(1).replace(',', '.')) * (1e9 if m.group(2).lower() == 'млрд' else 1e6)
    return None


# ОЦЕНКА ИЗ ИСТОЧНИКОВ — ВТОРАЯ ОПОРА (владелец, 6 ноября 2026, «Медскан»: «по
# оценке написано где-то 30 миллиардов, а если нажать "рассчитать", там чуть ли
# не 1 млрд… ориентируйся на оценочное число тоже»). Число берется из суммы
# карточки «X (по оценке)», иначе из первого предложения `eco.val`, где кто-то
# что-то ОЦЕНИВАЕТ в рублях. Предложения про ущерб, долг, кадастр, иск,
# капитализацию, активы и стартовую цену — не оценка цены бизнеса: пропускаются
# (пустое честнее чужого числа).
_SRC_VERB = re.compile(r'(?<!пере)оцени|(?<!пере)оценк|могл\w* стоить', re.I)
_SRC_NOT_PRICE = re.compile(
    r'ущерб|долг|задолженн|кадастр|начальн|стартов|капитализац|\bиск|исков|\bсуд(?!я)|прокурат|изъят|актив'
    r'|запас|вложени|привлеч|инвестиц|за\s+акци|акци\w*\s+по\b', re.I)
_SENTENCE = re.compile(r'(?<=[.!?])\s+')
# Расхождение «в разы» (владелец, 6 ноября 2026: «больше чем в 3 раза») —
# показывается явно, рядом с итогом и с вероятной причиной.
DIVERGENCE_MAX = 3.0
# «На порядок»: выручка юрлица в 10 раз меньше, чем следует из карточки или
# из оценки источников, — отчетность не той компании (одно юрлицо группы,
# холдинг без консолидации). Методы по ней в итог не входят.
SCALE_MISMATCH = 10.0
# ОКВЭД «Деятельность холдинговых компаний»: собственная отчетность такого
# юрлица (РСБУ, без консолидации) не включает выручку дочерних обществ —
# АО «Медскан» с выручкой 341 млн ₽ при выручке группы 28 млрд ₽.
HOLDING_OKVED = ('64.20',)


def source_value(deal: dict) -> dict | None:
    """Оценка из открытых источников числом: {'lo', 'hi', 'text', 'origin'}
    или None. За долю она или за всю компанию — из текста не видно, поэтому
    сравнение с расчетом идет по обеим базам (`_distance`)."""
    s = str(deal.get('sum') or '')
    if 'оценк' in s.lower():
        rng = dm.parse_rub_range(s)
        if rng:
            return {'lo': rng[0], 'hi': rng[1], 'text': _join_range(rng) if rng[0] != rng[1] else money(rng[0]),
                    'origin': 'sum'}
    val = str((deal.get('eco') or {}).get('val') or '')
    for sent in _SENTENCE.split(val):
        if not _SRC_VERB.search(sent) or _SRC_NOT_PRICE.search(sent):
            continue
        rng = dm.parse_rub_range(sent)
        if rng:
            return {'lo': rng[0], 'hi': rng[1], 'text': _join_range(rng) if rng[0] != rng[1] else money(rng[0]),
                    'origin': 'val'}
    return None


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Во сколько раз расходятся два диапазона: 1 — пересекаются, иначе
    отношение ближних концов."""
    if a[0] <= 0 or b[0] <= 0:
        return 1.0
    return max(a[0] / b[1], b[0] / a[1], 1.0)


def times(n: float) -> str:
    """30 → «в 30 раз», 3 → «в 3 раза», 21 → «в 21 раз»."""
    k = int(round(n))
    word = 'раза' if 2 <= k % 10 <= 4 and not 12 <= k % 100 <= 14 else 'раз'
    return f'в {k} {word}'


def report_mismatch(report: dict | None, card_revenue: float | None, src: dict | None,
                    table: dict, ind: str | None) -> dict | None:
    """Отчетность ФНС — не той компании, о которой сделка (владелец, 6 ноября
    2026, «Медскан»). Три признака, любой достаточен:
    - юрлицо по реестру — холдинговая компания (ОКВЭД 64.20): ее РСБУ не
      включает выручку дочерних обществ;
    - выручка из карточки (`card_revenue`) в `SCALE_MISMATCH` раз и больше
      выручки юрлица;
    - оценка источников, деленная на верхний квартиль P/S базы, в
      `SCALE_MISMATCH` раз и больше выручки юрлица: бизнес такой цены с такой
      выручкой не бывает даже по самым дорогим сделкам базы.
    Возвращает {'signals': [...], 'text': объяснение словами} или None."""
    if not report or not report.get('year'):
        return None
    rev = _pick(report, 'revenue_rub', '2110')
    signals, parts = [], []
    if str(report.get('okved_code') or '') in HOLDING_OKVED:
        signals.append('holding')
        parts.append('по реестру это холдинговая компания, и в ее собственную отчетность не входит выручка '
                     'дочерних компаний')
    if rev and rev > 0 and card_revenue and card_revenue >= SCALE_MISMATCH * rev:
        signals.append('card_revenue')
        parts.append(f'выручка по ее отчетности — {money(rev)}, а выручка бизнеса по данным источника — '
                     f'{money(card_revenue)}, {times(card_revenue / rev)} больше')
    if rev and rev > 0 and src and 'card_revenue' not in signals:
        cell = (dm.find_cell(table, 'ps', ind, None) if ind else None) or dm.find_cell(table, 'ps', None, None)
        q3 = _q(_cell_values(table, cell, 'ps'), 0.75) if cell else None
        if q3 and q3 > 0 and src['lo'] / q3 >= SCALE_MISMATCH * rev:
            signals.append('source_scale')
            parts.append(f'выручка по ее отчетности — {money(rev)}, а оценка источников ({src["text"]}) '
                         'предполагает бизнес как минимум на порядок крупнее')
    if not signals:
        return None
    return {'signals': signals,
            'text': 'Отчетность ФНС, судя по всему, — только одной компании, а не всего бизнеса: ' + '; '.join(parts)}


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
    ext_methods, benchmarks, global_methods = external_methods(
        ind, report if report and report.get('year') else None, net_debt, stake, external)
    methods.extend(ext_methods)

    # ОТЧЕТНОСТЬ НЕ ТОЙ КОМПАНИИ (владелец, 6 ноября 2026, «Медскан»: P/S по
    # выручке холдингового АО 341 млн ₽ дал «до 1,1 млрд ₽» при оценке
    # источников 31–36 млрд ₽ и выручке группы 28 млрд ₽). Методы по такой
    # отчетности остаются в сводке с пометкой, но в итог не входят; мировой
    # ориентир по ней же — не показывается.
    card_revenue = revenue_from_card(deal)
    src = source_value(deal)
    mismatch = report_mismatch(report, card_revenue, src, table, ind)
    if mismatch:
        for m in methods:
            m['unreliable'] = 'report_scale'
        global_methods = []

    # Отчетности нет (или она не той компании), но карточка называет выручку:
    # метод P/S считается по ней, с оговоркой — это цифра из источника, а не из
    # реестра.
    # Отчетность не той компании заменяется выручкой карточки, только если та
    # описывает бизнес крупнее: у элеватора (gafc80ee1) карточка называет ту же
    # выручку 11 млн ₽, что и отчетность, — подставлять нечего.
    rev_report = _pick(report, 'revenue_rub', '2110') if report and report.get('year') else None
    card_base = bool(card_revenue) and (
        (not methods and not (report and report.get('year')))
        or bool(mismatch and ('card_revenue' in mismatch['signals']
                              or ('holding' in mismatch['signals'] and card_revenue > (rev_report or 0)))))
    if card_base:
        cell, scope = (dm.find_cell(table, 'ps', ind, None) if ind else None), 'отрасль'
        if not cell or cell.get('median') is None:
            cell, scope = dm.find_cell(table, 'ps', None, None), 'все отрасли'
        if cell and cell.get('median') is not None:
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
    # Отчетность не той компании — ее выручка не размер бизнеса; берется выручка
    # из карточки, а без нее размер неизвестен.
    if mismatch:
        size = card_revenue if card_base else None
    else:
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

    # МИРОВОЙ ОРИЕНТИР — ТОЛЬКО КОГДА РОССИЙСКИХ МЕТОДОВ НЕТ (владелец, 29 октября
    # 2026): тогда он дает верхнюю границу, а не диапазон. Есть хоть один метод
    # по сделкам, бирже или базе — Дамодаран не показывается вовсе.
    global_methods = [] if methods else global_methods
    # ПО БАЛАНСУ: капитал компании (строка 1300) — нижняя граница. Сделку редко
    # закрывают дешевле балансового капитала; для производств, недвижимости и
    # банков это осмысленный ориентир, для ИТ — слабый (так и пишем).
    floor = None
    equity = _pick(report, 'equity_rub', '1300') if report and report.get('year') else None
    if equity and equity > 0:
        floor = {'equity_rub': equity, 'report_year': report['year'],
                 'stake_rub': equity * stake / 100 if stake else None}

    # ДИАПАЗОН НЕ НИЖЕ БАЛАНСА (владелец, 6 ноября 2026). Метод, который дает за
    # 100% меньше собственного капитала, считает не по той базе: выручка или
    # прибыль этого юрлица не отражают масштаб бизнеса. Он остается в сводке с
    # пометкой и в итог не входит; нижний конец диапазона поднимается до
    # капитала, а диапазон целиком ниже капитала не показывается вовсе.
    if floor:
        for m in methods + global_methods:
            if not m.get('unreliable') and m['full_rub'] < floor['equity_rub']:
                m['unreliable'] = 'below_floor'
    reliable = [m for m in methods if not m.get('unreliable')]
    global_ok = [m for m in global_methods if not m.get('unreliable')]

    rng, range_kind = None, 'estimate'
    basis = reliable or global_ok
    centrals = [m['stake_rub'] if stake else m['full_rub'] for m in basis]
    if len(centrals) >= 2:
        rng = (min(centrals), max(centrals))
    elif len(centrals) == 1:
        m = basis[0]
        k = (stake / 100) if stake else 1.0
        lo = m['base_rub'] * (m['q1'] or m['median']) * k
        hi = m['base_rub'] * (m['q3'] or m['median']) * k
        rng = (min(lo, hi), max(lo, hi)) if hi > 0 else None
    floor_cut = False
    if rng and floor:
        fl = floor['stake_rub'] or floor['equity_rub']
        if rng[1] < fl:
            rng = None
        elif rng[0] < fl:
            rng, floor_cut = (fl, rng[1]), True
    if rng:
        rng = (_round2(rng[0]), _round2(rng[1]))
    if rng and not reliable:
        range_kind = 'upper'          # только мировой ориентир: верхняя граница
    elif not rng and src:
        range_kind = 'sources'        # расчет не годится — опора на оценку источников
    elif not rng and floor:
        range_kind = 'floor'          # только баланс: нижняя граница

    # Расхождение с оценкой источников: за долю она или за всю компанию — из
    # текста не видно, поэтому берется ближняя из двух баз.
    if src and rng:
        bases = [rng] + ([(rng[0] * 100 / stake, rng[1] * 100 / stake)] if stake and stake < 99.5 else [])
        d = min(_distance((src['lo'], src['hi']), b) for b in bases)
        src = dict(src, ratio=d, direction=('higher' if src['lo'] > rng[1] else 'lower') if d > 1 else None,
                   divergent=d > DIVERGENCE_MAX)
        if src['divergent']:
            src['reason'] = _divergence_reason(src, card_revenue if mismatch and card_base else None, methods)
    elif src:
        src = dict(src, ratio=None, direction=None, divergent=False)

    return {
        'deal_id': deal.get('id'), 'title': deal.get('title'), 'year': year,
        'company': company_name, 'industry': ind, 'stake': stake,
        'report_year': (report or {}).get('year'), 'report_note': report_note,
        'revenue_rub': _pick(report, 'revenue_rub', '2110') if report else None,
        'net_profit_rub': _pick(report, 'net_profit_rub', '2400') if report else None,
        'methods': methods, 'benchmarks': benchmarks, 'global_methods': global_methods, 'floor': floor,
        'comparables': comps, 'experts': experts,
        'card_revenue_rub': card_revenue, 'size_unknown': size_unknown, 'hidden_for_size': hidden_for_size,
        'range': rng, 'range_kind': range_kind, 'floor_cut': floor_cut,
        'source_value': src, 'report_mismatch': mismatch, 'card_base': card_base,
        'range_text': range_text(rng, stake, range_kind, floor, src),
    }


# Почему метод не вошел в итог — одной фразой для сводки, шаблона и карточки.
UNRELIABLE_TEXT = {
    'report_scale': 'в итог не входит: отчетность ФНС — только одной компании, а не всего бизнеса',
    'below_floor': 'в итог не входит: дает меньше балансового капитала — выручка или прибыль по отчетности '
                   'не отражают масштаб бизнеса',
}


def _divergence_reason(src: dict, card_base_rub: float | None, methods: list[dict]) -> str:
    """Вероятная причина, по которой оценка источников и расчет расходятся в
    разы. Отчетность не той компании причиной уже не бывает: с ней расчет либо
    перешел на выручку из карточки (`card_base_rub`), либо в итог не вошел."""
    if card_base_rub and src['direction'] == 'lower':
        return (f'расчет Компаса идет по выручке бизнеса из источника — {money(card_base_rub)}, а оценка '
                'могла относиться к меньшей его части или учитывать долг и скидку за неконтрольную долю')
    if card_base_rub:
        return (f'расчет Компаса идет по выручке бизнеса из источника — {money(card_base_rub)}; источник '
                'оценки мог считать по прибыли или прогнозу; по открытым данным точнее не сказать')
    if src['direction'] == 'higher':
        if any(m.get('unreliable') == 'below_floor' for m in methods):
            return ('выручка или прибыль по отчетности ФНС малы для бизнеса такого масштаба: '
                    'возможно, это отчетность не всей группы')
        return ('источник мог считать по отчетности всей группы, по прогнозу или с учетом долга; '
                'по открытым данным точнее не сказать')
    return ('источник мог оценивать купленную долю, а не всю компанию, или учитывать долг и скидку '
            'за срочную продажу; по открытым данным точнее не сказать')


def can_estimate(s: dict) -> bool:
    """Есть чем считать: хотя бы один метод, похожая сделка по размеру или
    оценка из источников. Иначе кнопки «Посчитать» на карточке нет вовсе
    (владелец, 29 октября 2026: «где мы знаем, что оценку дать нельзя —
    вообще не будем даже кнопку добавлять»)."""
    return bool(s.get('methods') or s.get('global_methods') or s.get('floor')
                or s.get('comparables') or s.get('experts'))


def range_text(rng, stake, range_kind='estimate', floor=None, src=None) -> str | None:
    what = f'за {_pct(stake)}' if stake and stake < 99.5 else 'за 100%'
    if not rng:
        # За долю оценка источников или за всю компанию — из текста не видно,
        # поэтому без «за X%».
        if range_kind == 'sources' and src:
            return f'≈ {src["text"]} по оценке источников'
        if range_kind == 'floor' and floor:
            return f'не ниже {money(floor["stake_rub"] or floor["equity_rub"])} {what}'
        return None
    lo, hi = money(rng[0]), money(rng[1])
    core = lo if lo == hi else _join_range(rng)
    if range_kind == 'upper':
        return f'до {money(rng[1])} {what}, верхняя граница'
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


def _method_tail(m: dict) -> str:
    return f' — {UNRELIABLE_TEXT[m["unreliable"]]}' if m.get('unreliable') else ''


def source_line(s: dict) -> str | None:
    """Оценка источников рядом с итогом — одна строка для сводки и карточки:
    «31–36 млрд ₽, в 30 раз выше расчета Компаса»."""
    src = s.get('source_value')
    if not src:
        return None
    if src.get('divergent'):
        return (f'{src["text"]}, {times(src["ratio"])} '
                f'{"выше" if src["direction"] == "higher" else "ниже"} расчета Компаса')
    if s.get('range_kind') == 'sources':
        return src['text']
    if src.get('ratio') == 1.0:
        return f'{src["text"]}, в пределах расчета Компаса'
    if src.get('ratio'):
        return f'{src["text"]}, близко к расчету Компаса'
    return src['text']


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
        if s.get('report_mismatch'):
            mm = s['report_mismatch']['text']
            lines.append(f'Оговорка: {mm[0].lower() + mm[1:]}. Методы по этой отчетности в итог не входят'
                         + ('; вместо нее взята выручка бизнеса по данным источника — '
                            f'{money(s["card_revenue_rub"])}' if s.get('card_base') else ''))
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
                + (f', за долю {_pct(s["stake"])} — {money(m["stake_rub"])}' if m['stake_rub'] else '') + _method_tail(m))
            continue
        where = f'отрасль «{m["industry"]}»' if m['industry'] else 'все отрасли (в отрасли мало сделок)'
        lines.append(
            f'Метод {m["label"]} по базе Компаса: {m["base_name"]} {money(m["base_rub"])} × медиана {str(m["median"]).replace(".", ",")}× '
            f'({where}, {deals_word(m["count"])}) = {money(m["full_rub"])} за 100%'
            + (f', за долю {_pct(s["stake"])} — {money(m["stake_rub"])}' if m['stake_rub'] else '') + _method_tail(m))
    if any(m.get('external') and m['metric'] == 'ev_ebitda' and not m.get('unreliable') for m in s['methods']):
        lines.append('Оговорка: EBITDA в отчетности ФНС нет, мультипликатор EV/EBITDA применен к операционной прибыли '
                     '(без амортизации), поэтому такая оценка скорее занижена')
    for m in s.get('global_methods') or []:
        e = m['external']
        lines.append(
            f'Мировой ориентир, {e["source"]}, сектор «{e["label"]}», {e["year"]} год: {m["label"]} '
            f'{m["base_name"]} {money(m["base_rub"])} × {str(m["median"]).replace(".", ",")}× = {money(m["full_rub"])} за 100%'
            + (f', за долю {_pct(s["stake"])} — {money(m["stake_rub"])}' if m['stake_rub'] else '')
            + ('; уровни там в 2–3 раза выше российских, поэтому это верхняя граница, а не оценка'
               if not m.get('unreliable') else _method_tail(m)))
    if s.get('floor'):
        f = s['floor']
        lines.append(f'Балансовый капитал по отчетности ФНС за {f["report_year"]} год: {money(f["equity_rub"])}'
                     + (f', на долю {_pct(s["stake"])} — {money(f["stake_rub"])}' if f['stake_rub'] else '')
                     + ' — нижняя граница: дешевле собственного капитала компании продают редко')
        if s.get('floor_cut'):
            lines.append('Нижний конец диапазона поднят до балансового капитала: итог Компаса не бывает ниже него')
    if s['range_text']:
        kind = {'upper': 'Верхняя граница по мировому ориентиру', 'floor': 'Нижняя граница по балансу',
                'sources': 'Итог — оценка из открытых источников (расчет по отчетности для этой компании не годится)'}.get(
            s.get('range_kind'), 'Итоговый диапазон Компаса')
        lines.append(f'{kind}: {s["range_text"]}')
    src = s.get('source_value')
    if src and s.get('range_kind') != 'sources':
        lines.append(f'Оценка из открытых источников числом: {source_line(s)} '
                     '(за долю она или за всю компанию — как сказано в источнике)')
        if src.get('divergent'):
            lines.append(f'Расхождение с оценкой источников {times(src["ratio"])}; вероятная причина: {src["reason"]}. '
                         'Назвать это рядом с итогом, в первом абзаце')
    for c in s['comparables']:
        mult = ', '.join(f'{k.upper().replace("PS", "P/S").replace("PE", "P/E")} {str(round(v, 1)).replace(".", ",")}×'
                         for k, v in c['multiples'].items())
        lines.append(f'Похожая сделка {c["year"]}: {c["title"]} — {money(c["price_rub"])}'
                     + (f' за {_pct(c["stake"])}' if c['stake'] else '') + (f'; {mult}' if mult else ''))
    if s['experts']:
        lines.append(f'Оценки из открытых источников: {s["experts"]}')
    return '\n'.join(lines)


def _why_not_counted(s: dict) -> str | None:
    """Почему методы по отчетности не вошли в итог — одной фразой с точкой."""
    if s.get('report_mismatch'):
        return s['report_mismatch']['text'] + '.'
    low = [m for m in s['methods'] + (s.get('global_methods') or []) if m.get('unreliable') == 'below_floor']
    if low and s.get('floor'):
        names = ', '.join(dict.fromkeys(m['label'] for m in low))
        return (f'Мультипликаторы ({names}) дают меньше балансового капитала компании '
                f'({money(s["floor"]["equity_rub"])}), значит, выручка или прибыль по отчетности не отражают '
                'масштаб бизнеса, и в итог они не входят.')
    return None


def template_text(s: dict) -> list[str]:
    """Объяснение без модели: модель недоступна или назвала лишнее число.
    Случаи (владелец, 29 октября и 6 ноября 2026): есть российские методы —
    диапазон; только мировой ориентир — верхняя граница; расчет по
    отчетности не годится, но есть оценка источников — она и итог; только
    баланс — нижняя граница; ничего — одна фраза, кнопки на карточке в этом
    случае нет вовсе. Оценка источников, расходящаяся с расчетом в разы,
    называется в первом абзаце вместе с вероятной причиной."""
    out = []
    kind = s.get('range_kind') or 'estimate'
    src = s.get('source_value')
    reliable = [m for m in s['methods'] if not m.get('unreliable')]
    why_not = _why_not_counted(s)
    if s['range_text'] and kind == 'estimate':
        core = s["range_text"].replace("≈ ", "около ")
        if src and src.get('divergent'):
            out.append(f'Оценка из открытых источников — {src["text"]}, а расчет Компаса дает {core}: '
                       f'{times(src["ratio"])} {"меньше" if src["direction"] == "higher" else "больше"}. '
                       f'Вероятная причина: {src["reason"]}.')
        else:
            out.append(f'По расчету Компаса сделка могла стоить {core}. '
                       'Это прикидка по отчетности и мультипликаторам похожих сделок, а не цена договора.'
                       + (f' Оценка из открытых источников — {source_line(s)}.' if src else ''))
        names = ', '.join(dict.fromkeys(m['label'] for m in reliable))
        if s.get('report_mismatch') and not reliable[0]['report_year']:
            out.append(f'{s["report_mismatch"]["text"]}. Поэтому взяли выручку бизнеса по данным источника — '
                       f'{money(reliable[0]["base_rub"])} — и медианный мультипликатор {names} по сделкам '
                       'с известной ценой.')
        elif reliable[0]['report_year']:
            ext_names = sorted({m['external']['source'] for m in reliable if m.get('external')})
            own = any(not m.get('external') for m in reliable)
            parts = (['медианы по сделкам с известной ценой из базы Компаса'] if own else []) \
                + ([f'отраслевые ориентиры из открытых исследований ({", ".join(ext_names)})'] if ext_names else [])
            out.append(f'Взяли отчетность компании за {reliable[0]["report_year"]} год и мультипликаторы '
                       f'({names}): {" и ".join(parts)}. Разные методы дают разный результат — '
                       'отсюда ширина диапазона; ниже видно, что дает каждый.'
                       + (f' {why_not}' if why_not else '')
                       + (' Нижний конец диапазона — балансовый капитал: дешевле него продают редко.'
                          if s.get('floor_cut') else ''))
        else:
            out.append(f'Отчетности компании в базе нет, взяли выручку по данным источника и медианный '
                       f'мультипликатор {names} по сделкам отрасли с известной ценой.')
    elif s['range_text'] and kind == 'upper':
        g = s['global_methods'][0]['external']
        out.append(f'Российских ориентиров по этой отрасли нет: ни сделок с известной ценой, ни биржевых '
                   f'мультипликаторов. Есть мировые ({g["source"]}, {g["year"]} год), но там компании '
                   'оцениваются в 2–3 раза дороже российских, поэтому по ним можно назвать только '
                   f'верхнюю границу: {s["range_text"]}.'
                   + (f' Оценка из открытых источников — {source_line(s)}.' if src else ''))
    elif s['range_text'] and kind == 'sources':
        out.append(f'Опираемся на оценку из открытых источников: {src["text"]}. Посчитать цену по отчетности '
                   'не получилось' + (f': {why_not[0].lower() + why_not[1:]}' if why_not else '.'))
        if s.get('floor'):
            out.append(f'Балансовый капитал по отчетности за {s["floor"]["report_year"]} год — '
                       f'{money(s["floor"]["stake_rub"] or s["floor"]["equity_rub"])}; дешевле него продают редко.')
    elif s['range_text'] and kind == 'floor':
        f = s['floor']
        if why_not:
            out.append(f'Посчитать цену по мультипликаторам не получилось. {why_not} Есть балансовый капитал '
                       f'за {f["report_year"]} год — дешевле него продают редко, поэтому это нижняя граница: '
                       f'{s["range_text"]}.')
        else:
            out.append(f'Посчитать цену по мультипликаторам не получилось: нет российских ориентиров по отрасли'
                       + (' и прибыли у компании' if (s.get('net_profit_rub') or 0) <= 0 else '')
                       + f'. Есть только балансовый капитал за {f["report_year"]} год — дешевле него продают '
                       f'редко, поэтому это нижняя граница: {s["range_text"]}.')
    elif s['comparables'] or s['experts']:
        out.append('Посчитать цену по отчетности не получилось: '
                   + ('нет отчетности покупаемой компании за год до сделки.' if not s['report_year']
                      else 'у компании убыток или в отрасли мало сделок с известной ценой.')
                   + ' Ниже — с чем можно сравнить.')
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
    'Ты — аналитик сервиса «Компас» о сделках M&A в России. Цену сделки стороны не раскрыли; объясни читателю, '
    'сколько она могла стоить, — только по сводке ниже. Никаких чисел, которых нет в сводке, ничего не пересчитывай, '
    'итог бери ровно из сводки: это диапазон, или верхняя граница по мировому ориентиру, или оценка из открытых '
    'источников, или нижняя граница по балансу. Методы с пометкой «в итог не входит» итогом не называй, скажи '
    'коротко, почему они не вошли. Если в сводке есть строка «Расхождение с оценкой источников», в первом абзаце '
    'рядом с итогом назови оценку источников, во сколько раз она расходится с расчетом и вероятную причину — '
    'так, как в сводке. '
    'Все числа цифрами и в том виде, как в сводке (1,6 млрд ₽, а не «полтора миллиарда»). '
    'Пиши по-русски, просто и по-деловому, без заголовков, списков и markdown; два-три коротких абзаца через пустую '
    'строку: 1) итог и что он за долю; 2) из чего получился — какие методы и источники, названные как в сводке, и '
    'почему это только граница, если это граница; 3) одной-двумя фразами похожие сделки и оценки источников, если есть, '
    'и чего расчет не учитывает (долг, премия за контроль, условия сделки). Если итога нет — одной фразой, каких '
    'данных не хватает. Без инвестиционных советов.'
)
