# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партия nd): то, что review.py не умеет.

1. РОЛИ g4e9e15a6 («Беринг Металс» / Кун-Манье): профиль покупателя «Беринг Металс»
   (g870d935d, ООО «Беринг Металс», ИНН 9703077116; в реестре владельцы — МК ООО «Хорвик» 99,9% и
   Свиблов 0,1%) стоял ПРЕДМЕТОМ (target), покупатель был пуст. По объявлению Amur Minerals о
   закрытии (FCA NSM 4695320, 6 марта 2023): «Bering Metals LLC is a Russian incorporated company
   controlled by Vladislav Sviblov», продано «100% of its interest in Irosta's wholly owned
   subsidiary, AO Kun-Manie». Профиль переезжает в buyer, target пустеет; предмет текстом
   «АО «Кун-Манье»» ставит запись FIXES партии nd. Описание профиля говорило «Владеет …
   проектом Кун-Манье» — это описание предмета, а не покупателя, переписано.
2. ДАТЫ без дня (docs/card_status_dates.md, «Нет дня — только год»):
   - gf174262b (Де-Мондерик / «Лаборатория Касперского»): 2022-07-01 — выдуманное 1-е число;
     статьи: «появились в британском реестре юрлиц в июле 2022 года», «в июле 2022 года
     заключил соглашение» — дня нет → '2022'.
   - g6d74bc39 (доля Shell в «Сахалине-2»): 2023-04-11 — день распоряжения о продаже НОВАТЭКу,
     которое в марте 2024 года признано утратившим силу (Интерфакс 952407). Доля перешла ООО
     «Сахалинский проект» группы «Газпром»: «"Газпром" в марте купил 27,5% в ООО "Сахалинская
     энергия"» (обновление той же заметки, 25.03.2024), «перешла структуре «Газпрома»»
     (Коммерсантъ 7604250); дня перехода нет → '2024'.
3. LEGAL_SHORT (находки приемки party_legal_form) — по реестру из досье и
   party_legal_names.py: «Беринг Металс» → ООО «Беринг Металс»; «Лаборатория Касперского» →
   АО «Лаборатория Касперского»; «Сахалин-2» → ООО «Сахалинская энергия».
4. DESC профиля «Сахалин-2» (g152f9c1d): «в 2023 году долю Shell выкупил «Газпром»» — год
   неверный (2024), и пост брал описание действия вместо предмета (находка post).

После записи — python3 pipeline/facts_derive.py --write.

    python3 <этот файл>            # сухой прогон
    python3 <этот файл> --write    # записать (из корня репозитория, после review.py --write)
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

DATES = [  # id, старая дата, новая
    ('gf174262b', '2022-07-01', '2022'),
    ('g6d74bc39', '2023-04-11', '2024'),
]
ROLES = [  # id, поле, старое, новое
    ('g4e9e15a6', 'buyer', None, 'g870d935d'),
    ('g4e9e15a6', 'target', 'g870d935d', None),
]
LEGAL = [  # профиль, имя (для сверки), legal_short
    ('g870d935d', 'Беринг Металс', 'ООО «Беринг Металс»'),
    ('g623b934f', 'Лаборатория Касперского', 'АО «Лаборатория Касперского»'),
    ('g152f9c1d', 'Сахалин-2', 'ООО «Сахалинская энергия»'),
]
DESC = [
    ('g870d935d',
     'Владеет никелево-медно-сульфидным проектом Кун-Манье; в 2023 году структура Владислава Свиблова '
     'купила его у Amur Minerals Corporation за $35 млн.',
     'Компания Владислава Свиблова; в 2023 году купила у Amur Minerals АО «Кун-Манье» — владельца '
     'лицензии на никелево-медное месторождение в Амурской области.'),
    ('g152f9c1d',
     'Проект добычи и экспорта СПГ на Сахалине; в 2023 году долю Shell (27,5%) выкупил «Газпром» за 94,8 млрд ₽.',
     'Оператор проекта «Сахалин-2» на шельфе Сахалина: добыча нефти и газа и завод СПГ.'),
]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for did, old, new in DATES:
        d = deals[did]
        assert d.get('date') in (old, new), '%s: дата уже %r, ожидали %r' % (did, d.get('date'), old)
        assert not any(e.get('date') == old for e in d.get('events') or []), did
        if d['date'] != new:
            print('%s: date %s -> %s' % (did, old, new))
            d['date'] = new
    for did, field, old, new in ROLES:
        d = deals[did]
        assert d.get(field) in (old, new), '%s: %s уже %r, ожидали %r' % (did, field, d.get(field), old)
        if d.get(field) != new:
            print('%s: %s %r -> %r' % (did, field, old, new))
            d[field] = new
    for cid, name, legal in LEGAL:
        p = comps[cid]
        assert p.get('name') == name, '%s: имя %r' % (cid, p.get('name'))
        assert p.get('legal_short') in (None, legal), '%s: legal_short уже %r' % (cid, p.get('legal_short'))
        if p.get('legal_short') != legal:
            print('%s: legal_short -> %s' % (cid, legal))
            p['legal_short'] = legal
    for cid, old, new in DESC:
        p = comps[cid]
        assert p.get('desc') in (old, new), '%s: desc %r' % (cid, p.get('desc'))
        if p['desc'] != new:
            print('%s: desc -> %s' % (cid, new))
            p['desc'] = new
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
