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
                     названа сторонами в рублях и ПРОЧИТАНА в источнике
                     (read/verified), дата не спорная, дубль не заподозрен;
                     до третьего разбора рецензента хватало текста (rule) —
                     и «фонд планирует привлечь до 30 млрд ₽» шёл в суммы
                     покупок как цена;
    top_purchases  — список крупнейших покупок на экране: то же, но сделка
                     не «обсуждается»;
    multiple_text  — текстовая часть допуска к мультипликатору: смена
                     контроля (подтверждена чтением), предмет — одно юрлицо
                     с ИНН, не банк и не лот, периметр подтверждён ПО
                     КОНКРЕТНОМУ ОТЧЁТУ (perimeter_report), доля ≥95% и цена
                     — ВСЁ verified; финансовую часть (отчётность за нужный
                     год) добавляет deal_multiples.compute_market_multiples.

Природа сделки: флаги считаются правилом по типу карточки (basis 'rule' у
объекта), а прочитан только ОДИН признак — смена контроля; его основание
лежит отдельно (`control_change_basis`), чтобы метка «подтверждено» не
распространялась на признаки, которых читатель не видел (третий разбор).
`auction` — «карточка типа «Продажа с торгов»», не «сделка прошла на
торгах»: M&A-карточка с аукционом в тексте этот флаг не получает.

Тождество между карточками: `identity.possible_duplicate` ставится
проходом по всей базе (derive_all): две допущенные к деньгам сделки одного
года с суммами в пределах полутора процентов и общим названием в кавычках,
предметом или покупателем — обе выпадают из денежных показателей, пока
сканер дублей (pipeline/find_duplicate_deal_candidates.py) не прочитан:
прочитанная и признанная не-дублем пара снимает подозрение.

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
NATURE_FLAGS = ('control_change', 'cash_in', 'financing', 'auction', 'reorganization', 'own_shares')
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
    'date_disputed': 'два чтения даты разошлись — сделку нельзя отнести к году',
    'possible_duplicate': 'похожа на другую карточку той же сделки — ждёт сканера дублей',
    'control_change_not_verified': 'смена контроля не подтверждена двумя чтениями',
    'perimeter_report_missing': 'периметр подтверждён без привязки к конкретному отчёту',
    'intragroup': 'передача внутри одной группы — конечный контроль не менялся',
    'price_event_disputed': 'два чтения относят цену к разным событиям — не разрешено',
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
    # Сделка компании с СОБСТВЕННЫМИ акциями (buyback, выкуп у нерезидентов,
    # продажа казначейского пакета) — не покупка бизнеса: «Магнит» выкупил
    # свои акции за 48,5 млрд ₽, цена названа компанией и прочитана — и всё
    # равно в «Крупнейшие покупки» ей не место. «С правом обратного выкупа»
    # (залог госпакета «Самолёта») — не выкуп, а условие.
    own_shares = bool(re.search(
        r'buyback|(?<!с правом )обратн[а-яё]*\s+выкуп|выкуп[а-яё]*\s+(?:собственн[а-яё]*|сво[а-яё]+)\s+(?:акци|дол)'
        r'|у\s+нерезидент|казначейск[а-яё]*\s+(?:пакет|акци)', title, re.I))
    control_change = t in PURCHASE_TYPES and not cash_in and not own_shares
    return {'control_change': control_change, 'cash_in': bool(cash_in), 'financing': financing,
            'auction': auction, 'reorganization': reorganization, 'own_shares': own_shares}


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

    # природа: флаги — правилом, прочитанный признак смены контроля — поверх,
    # со своим основанием
    prev = old.get('nature') or {}
    nature = dict(_nature_by_rule(deal), basis='rule', card_hash=card_hash(deal, 'nature'))
    cc_basis = prev.get('control_change_basis') or (prev.get('basis') if prev.get('basis') in ('read', 'verified', 'disputed') else None)
    if cc_basis:
        if prev.get('card_hash') != card_hash(deal, 'nature'):
            cc_basis = 'stale'
        nature.update({k: v for k, v in prev.items() if k not in NATURE_FLAGS and k not in ('basis', 'card_hash')})
        if cc_basis != 'disputed' and prev.get('control_change') is not None:
            nature['control_change'] = prev['control_change']
        nature['control_change_basis'] = cc_basis
        nature['card_hash'] = prev.get('card_hash') if cc_basis != 'stale' else card_hash(deal, 'nature')
    facts['nature'] = nature

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

    if old.get('identity'):
        facts['identity'] = old['identity']  # перепроверяется проходом derive_all
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
                or nature.get('own_shares') or str(deal.get('type') or '').strip() not in PURCHASE_TYPES:
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
        # Деньги складываются только из прочитанных цен: правило предлагает,
        # чтение решает — для графиков так же, как для списка крупнейших.
        if _basis(price) not in TRUSTED:
            return False, 'stale' if _basis(price) == 'stale' else 'price_not_read'
        # Спорная дата — сделку нельзя отнести к году (Shell/«Сахалин-2»: одно
        # чтение о разрешении НОВАТЭКу в 2023-м, другое о покупке «Газпромом»
        # в 2024-м при одинаковой сумме).
        if _basis(date) == 'disputed':
            return False, 'date_disputed'
        # Цена, у которой не разрешено, к какому событию она относится, в
        # показатель по годам не идёт — даже подтверждённая (четвёртый разбор).
        if price.get('event') == 'disputed':
            return False, 'price_event_disputed'
        # Передача внутри одной группы (казахстанские активы между структурами
        # VEON, взаимозачётом) — не покупка на рынке; чтение говорит это прямо.
        if nature.get('intragroup'):
            return False, 'intragroup'
        if (f.get('identity') or {}).get('possible_duplicate'):
            return False, 'possible_duplicate'
        if metric == 'top_purchases' and deal.get('status') == 'Обсуждается':
            # Список крупнейших — о сделках, которые состоялись или подписаны;
            # обсуждаемая цена (оферта «русской рулетки» Шишкарёв/«Дело», 74 млрд ₽,
            # от которой он потом отказался) в нём вводит в заблуждение.
            return False, 'discussion_only'
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
        # Порядок причин — от устройства сделки к чтению: сначала «не та
        # сделка / не тот предмет», потом «цена не прочитана», и только затем
        # «природа не подтверждена»: в списке исключённых читатель видит
        # самую содержательную причину, а не ту, что проверилась первой.
        if nature.get('control_change_basis') != 'verified':
            return False, 'control_change_not_verified'
        if nature.get('intragroup'):
            return False, 'intragroup'
        if price.get('event') == 'disputed':
            return False, 'price_event_disputed'
        if (f.get('identity') or {}).get('possible_duplicate'):
            return False, 'possible_duplicate'
        if _basis(stake) != 'verified':
            return False, 'stake_not_verified'
        if (stake.get('value') or 0) < dm.MIN_STAKE_PERCENT:
            return False, 'stake_below'
        if target.get('perimeter') == 'stale':
            return False, 'stale'
        if target.get('perimeter') != 'verified':
            return False, 'perimeter_not_verified'
        if not (target.get('perimeter_report') or {}).get('inn'):
            return False, 'perimeter_report_missing'
        if _basis(date) == 'disputed':
            return False, 'date_disputed'
        return True, 'ok'
    raise KeyError(metric)


