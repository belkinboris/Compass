# -*- coding: utf-8 -*-
"""Мультипликаторы сделок (EV/Выручка) — Этап 16, П1.

ПОЧЕМУ ЭТОТ МОДУЛЬ СУЩЕСТВУЕТ. Пилот (`pipeline/measure_deal_multiples_pilot.py`,
Этап 15) показал: сырое сопоставление «сумма сделки / выручка цели» без
фильтров даёт мультипликаторы до 4336x — не редкие сделки, а несопоставимые
величины (IPO/допэмиссия вместо продажи компании, доля вместо 100%, выручка
управляющей компании-СПВ вместо операционного бизнеса). Здесь та же методика,
что доказала себя в пилоте, перенесена в код, КОТОРЫЙ РЕАЛЬНО ПОКАЗЫВАЕТСЯ
ПОСЕТИТЕЛЮ, — и поэтому обвешана тестами на каждую найденную ловушку, а не
только на happy path.

ЧТО СЧИТАЕТСЯ «ЧИСТОЙ» СДЕЛКОЙ ДЛЯ МУЛЬТИПЛИКАТОРА:
  * `type == "M&A"` И названы ОБЕ стороны (покупатель и продавец) — тип
    сам по себе ненадёжен: у допэмиссий и SPO он тоже стоит «M&A» (см.
    CLAUDE.md, «Тип сделки определяет не только ярлык, но и какие роли
    существуют»), но у cash-in сделки структурно нет продавца — деньги
    идут в компанию, а не от одного акционера другому. Требование «обе
    стороны названы» отсеивает Segezha-допэмиссию и SPO «Эталона» ещё на
    текстовом фильтре, до всякого обращения к БФО.
  * сумма сделки — число В РУБЛЯХ (не $/€: курс на момент старой сделки
    сегодняшним пересчётом молча искажается, см. CLAUDE.md «Число может
    быть верным фактом и совсем не той величиной»).
  * сумма НЕ помечена «(по оценке)» — оценка не то же самое, что цена.
  * доля предмета сделки (если она вообще названа в тексте) — не меньше
    95%: сумма за долю меньше этого нельзя молча делить на выручку всей
    компании.
  * цель сделки — не банк (РСБУ банков не сопоставим с обычной выручкой,
    см. блок «По данным Банка России») и с подтверждённым по ИНН профилем
    (fns_registry.py, decision=confirmed).
  * выручка цели взята ЗА ГОД, ближайший к году сделки СВЕРХУ ВНИЗ не
    больше чем на один год (последний отчётный год перед закрытием —
    стандартная практика в M&A, а разрыв 2+ года почти всегда значит, что
    более свежей отчётности просто нет, и старое число может не отражать
    компанию на момент сделки).
  * итоговый мультипликатор — в разумных границах 0,1–15. Шире — почти
    всегда означает, что выручка взята не у того юридического лица (лот,
    управляющая компания-прослойка вместо операционного бизнеса), а не
    редкую сделку: см. находки пилота (g5eb6ff22 — 4336x, revenue
    юрлица-прослойки 17 млн ₽ при сумме сделки 75 млрд ₽).

Ничего из отброшенного не считается неверным фактом — это фильтр
СОПОСТАВИМОСТИ, а не оценка качества карточки: сделка без чистого
мультипликатора просто не участвует в статистике, её данные не трогаются.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select

MIN_MULTIPLE = 0.1
MAX_MULTIPLE = 15.0
MIN_STAKE_PERCENT = 95.0
MAX_YEAR_GAP = 1
MIN_YEAR = 2022
MIN_INDUSTRY_SAMPLE = 3

UNIT_MULT = {'тыс': 1e3, 'млн': 1e6, 'млрд': 1e9, 'трлн': 1e12}

_RUB_AMOUNT = re.compile(
    r'(?P<n1>\d[\d\s\xa0]*(?:[.,]\d+)?)'
    r'(?:\s*[–—-]\s*(?P<n2>\d[\d\s\xa0]*(?:[.,]\d+)?))?'
    r'\s*(?P<unit>тыс|млн|млрд|трлн)\.?\s*₽',
    re.I)
_STAKE_PCT = re.compile(r'(\d{1,3}(?:[.,]\d+)?)\s*%')
_ESTIMATE = re.compile(r'оценк|оценив', re.I)


def parse_rub_sum(text: str | None) -> float | None:
    """Число в рублях из строки суммы, или None, если это не ₽-сумма.

    Диапазон («36–45 млн ₽») усредняется — известное огрубление (см. урок
    «Диапазон при разборе может схлопнуться в одну цифру»), но для оценки
    порядка величины мультипликатора этого достаточно; сама карточка
    диапазон не теряет, он остаётся в `sum` как есть."""
    if not text:
        return None
    m = _RUB_AMOUNT.search(text)
    if not m:
        return None
    def num(s: str) -> float:
        return float(s.replace(' ', '').replace('\xa0', '').replace(',', '.'))
    n1 = num(m.group('n1'))
    n2 = num(m.group('n2')) if m.group('n2') else None
    mult = UNIT_MULT[m.group('unit').lower()]
    lo = n1 * mult
    hi = (n2 * mult) if n2 is not None else lo
    return (lo + hi) / 2


def is_estimate(text: str | None) -> bool:
    return bool(text) and bool(_ESTIMATE.search(text))


def stake_percent(deal: dict[str, Any]) -> float | None:
    """Доля предмета сделки в процентах, если она названа в тексте.

    None значит «доля не названа» — в контексте этого модуля такую сделку
    ТРЕТИРУЕМ как потенциально 100% (это стандартное умолчание для сделок
    смены контроля без явно указанной меньшей доли), а не отбрасываем;
    отбрасываются только сделки, где доля НАЗВАНА и она меньше порога."""
    for text in (deal.get('eco', {}).get('share'), deal.get('asset')):
        if not text:
            continue
        nums = [float(x.replace(',', '.')) for x in _STAKE_PCT.findall(text)]
        plausible = [n for n in nums if 1 <= n <= 100]
        if plausible:
            return max(plausible)
    return None


def year_of(deal: dict[str, Any]) -> int | None:
    ds = str(deal.get('date') or '')
    return int(ds[:4]) if ds[:4].isdigit() else None


def target_of(deal: dict[str, Any]) -> str | None:
    return deal.get('target') or deal.get('asset_id')


@dataclass
class MultipleCandidate:
    """Сделка, прошедшая ТЕКСТОВЫЕ фильтры (без обращения к БФО) —
    промежуточный шаг перед докачкой выручки цели из базы."""
    deal_id: str
    title: str
    target_id: str
    year: int
    sum_rub: float
    stake_percent: float | None


def find_candidates(deals: dict[str, dict[str, Any]], confirmed_ids: set[str],
                     bank_ids: set[str]) -> list[MultipleCandidate]:
    """Кандидаты по ТЕКСТУ карточки — без обращения к БФО (та часть фильтра,
    которую можно применить без единого запроса к базе)."""
    out = []
    for deal_id, d in deals.items():
        if d.get('type') != 'M&A':
            continue
        has_buyer = bool(d.get('buyer') or d.get('buyer_name'))
        has_seller = bool(d.get('seller') or d.get('seller_id'))
        if not (has_buyer and has_seller):
            continue
        yr = year_of(d)
        if not yr or yr < MIN_YEAR:
            continue
        target = target_of(d)
        if not target or target in bank_ids or target not in confirmed_ids:
            continue
        if is_estimate(d.get('sum')):
            continue
        stake = stake_percent(d)
        if stake is not None and stake < MIN_STAKE_PERCENT:
            continue
        sum_rub = parse_rub_sum(d.get('sum'))
        if not sum_rub or sum_rub <= 0:
            continue
        out.append(MultipleCandidate(
            deal_id=deal_id, title=d.get('title') or deal_id, target_id=target,
            year=yr, sum_rub=sum_rub, stake_percent=stake))
    return out


@dataclass
class DealMultiple:
    deal_id: str
    title: str
    target_id: str
    target_name: str | None
    year: int
    sum_rub: float
    revenue_rub: float
    revenue_year: int
    multiple: float


def multiple_for_candidate(cand: MultipleCandidate, revenue_rub: float | None,
                            revenue_year: int | None, target_name: str | None
                            ) -> DealMultiple | None:
    """Санитарная проверка одного кандидата с уже докачанной выручкой.

    Отдельная от `find_candidates` функция специально: текстовый фильтр не
    требует БД и тестируется без фикстур, а этот шаг — единственное место,
    трогающее реальное число выручки, и его легче всего проверить на
    придуманных значениях (см. test_deal_multiples.py)."""
    if revenue_rub is None or revenue_year is None or revenue_rub <= 0:
        return None
    if cand.year - revenue_year > MAX_YEAR_GAP or cand.year - revenue_year < 0:
        return None
    multiple = cand.sum_rub / revenue_rub
    if not (MIN_MULTIPLE <= multiple <= MAX_MULTIPLE):
        return None
    return DealMultiple(
        deal_id=cand.deal_id, title=cand.title, target_id=cand.target_id,
        target_name=target_name, year=cand.year, sum_rub=cand.sum_rub,
        revenue_rub=revenue_rub, revenue_year=revenue_year, multiple=round(multiple, 2))


def industry_medians(rows: list[DealMultiple], industry_of: dict[str, str]
                      ) -> list[dict[str, Any]]:
    """Медиана по отраслям с >=MIN_INDUSTRY_SAMPLE наблюдениями — меньше
    трёх сделок медианой не подписываем (см. CLAUDE.md, «У числа на экране
    два свойства: величина и множество» — знаменатель обязан быть честным,
    а на выборке в одну-две сделки медиана выглядит точнее, чем есть)."""
    by_ind: dict[str, list[float]] = {}
    for r in rows:
        ind = industry_of.get(r.target_id) or 'Не определена'
        by_ind.setdefault(ind, []).append(r.multiple)
    out = []
    for ind, mults in by_ind.items():
        if len(mults) < MIN_INDUSTRY_SAMPLE:
            continue
        s = sorted(mults)
        n = len(s)
        median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        out.append({'industry': ind, 'count': n, 'median': round(median, 2),
                     'min': round(s[0], 2), 'max': round(s[-1], 2)})
    out.sort(key=lambda x: -x['count'])
    return out


def overall_median(rows: list[DealMultiple]) -> float | None:
    if not rows:
        return None
    s = sorted(r.multiple for r in rows)
    n = len(s)
    return round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 2)


def compute_market_multiples(db, deals: dict[str, dict[str, Any]],
                              registry: dict[str, dict], get_company_profile) -> dict[str, Any]:
    """Полный расчёт для эндпоинта /api/analytics/multiples — единственная
    функция здесь, которая трогает БД; всё остальное в модуле — чистые
    функции над словарями, проверяемые без фикстур базы."""
    from db.models import FinancialReport, LegalEntity, LegalEntityMatchStatus

    confirmed_ids = {cid for cid, row in registry.items() if row['decision'] == 'confirmed'}
    bank_ids = {cid for cid, row in registry.items() if row['decision'] == 'bank'}
    candidates = find_candidates(deals, confirmed_ids, bank_ids)

    rows: list[DealMultiple] = []
    industry_of: dict[str, str] = {}
    for cand in candidates:
        entity = db.scalar(select(LegalEntity).where(
            LegalEntity.company_id == cand.target_id,
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
        ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id))
        if not entity:
            continue
        report = db.scalar(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id,
            FinancialReport.year < cand.year + 1,
            FinancialReport.revenue_rub.is_not(None),
        ).order_by(FinancialReport.year.desc()))
        if not report:
            continue
        dm = multiple_for_candidate(cand, float(report.revenue_rub), report.year, entity.legal_name)
        if not dm:
            continue
        rows.append(dm)
        profile = get_company_profile(cand.target_id)
        if profile and profile.get('ind'):
            industry_of[cand.target_id] = profile['ind']

    rows.sort(key=lambda r: r.year, reverse=True)
    return {
        'candidates_total': len(candidates),
        'clean_total': len(rows),
        'median': overall_median(rows),
        'industries': industry_medians(rows, industry_of),
        'deals': [{
            'id': r.deal_id, 'title': r.title, 'year': r.year,
            'target_id': r.target_id, 'target_name': r.target_name,
            'sum_rub': r.sum_rub, 'revenue_rub': r.revenue_rub,
            'revenue_year': r.revenue_year, 'multiple': r.multiple,
        } for r in rows],
        'methodology': (
            'Только сделки M&A с суммой в рублях (не оценка), долей предмета '
            '95% и выше, выручка цели — последний отчётный год перед сделкой '
            '(не позже одного года до неё), мультипликатор в границах 0,1–15. '
            'Сумма сделки может включать принятый долг — это EV-прокси, а не '
            'обязательно equity value.'
        ),
    }
