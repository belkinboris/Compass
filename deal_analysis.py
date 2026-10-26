"""«Разбор сделки» — кнопка под схемой сделки на карточке.

Владелец 26 октября 2026: анализ «должен относиться ко всей карточке» и «не
должен дублировать то, что уже написано (кто сопровождал), а только давать
дополнительную информацию»; кнопка — под схемой сделки, не отдельная вкладка.

Поэтому модель видит две части сводки:
- КАРТОЧКА — то, что читатель уже видит; пересказывать это запрещено, оно
  нужно модели, чтобы понять сделку;
- ИЗ БАЗЫ КОМПАСА — то, чего на карточке нет: другие сделки покупателя,
  продавца и покупаемой компании, что происходит в отрасли (сколько сделок,
  кто покупает чаще всех, сколько обычно платят).
Разбор строится на второй части. Числа ответа сверяются со всей сводкой
(`price_estimate.clean_answer`): предложение с чужим числом выпадает.
"""
from __future__ import annotations

import statistics
from collections import Counter

CARD_FIELDS = (
    ('Цель сделки', ('eco', 'rationale')),
    ('Контекст', ('eco', 'context')),
    ('Показатели покупаемой компании', ('eco', 'target_fin')),
    ('Сумма', ('sum',)),
    ('Предмет и доля', ('eco', 'share')),
    ('Оценка и дисконт', ('eco', 'val')),
    ('Как устроена сделка', ('law', 'struct')),
    ('Согласования', ('law', 'appr')),
    ('Условия', ('law', 'terms')),
    ('Дополнительно', ('extra',)),
)
PARTY_DEALS_MAX = 8
LEADS = ('Для покупателя.', 'Для продавца.', 'Рынок вокруг.', 'Что может быть дальше.')
KNOWN_PRICE = ('disclosed', 'foreign_currency')


def _get(d: dict, path: tuple) -> str:
    v = d
    for k in path:
        v = v.get(k) if isinstance(v, dict) else None
    s = str(v or '').strip()
    return '' if s in ('—', '-') else s


def _advisors(deal: dict) -> str:
    adv = (deal.get('law') or {}).get('adv')
    if isinstance(adv, list):
        return '; '.join(f'{a[0]}: {a[1]}' for a in adv if isinstance(a, (list, tuple)) and len(a) > 1)
    return _get(deal, ('law', 'adv'))


def _party_deals(deal: dict, deals: dict, party_id: str | None) -> list[dict]:
    if not party_id:
        return []
    out = [dict(d, id=cid) for cid, d in deals.items() if cid != deal.get('id')
           and party_id in (d.get('buyer'), d.get('seller_id'), d.get('target'), d.get('asset_id'))]
    out.sort(key=lambda d: str(d.get('date') or ''), reverse=True)
    return out[:PARTY_DEALS_MAX]


def _year(d: dict) -> int | None:
    s = str(d.get('date') or '')
    return int(s[:4]) if s[:4].isdigit() else None


def industry_lines(deal: dict, deals: dict, name_of) -> list[str]:
    """Отрасль вокруг сделки: сколько сделок в этом и прошлом году, кто покупает
    чаще всех за два года, медиана названной цены покупки — только по базе."""
    ind, year = deal.get('ind'), _year(deal)
    if not ind or ind == 'Не определена' or not year:
        return []
    same = [d for cid, d in deals.items() if cid != deal.get('id') and d.get('ind') == ind]
    this = [d for d in same if _year(d) == year]
    prev = [d for d in same if _year(d) == year - 1]
    out = [f'В отрасли «{ind}» в базе: {len(this)} других сделок за {year} год, {len(prev)} — за {year - 1} год.']
    buyers = Counter(d.get('buyer') for d in same if d.get('buyer') and (_year(d) or 0) >= year - 1)
    top = [(b, n) for b, n in buyers.most_common(3) if n >= 2]
    if top:
        out.append('Чаще всех в отрасли за два года покупали: '
                   + ', '.join(f'{name_of(b) or b} — {n}' for b, n in top) + '.')
    prices = [float(((d.get('facts') or {}).get('price') or {}).get('value_rub'))
              for d in same if (_year(d) or 0) >= year - 2 and d.get('type') == 'M&A'
              and ((d.get('facts') or {}).get('price') or {}).get('meaning') in KNOWN_PRICE
              and ((d.get('facts') or {}).get('price') or {}).get('value_rub')]
    if len(prices) >= 5:
        med = statistics.median(prices)
        out.append(f'Медиана названной цены покупки в отрасли за три года: {_money(med)} ({len(prices)} сделок).')
    return out


