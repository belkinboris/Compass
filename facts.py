# -*- coding: utf-8 -*-
"""Слой фактов: структурные значения с происхождением, по которым считаются
числа на экране. Проза карточки — для читателя; вычисления — только отсюда.

ЗАЧЕМ (архитектурное решение 6 сентября 2026, после двух аудитов и двух
разборов рецензента). Три структурные причины повторяющихся дефектов:
единицей правды была проза («консолидировал 100%, выкупив 30%»), и аналитика
выводила из неё числа регэкспами; у факта не было происхождения — прочитан,
выведен правилом или предположен, для расчёта выглядело одинаково; правила
жили в двух исполнителях (Python и JS) и расходились. Отсюда: у сделки есть
объект `facts` с небольшим набором вычислимых фактов, у каждого — основание
(`basis`), цитата и источник; правила больше не решают, а ПРЕДЛАГАЮТ
(basis 'rule'); допуск к каждому показателю определяется отдельно; факты
считаются здесь один раз и уезжают в JSON, клиент их только читает.

ОСНОВАНИЯ (`BASES`), по возрастанию доверия:
    unknown   — карточка факта не содержит;
    rule      — предложено разбором текста (deal_multiples.*) или явным
                полем карточки без цитаты;
    stale     — было прочитано, но с тех пор изменились поля карточки,
                по которым факт читали (отпечаток `card_hash`), — до
                повторного чтения считается как rule;
    read      — одно чтение источника с дословной цитатой, проверенной
                pipeline/facts_confirm.py;
    verified  — два независимых чтения сошлись в значении и смысле (или
                подтвердил человек: verified_by начинается с 'human');
    disputed  — два чтения разошлись; ждёт человека, в расчёты не идёт.

ФАКТЫ (`FACT_KEYS`):
    stake   — доля, приобретаемая в ЭТОЙ сделке (%), с объектом и событием;
    price   — сумма: рублёвое значение, смысл раскрытия (`meaning`,
              deal_multiples.SUM_BASES) и ПЕРИМЕТР цены (`scope`: package —
              цена пакета, equity — вся компания, ev — с долгом, unknown);
    date    — дата и её основание (deal_multiples.DATE_BASES);
    nature  — признаки природы сделки, НЕ взаимоисключающие: смена контроля,
              деньги в компанию (cash-in), финансирование, торги,
              реорганизация;
    target  — предмет как юрлицо: профиль, ИНН из реестра, лот, банк, и
              подтверждение ПЕРИМЕТРА (`perimeter`): что отчётность этого
              юрлица описывает купленный бизнес.

ДОПУСК ПО ПОКАЗАТЕЛЯМ (`METRICS`, `admitted()`), разный для каждого:
    count          — сделка считается в числе сделок: есть дата с годом;
    industry       — + отрасль названа;
    purchase_sums  — суммы по годам/отраслям (графики): покупка (не cash-in,
                     не финансирование, не реорганизация), состоялась, цена
                     названа сторонами в рублях хотя бы по тексту (rule);
    top_purchases  — список крупнейших покупок на экране: то же, но сделка
                     не «обсуждается» и цена ПРОЧИТАНА в источнике (read/verified);
    multiple_text  — текстовая часть допуска к мультипликатору: смена
                     контроля, предмет — одно юрлицо с ИНН, не банк и не лот,
                     периметр подтверждён, доля ≥95% и цена — ВСЁ verified;
                     финансовую часть (отчётность за нужный год) добавляет
                     deal_multiples.compute_market_multiples.

Отсутствие цены не выкидывает достоверную сделку из числа сделок, а
отсутствие точной доли не мешает показать раскрытую цену покупки — у каждого
показателя свой набор фактов.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import deal_multiples as dm

BASES = ('unknown', 'rule', 'stale', 'read', 'verified', 'disputed')
TRUSTED = ('read', 'verified')
FACT_KEYS = ('stake', 'price', 'date', 'nature', 'target')
METRICS = ('count', 'industry', 'purchase_sums', 'top_purchases', 'multiple_text')
PRICE_SCOPES = ('package', 'equity', 'ev', 'unknown')
NATURE_FLAGS = ('control_change', 'cash_in', 'financing', 'auction', 'reorganization')
PURCHASE_TYPES = ('M&A', 'Продажа с торгов')

BASIS_LABELS = {
    'unknown': 'нет в карточке',
    'rule': 'по тексту карточки',
    'stale': 'прочитано, но карточка с тех пор изменилась',
    'read': 'прочитано в источнике',
    'verified': 'подтверждено двумя независимыми чтениями',
    'disputed': 'два чтения разошлись — ждёт человека',
}
REASON_LABELS = {
    'ok': 'допущена',
    'no_year': 'нет даты с годом',
    'before_site_year': 'сделка раньше 2022 года',
    'no_industry': 'отрасль не названа',
    'not_purchase': 'не покупка (деньги в компанию, финансирование, реорганизация, IPO)',
    'failed': 'сделка не состоялась',
    'discussion_only': 'сделка только обсуждается',
    'auction_open': 'торги не завершены',
    'price_not_disclosed': 'цена сторонами не названа',
    'price_not_rub': 'цена не в рублях',
    'price_not_read': 'цена не прочитана в источнике',
    'price_disputed': 'два чтения цены разошлись',
    'stake_not_verified': 'доля не подтверждена двумя чтениями',
    'stake_below': 'куплена доля меньше 95%',
    'price_not_verified': 'цена не подтверждена двумя чтениями',
    'price_scope_unknown': 'не ясно, за что цена: пакет, компания или с долгом',
    'not_control_change': 'не смена контроля',
    'no_target': 'предмет не привязан к профилю компании',
    'target_lot': 'предмет — лот из нескольких юрлиц',
    'target_bank': 'предмет — банк',
    'target_unconfirmed': 'у предмета не подтверждён ИНН',
    'perimeter_not_verified': 'периметр отчётности не подтверждён чтением',
    'stale': 'карточка изменилась после чтения — факт ждёт повторного чтения',
}


# ---------- отпечатки: какие поля карточки «держат» каждый факт ----------

def _hash(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]


def card_hash(deal: dict[str, Any], key: str) -> str:
    """Отпечаток полей карточки, по которым факт читали: изменились они —
    прочитанный факт становится stale и ждёт повторного чтения (пункт
    рецензента: при изменении значимых фактов пересматривать допуск)."""
    eco = deal.get('eco') or {}
    if key == 'stake':
        return _hash(deal.get('title'), eco.get('share'), deal.get('asset'), deal.get('stake_acquired'))
    if key == 'price':
        return _hash(deal.get('sum'), deal.get('sum_basis'), deal.get('type'), deal.get('status'))
    if key == 'date':
        return _hash(deal.get('date'), deal.get('date_basis'),
                     [(e.get('kind'), e.get('date')) for e in deal.get('events') or [] if isinstance(e, dict)])
    if key == 'nature':
        return _hash(deal.get('type'), deal.get('title'), deal.get('status'))
    if key == 'target':
        return _hash(deal.get('target'), deal.get('asset_id'))
    raise KeyError(key)


# ---------- правила как предложения ----------

def _nature_by_rule(deal: dict[str, Any]) -> dict[str, Any]:
    t = str(deal.get('type') or '').strip()
    title = str(deal.get('title') or '')
    cash_in = t in ('Инвестиция', 'IPO') or bool(re.search(r'допэмисс|SPO|закрыт[а-яё]*\s+подписк', title, re.I)) \
        and not re.search(r'оплат[а-яё]*\s+допэмисс', title, re.I)
    financing = t.startswith('Финансирование')
    reorganization = t == 'Реорганизация'
    auction = t == 'Продажа с торгов'
    control_change = t in PURCHASE_TYPES and not cash_in
    return {'control_change': control_change, 'cash_in': bool(cash_in), 'financing': financing,
            'auction': auction, 'reorganization': reorganization}


def _target_by_rule(deal: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    target = dm.target_of(deal)
    reg = (ctx.get('registry') or {}).get(target) if target else None
    return {
        'company_id': target,
        'inn': (reg or {}).get('inn') if reg and reg.get('decision') == 'confirmed' else None,
        'confirmed': bool(reg and reg.get('decision') == 'confirmed'),
        'bank': bool(reg and reg.get('decision') == 'bank'),
        'lot': bool(target and target in (ctx.get('lot_ids') or set())),
    }


def _fresh(existing: dict[str, Any] | None, deal: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Прочитанный факт, если он есть и карточка с тех пор не менялась."""
    if not existing or existing.get('basis') not in ('read', 'verified', 'disputed'):
        return None
    if existing.get('card_hash') != card_hash(deal, key):
        return dict(existing, basis='stale', stale_from=existing.get('basis'))
    return existing


