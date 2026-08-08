#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Заголовки трёх карточек последнего притока (4–6 августа) нарушают правила
именования новых карточек (CLAUDE.md, «Правила именования новых карточек —
мягкие, и только для новых»; PRODUCT_ROADMAP.md, G3).

ЗАМЕР (8 августа). Из 16 карточек, реально добавленных притоком за 4–6
августа (не считая переноса архива 3 августа), два класса нарушений:

1. Прямые кавычки вместо «ёлочек» — та же болезнь, что чинил
   `fix_straight_quotes.py` 2 августа (12 карточек), в новых карточках снова:
   g6d73538c («"Основа"», «"Свиблово"») и g8827d795 («"Лукойла"»). Проект
   последовательно использует «Основа», «Свиблово», «Лукойл» — разнобой виден
   рядом с любой другой карточкой на той же ленте.
2. Генерик вместо узнаваемого имени — g80f18d3d: `buyer_name`
   «Знаменитый российский производитель электроники» ничего не называет,
   хотя источник (событие карточки, уже дозабранное приточным текстом) прямо
   говорит: «Владелец крупнейшего российского производителя серверов Yadro
   приобрел складское помещение…» — узнаваемый бренд «Yadro» уже лежит в
   `events[0].note` этой же карточки. Само правило именования запрещает
   именно это: «вместо „крупнейший производитель X" — настоящее имя из
   статьи». Персону-владельца источник по имени не называет — записываем
   «Владелец Yadro», а не выдумываем имя человека.

Дословность проверена по своим же данным (`events[0].note`), не по свежему
поиску: это не новый факт, а перенос уже стоящего в карточке имени в поле,
которое показывается на экране (тот же класс правки, что «факт лежит не в
своём поле» в CLAUDE.md).

Запуск:
    python3 pipeline/fix_new_card_titles_batch3.py            # сухой прогон
    python3 pipeline/fix_new_card_titles_batch3.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> список (поле, было, стало). Поле поддерживает точку для
# вложенного словаря (eco.rationale) — party_evidence правится отдельно ниже,
# у него список словарей, а не плоский словарь.
FIXES = {
    'g6d73538c': [
        ('title', '"Основа" приобрела 5 гектаров земли в бывшей промзоне "Свиблово" в Москве',
                   '«Основа» приобрела 5 гектаров земли в бывшей промзоне «Свиблово» в Москве'),
        ('buyer_name', '"Основа"', '«Основа»'),
        ('asset', '5 гектаров земли в бывшей промзоне "Свиблово" в Москве',
                  '5 гектаров земли в бывшей промзоне «Свиблово» в Москве'),
    ],
    'g8827d795': [
        ('title', 'Бывший топ-менеджер "Лукойла" приобрел старинную усадьбу в Москве',
                  'Бывший топ-менеджер «Лукойла» приобрел старинную усадьбу в Москве'),
    ],
    'g80f18d3d': [
        ('title', 'Знаменитый российский производитель электроники купил склад на границе с Китаем',
                  'Владелец Yadro купил склад на границе с Китаем'),
        ('buyer_name', 'Знаменитый российский производитель электроники', 'Владелец Yadro'),
    ],
}

# id сделки -> список (роль в party_evidence, было, стало). Значение внутри
# party_evidence дублирует то же поле карточки и правится тем же текстом.
EVIDENCE_FIXES = {
    'g6d73538c': [
        ('buyer', '"Основа"', '«Основа»'),
        ('target', '5 гектаров земли в бывшей промзоне "Свиблово" в Москве',
                   '5 гектаров земли в бывшей промзоне «Свиблово» в Москве'),
    ],
    'g80f18d3d': [
        ('buyer', 'Знаменитый российский производитель электроники', 'Владелец Yadro'),
    ],
}
# g80f18d3d: значение переносится из своего же текста, а не с чужих слов —
# метод правки честнее назвать human_review, как у соседней карточки g8827d795
# (там таким же образом переносили «Рид Ойл» из текста в buyer_name).
EVIDENCE_METHOD_FIXES = {
    ('g80f18d3d', 'buyer'): 'human_review',
}


def _get(deal, field):
    if '.' in field:
        block, sub = field.split('.', 1)
        return (deal.get(block) or {}).get(sub)
    return deal.get(field)


def _set(deal, field, value):
    if '.' in field:
        block, sub = field.split('.', 1)
        deal[block][sub] = value
    else:
        deal[field] = value


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for deal_id, fixes in FIXES.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        for field, old, new in fixes:
            current = _get(deal, field)
            assert current is not None and old in current, \
                '%s.%s: подстрока не найдена дословно: %r' % (deal_id, field, old[:80])
            assert current.count(old) == 1, '%s.%s: подстрока встречается не один раз' % (deal_id, field)
            plan.append((deal_id, field, old, new))

    ev_plan = []
    for deal_id, fixes in EVIDENCE_FIXES.items():
        deal = by_id[deal_id]
        pe = deal.get('party_evidence') or {}
        for role, old, new in fixes:
            entries = pe.get(role) or []
            assert entries, '%s: party_evidence.%s пуст' % (deal_id, role)
            entry = entries[0]
            assert entry.get('value') == old, \
                '%s.party_evidence.%s: значение не совпадает дословно: %r' % (deal_id, role, entry.get('value'))
            ev_plan.append((deal_id, role, old, new))

    print('Карточек с правкой заголовка/полей: %d (%d замен)' % (len(FIXES), len(plan)))
    for deal_id, field, old, new in plan:
        print('  %-12s %-12s %r -> %r' % (deal_id, field, old, new))
    print('Правок в party_evidence: %d' % len(ev_plan))
    for deal_id, role, old, new in ev_plan:
        print('  %-12s %-8s %r -> %r' % (deal_id, role, old, new))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, field, old, new in plan:
        deal = by_id[deal_id]
        current = _get(deal, field)
        _set(deal, field, current.replace(old, new, 1))
    for deal_id, role, old, new in ev_plan:
        deal = by_id[deal_id]
        entry = deal['party_evidence'][role][0]
        entry['value'] = new
        method = EVIDENCE_METHOD_FIXES.get((deal_id, role))
        if method:
            entry['method'] = method

    for deal_id, field, old, new in plan:
        assert new in _get(by_id[deal_id], field), '%s.%s: новое значение не записалось' % (deal_id, field)
    for deal_id, role, old, new in ev_plan:
        assert by_id[deal_id]['party_evidence'][role][0]['value'] == new, \
            '%s.party_evidence.%s: новое значение не записалось' % (deal_id, role)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d замен в карточках, %d в party_evidence.' % (len(plan), len(ev_plan)))


if __name__ == '__main__':
    main('--write' in sys.argv)
