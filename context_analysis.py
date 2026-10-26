"""«Анализ ассистента» у блока «Контекст» на карточке сделки.

Идея партнёра владельца (Артём), макет показан владельцу 25 октября 2026,
решение «внедри» — 26 октября 2026: кнопка у «Контекста» → текст мерцает,
пока ассистент читает → рядом (компьютер) или снизу (телефон) — короткий
разбор: что сделка значит, масштаб, что может быть дальше.

Что видит модель — только сводка `facts_text`: поля карточки и другие сделки
тех же сторон из базы. Числа ответа сверяются со сводкой
(`price_estimate.numbers_ok`): число не из сводки — ответа нет. Шаблонного
текста здесь не бывает: разбор без модели был бы пересказом карточки.
"""
from __future__ import annotations

FIELDS = (
    ('Цель сделки', ('eco', 'rationale')),
    ('Контекст', ('eco', 'context')),
    ('Показатели актива', ('eco', 'target_fin')),
    ('Сумма', ('sum',)),
    ('Предмет / доля', ('eco', 'share')),
    ('Оценка и дисконт', ('eco', 'val')),
    ('Как устроена сделка', ('law', 'struct')),
    ('Дополнительно', ('extra',)),
)
OTHER_DEALS_MAX = 8


def _get(d: dict, path: tuple) -> str:
    v = d
    for k in path:
        v = v.get(k) if isinstance(v, dict) else None
    s = str(v or '').strip()
    return '' if s in ('—', '-') else s


def _party_deals(deal: dict, deals: dict[str, dict], party_id: str | None) -> list[dict]:
    if not party_id:
        return []
    out = []
    for cid, d in deals.items():
        if cid == deal.get('id'):
            continue
        if party_id in (d.get('buyer'), d.get('seller_id'), d.get('target'), d.get('asset_id')):
            out.append(dict(d, id=cid))
    out.sort(key=lambda d: str(d.get('date') or ''), reverse=True)
    return out[:OTHER_DEALS_MAX]


def facts_text(deal: dict, deals: dict[str, dict], name_of) -> str:
    lines = [f'Сделка: {deal.get("title")}',
             f'Дата: {deal.get("date") or "не указана"}; статус: {deal.get("status") or "не указан"}; '
             f'тип: {deal.get("type") or "—"}; отрасль: {deal.get("ind") or "не определена"}']
    buyer = deal.get('buyer')
    seller = deal.get('seller_id')
    if buyer:
        lines.append(f'Покупатель: {name_of(buyer) or buyer}')
    if deal.get('seller'):
        lines.append(f'Продавец: {deal["seller"]}')
    for label, path in FIELDS:
        v = _get(deal, path)
        if v:
            lines.append(f'{label}: {v[:1500]}')
    for role, pid in (('покупателя', buyer), ('продавца', seller), ('покупаемой компании', deal.get('target'))):
        other = _party_deals(deal, deals, pid)
        if other:
            lines.append(f'Другие сделки {role} в базе Компаса:')
            for d in other:
                lines.append(f'— {str(d.get("date") or "")[:10]}: {d.get("title")} '
                             f'({d.get("status") or "статус не указан"}; сумма: {d.get("sum") or "не раскрыта"})')
    return '\n'.join(lines)


def has_context(deal: dict) -> bool:
    return bool(_get(deal, ('eco', 'context')))


LEADS = ('Что это значит.', 'Масштаб.', 'Что может быть дальше.')

SYSTEM = (
    'Ты — аналитик сервиса «Компас» о сделках M&A в России. Читатель открыл карточку сделки и просит '
    'короткий разбор. Пиши только по сводке ниже: никаких фактов и чисел, которых в ней нет. '
    'Три коротких абзаца через пустую строку, каждый начинается ровно с этих слов: '
    '«Что это значит.» — зачем сделка покупателю и как она вписывается в его другие сделки из сводки; '
    '«Масштаб.» — насколько сделка велика для сторон, только по числам из сводки (если чисел нет — '
    'скажи, что масштаб по открытым данным оценить нельзя); '
    '«Что может быть дальше.» — осторожное предположение, прямо названное предположением. '
    'Каждый абзац — 1–3 предложения. По-русски, просто и по-деловому, как аналитик объяснял бы партнёру '
    'вслух: без markdown, списков, заголовков, эффектных метафор и инвестиционных советов. '
    'Не оценивай людей и не обвиняй никого.'
)


def split_answer(text: str) -> list[dict]:
    """Абзацы с выделенным началом: [{'lead': 'Масштаб.', 'text': '…'}]."""
    import re
    out = []
    for p in [p.strip() for p in re.split(r'\n\s*\n', text or '') if p.strip()]:
        lead = next((l for l in LEADS if p.startswith(l)), '')
        out.append({'lead': lead, 'text': p[len(lead):].strip()})
    return out