def derive(deal: dict[str, Any], ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """Объект `facts` для карточки: прочитанные факты сохраняются (или
    помечаются stale), остальное предлагается правилами (basis 'rule').
    Идемпотентна: derive(derive(...)) даёт то же самое."""
    ctx = ctx or {}
    old = deal.get('facts') or {}
    facts: dict[str, Any] = {}

    # доля
    kept = _fresh(old.get('stake'), deal, 'stake')
    if kept:
        facts['stake'] = kept
    else:
        value = dm.stake_established(deal)
        facts['stake'] = {'value': value, 'basis': 'rule' if value is not None else 'unknown',
                          'card_hash': card_hash(deal, 'stake')}

    # цена
    kept = _fresh(old.get('price'), deal, 'price')
    if kept:
        facts['price'] = kept
    else:
        meaning = dm.sum_basis(deal)
        value = dm.parse_rub_sum(deal.get('sum')) if meaning == 'disclosed' else None
        facts['price'] = {'value_rub': value, 'meaning': meaning, 'scope': 'unknown',
                          'basis': 'rule' if meaning != 'undisclosed' else 'unknown',
                          'card_hash': card_hash(deal, 'price')}

    # дата
    kept = _fresh(old.get('date'), deal, 'date')
    if kept:
        facts['date'] = kept
    else:
        ds = str(deal.get('date') or '')
        facts['date'] = {'value': ds or None,
                         'meaning': deal.get('date_basis') if deal.get('date_basis') in dm.DATE_BASES else 'unknown',
                         'basis': 'rule' if ds else 'unknown', 'card_hash': card_hash(deal, 'date')}

    # природа
    kept = _fresh(old.get('nature'), deal, 'nature')
    facts['nature'] = kept or dict(_nature_by_rule(deal), basis='rule', card_hash=card_hash(deal, 'nature'))

    # предмет: «прочитанность» здесь — подтверждение периметра, а не basis
    # (basis у предмета — registry/rule, ИНН приходит из реестра)
    kept = None
    prev = old.get('target') or {}
    if prev.get('perimeter') in ('read', 'verified', 'disputed', 'refuted'):
        kept = prev if prev.get('card_hash') == card_hash(deal, 'target') else dict(prev, perimeter='stale', stale_from=prev.get('perimeter'))
    if kept:
        facts['target'] = dict(kept, **_target_by_rule(deal, ctx))  # реестр — всегда свежий
    else:
        t = _target_by_rule(deal, ctx)
        facts['target'] = dict(t, basis='registry' if t['confirmed'] else ('rule' if t['company_id'] else 'unknown'),
                               perimeter='unknown', card_hash=card_hash(deal, 'target'))

    facts['admitted'] = {m: admitted(dict(deal, facts=facts), m)[0] for m in METRICS}
    facts['reasons'] = {m: admitted(dict(deal, facts=facts), m)[1] for m in METRICS}
    return facts


# ---------- допуск по показателям ----------

def _basis(fact: dict[str, Any] | None) -> str:
    return (fact or {}).get('basis') or 'unknown'


def admitted(deal: dict[str, Any], metric: str) -> tuple[bool, str]:
    """Допущена ли сделка к показателю и почему нет (ключ REASON_LABELS)."""
    f = deal.get('facts') or {}
    stake, price, date, nature, target = (f.get(k) or {} for k in FACT_KEYS)
    year = dm.year_of(deal)
    if metric == 'count':
        if not year:
            return False, 'no_year'
        return True, 'ok'
    if metric == 'industry':
        if not year:
            return False, 'no_year'
        if not deal.get('ind') or deal.get('ind') == 'Не определена':
            return False, 'no_industry'
        return True, 'ok'
    if metric in ('purchase_sums', 'top_purchases'):
        if nature.get('cash_in') or nature.get('financing') or nature.get('reorganization') \
                or str(deal.get('type') or '').strip() not in PURCHASE_TYPES:
            return False, 'not_purchase'
        if deal.get('status') == 'Не состоялась':
            return False, 'failed'
        if nature.get('auction') and deal.get('status') != 'Закрыта':
            return False, 'auction_open'
        if _basis(price) == 'disputed':
            return False, 'price_disputed'
        if price.get('meaning') != 'disclosed':
            return False, 'price_not_disclosed'
        if not price.get('value_rub'):
            return False, 'price_not_rub'
        if metric == 'top_purchases':
            # Список крупнейших — о сделках, которые состоялись или подписаны;
            # обсуждаемая цена (оферта «русской рулетки» Шишкарёв/«Дело», 74 млрд ₽,
            # от которой он потом отказался) в нём вводит в заблуждение, а в
            # суммах по годам объявленная стоимость — обычная практика.
            if deal.get('status') == 'Обсуждается':
                return False, 'discussion_only'
            if _basis(price) not in TRUSTED:
                return False, 'stale' if _basis(price) == 'stale' else 'price_not_read'
        return True, 'ok'
    if metric == 'multiple_text':
        if not nature.get('control_change') or str(deal.get('type') or '').strip() != 'M&A':
            return False, 'not_control_change'
        if deal.get('status') == 'Не состоялась':
            return False, 'failed'
        if not year or year < dm.MIN_YEAR:
            return False, 'before_site_year'
        if not target.get('company_id'):
            return False, 'no_target'
        if target.get('lot'):
            return False, 'target_lot'
        if target.get('bank'):
            return False, 'target_bank'
        if not target.get('confirmed'):
            return False, 'target_unconfirmed'
        if price.get('meaning') != 'disclosed' or not price.get('value_rub'):
            return False, 'price_not_disclosed'
        if _basis(price) == 'stale' or _basis(stake) == 'stale':
            return False, 'stale'
        if _basis(price) != 'verified':
            return False, 'price_not_verified'
        if price.get('scope') not in ('package', 'equity', 'ev'):
            return False, 'price_scope_unknown'
        if _basis(stake) != 'verified':
            return False, 'stake_not_verified'
        if (stake.get('value') or 0) < dm.MIN_STAKE_PERCENT:
            return False, 'stake_below'
        if target.get('perimeter') == 'stale':
            return False, 'stale'
        if target.get('perimeter') != 'verified':
            return False, 'perimeter_not_verified'
        return True, 'ok'
    raise KeyError(metric)


def build_ctx(base: dict[str, Any], registry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Контекст для derive: реестр ИНН по id профиля и множество лотов."""
    return {
        'registry': {r['company_id']: r for r in registry_rows},
        'lot_ids': {cid for cid, p in (base.get('companies') or {}).items() if p.get('lot')},
    }


def derive_all(base: dict[str, Any], ctx: dict[str, Any]) -> int:
    """Проставить facts всем сделкам базы; возвращает число изменённых."""
    changed = 0
    for d in base['deals']:
        new = derive(d, ctx)
        if d.get('facts') != new:
            d['facts'] = new
            changed += 1
    return changed


# ---------- арифметика: третий уровень проверки ----------

def number_checks(deal: dict[str, Any]) -> list[str]:
    """Проверки, которые не поймает ни цитата, ни смысл: порядок величины,
    валюта, единицы, доля против периметра цены. Пустой список — чисто."""
    f = deal.get('facts') or {}
    price, stake = f.get('price') or {}, f.get('stake') or {}
    out = []
    v = price.get('value_rub')
    if v is not None:
        if not (1e6 <= v <= 5e13):
            out.append('price_out_of_range')
        text = str(deal.get('sum') or '')
        unit = re.search(r'(тыс|млн|млрд|трлн)', text, re.I)
        if unit:
            expect = dm.UNIT_MULT[unit.group(1).lower()]
            if not (expect * 0.5 <= v <= expect * 100000):
                out.append('unit_mismatch')
        if re.search(r'[$€£¥]', text) and '₽' not in text:
            out.append('foreign_currency')
    s = stake.get('value')
    if s is not None and not (1 <= s <= 100):
        out.append('stake_out_of_range')
    if s is not None and s < dm.MIN_STAKE_PERCENT and price.get('scope') in ('equity', 'ev') \
            and f.get('admitted', {}).get('multiple_text'):
        out.append('package_stake_with_company_price')
    return out
