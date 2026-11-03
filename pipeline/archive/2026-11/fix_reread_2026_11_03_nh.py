# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026, партия nh: правки, которых review.py не умеет.

Основания — в докстроке и записях `pipeline/ingest/fixes/reread_2026_11_03_nh.py`.

Даты (день события по реестру, а не объявление и не заглушка):
- ga80371a8 (Softline / «ОМЗ-ИТ»): 2024-07-01 — «1-е число» при «заключена в июле 2024 г.»
  (CNews) → 2024-08-07: по истории участников ЕГРЮЛ в этот день ООО «Инвестпроекты»
  (ООО «Софтлайн Проекты») вошло с 60%, доля АО «ААА Управление Капиталом» упала с 98,03% до 40%;
  основание registry.
- g075e9738 (VK / «Р7»): 2024-12-31 → 2024: в отчете VK только «в течение 2024 года»,
  31 декабря выдумано (docs/card_status_dates.md, «Нет дня — только год»).
- g9d6e9676 (фонд «Восход» / НДТ): 2025-04-10 (объявление) → 2025-01-21: по ЕГРЮЛ в этот день
  вошло ООО «УК Восход» с 40,7%, доля Т. Хихинашвили 100% → 59,3% (vc.ru: «через месяц» после
  28 декабря 2024 года); основание registry.

Прочее:
- legal_short профиля g4a281a8e «Ингосстрах» — СПАО «Ингосстрах» (реестр: СПАО "ИНГОССТРАХ",
  ИНН 7705042179); party_legal_names.py форму СПАО не знает.
- g075e9738 accepted_notes.no_profile.seller — где искали продавца.
- ga69530bc accepted_notes.no_profile.buyer — где искали покупателя.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nh.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nh.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DATES = [  # id, старая дата, новая дата, новое основание (None — не трогать)
    ('ga80371a8', '2024-07-01', '2024-08-07', 'registry'),
    ('g075e9738', '2024-12-31', '2024', None),
    ('g9d6e9676', '2025-04-10', '2025-01-21', 'registry'),
]

NO_PROFILE = [  # id, роль, где искали
    ('g075e9738', 'seller',
     'Продавец не раскрыт: VK, «Р7» и годовой отчет VK его не называют; по Ведомостям (14 февраля 2025) '
     'основатели Лев Баннов и Алексей Рязанов вышли из учредителей в 2021 году, на конец 2023 года '
     'акционеры — Артур Акопьян, Игорь Колпаков и АО «Технологии распределенных коммуникаций», доли не '
     'уточняются; «Р7» — АО, реестр акционеров в ЕГРЮЛ не ведется'),
    ('ga69530bc', 'buyer',
     'Покупатель не раскрыт: в пояснениях к отчетности ООО «Технологии и моторы» за 2024 год не указан '
     '(Интерфакс, АБН 24, 8 апреля 2025), S7 от комментариев отказалась; поиск по Коммерсанту, Infopro54 и '
     'новостям о БЭМЗ его не дал; БЭМЗ — АО, реестр акционеров в ЕГРЮЛ не ведется'),
]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0

    for did, old, new, basis in DATES:
        d = deals[did]
        assert d.get('date') == old, '%s: date %r, ожидали %r' % (did, d.get('date'), old)
        assert not any(e.get('date') == old for e in d.get('events') or []), '%s: этап с той же датой' % did
        d['date'] = new
        if basis:
            d['date_basis'] = basis
        print('%s date %s → %s%s' % (did, old, new, (' (%s)' % basis) if basis else ''))
        n += 1

    c = comps['g4a281a8e']
    assert c.get('name') == 'Ингосстрах' and c.get('legal_short') is None, c.get('legal_short')
    c['legal_short'] = 'СПАО «Ингосстрах»'
    print('g4a281a8e legal_short → СПАО «Ингосстрах»')
    n += 1

    for did, role, note in NO_PROFILE:
        d = deals[did]
        cur = ((d.get('accepted_notes') or {}).get('no_profile') or {}).get(role)
        assert cur is None, '%s: no_profile.%s уже %r' % (did, role, cur)
        d.setdefault('accepted_notes', {}).setdefault('no_profile', {})[role] = note
        print('%s accepted_notes.no_profile.%s' % (did, role))
        n += 1

    print('правок: %d' % n)
    if write:
        open(DATA, 'w', encoding='utf-8').write(
            json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('записано')
    else:
        print('Сухой прогон. Запись — --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
