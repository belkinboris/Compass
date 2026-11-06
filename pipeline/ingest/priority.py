# -*- coding: utf-8 -*-
"""Важное — вне очереди (владелец, 6 ноября 2026: указ о JTI и оферта «Т-Технологий»
по «Циану» шли в общей очереди; «приоритизировать выпуск важных карточек надо, но
мимо консоли идти нельзя»).

Ничего не публикует и ничего не решает за людей: только помечает. Сырье с пометкой
уходит в консоль с «⚡ Важное» в первой строке (`send_drafts.raw_message`), а карточки
с пометкой стоят первыми в очереди приемки (`accept_card.queue`) — рутина притока
берет их раньше остальных. Решение «это сделка» и «опубликовать» по-прежнему за
людьми в консоли.

Признак считается заново при каждом вызове по заголовку и сумме, в карточку не
пишется: правило поменялось — пометки сразу новые, без миграции.
"""
import re

# Сделки, которые меняют рынок или отношения с государством.
STRONG = [
    (re.compile(r'\bуказ\w*|временн\w+\s+управлени\w*', re.I), 'указ или временное управление'),
    (re.compile(r'национализ\w*|в доход государства|иск\w* Генпрокуратур\w*', re.I), 'изъятие'),
    (re.compile(r'\bоферт\w*|выкуп\w*\s+до\s+100|до\s+100\s*%', re.I), 'оферта или выкуп до 100%'),
    (re.compile(r'контрольн\w+\s+пакет\w*|контроль\s+над|поглощ\w*|слияни\w*', re.I), 'смена контроля'),
    (re.compile(r'\bIPO\b|\bSPO\b|размещени\w+\s+акций', re.I), 'размещение акций'),
]
BIG_SUM = re.compile(r'(\d+(?:[.,]\d+)?)\s*(трлн|млрд)\s*(?:₽|руб|рублей)', re.I)
_BIG_NAMES = {}


def _big_names(base):
    """Компании с пятью и больше сделками в базе — «крупные из нашей базы»."""
    key = id(base)
    if key in _BIG_NAMES:
        return _BIG_NAMES[key]
    comps = base.get('companies') or {}
    count = {}
    for d in base.get('deals') or []:
        for role in ('buyer', 'target', 'seller_id'):
            cid = d.get(role)
            if cid in comps:
                count[cid] = count.get(cid, 0) + 1
    names = []
    for cid, n in count.items():
        name = re.sub(r'[«»"]', '', comps[cid].get('name') or '').strip()
        if n >= 5 and 4 <= len(name) <= 40 and not re.search(r'\s{2}|[()]', name):
            names.append(name)
    _BIG_NAMES.clear()
    _BIG_NAMES[key] = names
    return names


def reason(title, sum_text='', base=None):
    """Почему важное (строка) или None."""
    t = str(title or '')
    for rx, why in STRONG:
        if rx.search(t):
            return why
    m = BIG_SUM.search(t + ' ' + str(sum_text or ''))
    if m:
        value = float(m.group(1).replace(',', '.'))
        if m.group(2).lower() == 'трлн' or value >= 1:
            return 'сумма от 1 млрд ₽'
    if base:
        low = t.lower()
        for name in _big_names(base):
            if re.search(r'(?<![\wА-Яа-яЁё])' + re.escape(name.lower()) + r'(?![\wА-Яа-яЁё])', low):
                return 'крупная компания из базы: %s' % name
    return None