def build_ctx(base: dict[str, Any], registry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Контекст для derive: реестр ИНН по id профиля и множество лотов."""
    return {
        'registry': {r['company_id']: r for r in registry_rows},
        'lot_ids': {cid for cid, p in (base.get('companies') or {}).items() if p.get('lot')},
    }


def derive_all(base: dict[str, Any], ctx: dict[str, Any]) -> int:
    """Проставить facts всем сделкам базы; возвращает число изменённых.
    Второй проход — тождество между карточками (possible_duplicate)."""
    changed = 0
    for d in base['deals']:
        new = derive(d, ctx)
        if d.get('facts') != new:
            d['facts'] = new
            changed += 1
    changed += mark_possible_duplicates(base, ctx)
    return changed


_QUOTED = re.compile(r'[«"“]([^»"”]{2,60})[»"”]')


def _names(deal: dict[str, Any]) -> set[tuple[str, ...]]:
    """Названия в кавычках из заголовка как кортежи основ слов (первые пять
    букв): «Азбука вкуса» и «Азбуки вкуса» — одно название."""
    out = set()
    for m in _QUOTED.findall(str(deal.get('title') or '')):
        words = tuple(w[:5] for w in re.findall(r'[а-яёa-z0-9]+', m.lower().replace('ё', 'е')) if len(w) >= 3)
        if words:
            out.add(words)
    return out


def _not_duplicate_pairs(ctx: dict[str, Any]) -> set[frozenset]:
    pairs = set(ctx.get('not_duplicates') or ())
    try:
        from pipeline import find_duplicate_deal_candidates as scanner
        pairs |= set(scanner.NOT_DUPLICATES.keys())
        pairs |= {frozenset(v['pair']) for v in scanner.load_read_state().values() if v.get('pair')}
    except Exception:  # noqa: BLE001 — сканер не обязателен для derive
        pass
    return pairs


def mark_possible_duplicates(base: dict[str, Any], ctx: dict[str, Any]) -> int:
    """Две сделки одного года с суммой в пределах 1,5% и общим названием в
    кавычках, предметом или покупателем — подозрение на одну сделку в двух
    карточках («Магнит» и «Тандер» покупают «Азбуку вкуса», 29,65 и 29,6
    млрд ₽). Обе выпадают из денежных показателей, пока пара не прочитана
    сканером дублей. Ставится только тем, у кого есть цена и год."""
    ok_pairs = _not_duplicate_pairs(ctx)
    by_year: dict[int, list[dict[str, Any]]] = {}
    for d in base['deals']:
        f = d.get('facts') or {}
        v = (f.get('price') or {}).get('value_rub')
        y = dm.year_of(d)
        if v and y and (f.get('price') or {}).get('meaning') == 'disclosed':
            by_year.setdefault(y, []).append(d)
    suspects: dict[str, set[str]] = {}
    for rows in by_year.values():
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                va, vb = a['facts']['price']['value_rub'], b['facts']['price']['value_rub']
                if abs(va - vb) > 0.015 * max(va, vb):
                    continue
                if frozenset((a['id'], b['id'])) in ok_pairs:
                    continue
                # общий покупатель сам по себе — не признак: Softline за один
                # месяц купила «МД Аудит» за 163 млн ₽ и Visitech за 162 млн ₽
                same_target = dm.target_of(a) and dm.target_of(a) == dm.target_of(b)
                if same_target or (_names(a) & _names(b)):
                    suspects.setdefault(a['id'], set()).add(b['id'])
                    suspects.setdefault(b['id'], set()).add(a['id'])
    changed = 0
    for d in base['deals']:
        f = d['facts']
        want = {'possible_duplicate': sorted(suspects[d['id']]), 'basis': 'rule'} if d['id'] in suspects else None
        if (f.get('identity') or None) != want:
            if want:
                f['identity'] = want
            else:
                f.pop('identity', None)
            f['admitted'] = {m: admitted(d, m)[0] for m in METRICS}
            f['reasons'] = {m: admitted(d, m)[1] for m in METRICS}
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