def _money(rub: float) -> str:
    import price_estimate
    return price_estimate.money(rub)


def facts_text(deal: dict, deals: dict, name_of) -> str:
    card = [f'Сделка: {deal.get("title")}',
            f'Дата: {deal.get("date") or "не указана"}; статус: {deal.get("status") or "не указан"}; '
            f'тип: {deal.get("type") or "—"}; отрасль: {deal.get("ind") or "не определена"}']
    if deal.get('buyer'):
        card.append(f'Покупатель: {name_of(deal["buyer"]) or deal["buyer"]}')
    if deal.get('seller'):
        card.append(f'Продавец: {deal["seller"]}')
    for label, path in CARD_FIELDS:
        v = _get(deal, path)
        if v:
            card.append(f'{label}: {v[:1500]}')
    adv = _advisors(deal)
    if adv:
        card.append(f'Консультанты: {adv[:600]}')
    base = []
    for role, pid in (('покупателя', deal.get('buyer')), ('продавца', deal.get('seller_id')),
                      ('покупаемой компании', deal.get('target'))):
        other = _party_deals(deal, deals, pid)
        if other:
            base.append(f'Другие сделки {role}:')
            base += [f'— {str(d.get("date") or "")[:10]}: {d.get("title")} '
                     f'({d.get("status") or "статус не указан"}; сумма: {d.get("sum") or "не раскрыта"})' for d in other]
    base += industry_lines(deal, deals, name_of)
    return ('КАРТОЧКА (читатель это уже видит):\n' + '\n'.join(card)
            + '\n\nИЗ БАЗЫ КОМПАСА (на карточке этого нет):\n' + ('\n'.join(base) or 'ничего'))


SYSTEM = (
    'Ты — аналитик сервиса «Компас» о сделках M&A в России. Читатель уже видит карточку сделки; '
    'ему нужен разбор, которого в карточке нет. Сводка ниже из двух частей. КАРТОЧКА — то, что '
    'читатель уже видит: не пересказывай ее (стороны, сумму, консультантов, цель, контекст, '
    'показатели) — она нужна тебе, чтобы понять сделку. ИЗ БАЗЫ КОМПАСА — то, чего на карточке нет: '
    'строй разбор на этом. До четырех коротких абзацев через пустую строку, каждый начинается ровно '
    'с этих слов, и только если по нему есть что добавить: «Для покупателя.» — как сделка вписывается '
    'в другие сделки покупателя, какая линия видна; «Для продавца.» — только если в базе есть другие '
    'сделки продавца, иначе этот абзац не пиши; «Рынок вокруг.» — что происходит в отрасли, только '
    'цифрами из базы, без оценок вроде «консолидация» или «бум»; «Что может быть дальше.» — осторожное '
    'предположение, прямо названное предположением. Каждый абзац — 1–2 предложения. Числа бери только '
    'из части ИЗ БАЗЫ КОМПАСА: цифры карточки (доли, выручку, цели) не повторяй. Не приписывай сторонам '
    'выгоды, мотивы и ожидания, которых нет в сводке. '
    'Никаких фактов и чисел, которых нет в сводке; все числа — цифрами и ровно как в сводке; не '
    'досчитывай доли, проценты и разы. По-русски, просто и по-деловому, без markdown, списков, '
    'заголовков, эффектных метафор и инвестиционных советов. Не оценивай людей и не обвиняй никого.'
)


def base_part(facts: str) -> str:
    """Только часть ИЗ БАЗЫ: числа разбора сверяются с ней, и цифра, взятая из
    карточки (доля продавца, выручка), выпадает вместе с предложением — так
    разбор механически не пересказывает карточку (владелец, 26 октября 2026)."""
    return facts.split('ИЗ БАЗЫ КОМПАСА', 1)[-1]


def split_answer(text: str) -> list[dict]:
    import re
    out = []
    for p in [p.strip() for p in re.split(r'\n\s*\n', text or '') if p.strip()]:
        lead = next((l for l in LEADS if p.startswith(l)), '')
        body = p[len(lead):].strip()
        if body:
            out.append({'lead': lead, 'text': body})
    return out
