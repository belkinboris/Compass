# -*- coding: utf-8 -*-
"""Разовая часть вычитки 12 ноября 2026 (марафон, партия m022): то, что не ложится в таблицу FIXES.

- суммы: оценки аналитиков и ориентир объема IPO стояли ценой сделки (gb3211ae8, g7b4be1c4) — «Не раскрыта»;
  у птицефабрики «Кинешемская» (g7ce0250d) ценой стояла оценка EV 1,5 млрд ₽, а цена по собеседнику
  «Коммерсанта» — 400–450 млн ₽ (review.py не принимает «Не раскрыта» и «≈»);
- продавец «Русала» (ga58eb450) — группы Pioneer и KCap по раскрытию UC RUSAL на HKEX 14.03.2025
  (продавец текстом: у иностранных групп профиля нет); основание даты 15 августа — день, когда «Русал»
  сообщил о завершении первого этапа (Интерфакс, 15.08.2025);
- профиль покупателя g4233e198: «100%-ная структура АФК «Система»» — неверно: АО «Корпорация Роботов»
  создано и принадлежит АО «Элемент» (CNews, OpenSanctions по ЕГРЮЛ);
- где искали продавца «Эйдос Робототехники» (g57a44f07).

    python3 pipeline/archive/2026-11/reread_oneoff_m022.py           # сухо
    python3 pipeline/archive/2026-11/reread_oneoff_m022.py --write   # запись; повторный запуск — «уже применено»
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread_oneoff_m022 (вычитка 12.11.2026)'

# (id, поле, старое, новое, цитата, адрес)
_SET = [
    ('gb3211ae8', 'sum', '≈5 млрд ₽', 'Не раскрыта',
     'Объем размещения пока окончательно не определен. По словам одного из источников издания, «размер IPO может '
     'быть определен на уровне средних величин сделок IPO за 2023–2024 годы, составивших порядка 5 млрд руб.».',
     'https://expert.ru/news/rbk-uznal-o-planakh-gruppy-vis-provesti-ipo-do-kontsa-goda/'),
    ('gb3211ae8', 'eco.sum', '≈5 млрд ₽', 'Не раскрыта', None, None),
    ('g7b4be1c4', 'sum', '6–7 млрд ₽ (или 9,4–9,5 млрд ₽ по другой оценке)', 'Не раскрыта',
     'Гендиректор «Infoline-аналитики» Михаил Бурмистров оценивает стоимость доли Туголукова в «Медскане» в 6–7 '
     'млрд рублей .',
     'https://iz.ru/1950983/denis-kuznetcov/klinicheskij-sluchaj-farmstandart-mozhet-vyjti-na-rynok-meduslug'),
    ('g7b4be1c4', 'eco.sum', '6–7 млрд ₽ (или 9,4–9,5 млрд ₽ по другой оценке)', 'Не раскрыта', None, None),
    ('g7ce0250d', 'sum', '≈1,5 млрд ₽ (по оценке)', '400–450 млн ₽',
     'Собеседник “Ъ” на аграрном рынке говорит, что стороны сторговались на 400–450 млн руб. из-заплохой '
     'рыночной конъюнктуры.', 'https://www.kommersant.ru/doc/7990349'),
    ('g7ce0250d', 'eco.sum', '≈1,5 млрд ₽ (по оценке)', '400–450 млн ₽', None, None),
    ('g7ce0250d', 'sum_basis', None, 'reported', None, None),
    ('ga58eb450', 'seller', None, 'группа Pioneer и группа KCap',
     'a wholly-owned subsidiary of the Company (the “ Purchaser ”) entered into the agreement with Pioneer group '
     'of companies and KCap group of companies',
     'https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0314/2025031401973.pdf'),
    ('ga58eb450', 'date_basis', None, 'announcement', None, None),
]

_RETRACT = [
    ('gb3211ae8', 'sum', '≈5 млрд ₽'),
    ('g7b4be1c4', 'sum', '6–7 млрд ₽ (или 9,4–9,5 млрд ₽ по другой оценке)'),
    ('g7ce0250d', 'sum', '≈1,5 млрд ₽ (по оценке)'),
]

_PROFILE = [
    ('g4233e198', 'desc', '100%-ная структура АФК «Система»; ', 'Структура группы «Элемент»; '),
]

# Имя с правовой формой по ЕГРЮЛ (досье партии: АО "КОРПОРАЦИЯ РОБОТОТЕХНИКИ" ИНН 9703208270;
# ГРУППА "ВИС" (АО) ИНН 7728355650) — party_legal_names.py в прогоне 12.11 реестра не достал / формы не вывел.
_LEGAL = [
    ('g4233e198', 'АО «Корпорация Робототехники»'),
    ('g40ce292b', 'АО «Группа «ВИС»»'),
]

_NOTES = {
    'g57a44f07': {
        'no_profile': {'seller': (
            'Продавец не назван: CNews, www1.ru и Business Gazeta (пересказ РБК) пишут только о покупке 51% акций '
            'АО «Эйдос Робототехника» «Корпорацией Роботов»; ООО «Эйдос-Робототехника» (ИНН 1655268265) по ЕГРЮЛ '
            'сменило участников в 2022 году, а в 2025-м — нет, поэтому кто из совладельцев продал акции АО, '
            'по открытым данным не видно.')},
        'searched': ['cnews.ru/news/line/2025-09-22_korporatsiya_robotovpriobrela',
                     'www1.ru/news/2025/09/24 (Элемент приобрел 51% акций «Эйдос Робототехника»)',
                     'business-gazeta.ru/news/683427 (пересказ РБК)',
                     'party_legal_names.py g57a44f07 (ЕГРЮЛ ООО «Эйдос-Робототехника»)',
                     'WebSearch: АО «Эйдос Робототехника» ИНН / ОГРН / акционеры',
                     'rbc.ru (статья не открылась: 401)']},
}


def _get(card, field):
    o = card
    for p in field.split('.'):
        o = o.get(p) if isinstance(o, dict) else None
    return o


def _set(card, field, value):
    parts = field.split('.')
    o = card
    for p in parts[:-1]:
        o = o.setdefault(p, {})
    o[parts[-1]] = value


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    n = 0
    for cid, field, old, new, quote, url in _SET:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if quote:
            fact_edit_guard.log(card, field, new, quote, url, BY)
            if field == 'sum':                       # eco.sum — то же значение, та же цитата
                fact_edit_guard.log(card, 'eco.sum', new, quote, url, BY)
        n += 1
    for cid, field, value in _RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            n += 1
    for comp, field, old, new in _PROFILE:
        c = data['companies'][comp]
        if old in (c.get(field) or ''):
            c[field] = c[field].replace(old, new)
            n += 1
        else:
            assert new in (c.get(field) or ''), (comp, c.get(field))
    for comp, short in _LEGAL:
        c = data['companies'][comp]
        if c.get('legal_short') != short:
            assert not c.get('legal_short'), (comp, c.get('legal_short'))
            c['legal_short'] = short
            n += 1
    for cid, notes in _NOTES.items():
        acc = deals[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            if acc.get(k) != v and not (isinstance(v, dict) and all(acc.get(k, {}).get(a) == b for a, b in v.items())):
                if isinstance(v, dict):
                    acc.setdefault(k, {}).update(v)
                else:
                    acc[k] = v
                n += 1
    return n


if __name__ == '__main__':
    data = json.load(open(DATA, encoding='utf-8'))
    n = apply(data)
    print('Изменений: %d' % n if n else 'Уже применено.')
    if '--write' in sys.argv and n:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(fresh)
        json.dump(fresh, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    elif '--write' not in sys.argv:
        print('Сухой прогон. Запись — с ключом --write.')
