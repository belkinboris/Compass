# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партия dj): то, что review.py не умеет.

1. ДАТЫ без дня словами в статье или в другой год (docs/card_status_dates.md, «Дата»):
   - g9dd54742 (McDonald's → Говор): 2022-06-12 — день открытия «Вкусно — и точка», а не
     событие сделки. По ЕГРЮЛ (история участников ООО «Система ПБО», ИНН 7710044140,
     pipeline/party_legal_names.py): «2022-06-10 left: "МАКДОНАЛДС КОРПОРЕЙШН" (100.0 → None);
     2022-06-10 joined: ООО "КЛУБ ОТЕЛЬ" (None → 100.0)» → 2022-06-10, date_basis 'registry'.
   - gd4e555e3 (ЛУКОЙЛ-Коми / Лаявожнефтегаз): 2022-06-30 — день сообщения пресс-службы
     «Газпрома». По ЕГРЮЛ (ООО «ЛВНГ», ИНН 2983013832): «2022-06-27 share_changed: ООО "ГАЗПРОМ
     ДОБЫЧА КРАСНОДАР" (99.0 → 50.0); ООО "ЛУКОЙЛ-КОМИ" (1.0 → 50.0)» → 2022-06-27, 'registry'
     (AK&M 29.06.2022: «Такие данные содержит ЕГРЮЛ»).
   - g53ebfe72 («Новые утиные фермы» / «Донстар»): 2022-07-15 — день объявления торгов за
     2,1 млрд ₽, которые не состоялись (PROбанкротство 06.09.2022: «Никто не купил
     имущественный комплекс Донстара за 2,1 млрд рублей … признаны несостоявшимися»). Комплекс
     куплен на торгах 2024 года: «2.09.2024 Группа компаний "Дамате" выиграла торги … Цена
     предложения по лоту составила 1,282 млрд рублей» (пресс-релиз «Дамате»); Агроинвестор
     «2 сентября 2024». День протокола не назван → 2024-09-02, date_basis 'publication'
     (как у «Евродон-Юга», g7527482e, партия zb). Сумма и заголовок — записями FIXES партии dj.
2. RETRACTED: снятые суммы, чтобы enrich.py не вернул их с теми же статьями
   (docs/card_money.md, «После правки или снятия суммы»): g53ebfe72 «2,1 млрд ₽» (стартовая
   цена несостоявшихся торгов), g17d26389 «$25 млн» (предел оферты, выкуплено на $12,15 млн).
3. LEGAL_SHORT сторон (находки приемки party_legal_form). party_legal_names.py предлагает
   «АО «УК "группа Океан»» (сломанные кавычки и регистр), «ООО «ЛВНГ»» и «ООО «НУФ»» (краткие
   реестровые имена при полных «Лаявожнефтегаз» и «Новые утиные фермы») — поэтому вручную по
   полному наименованию из /api/companies/<id>/fns.
4. DESC профиля «Донстар» говорил «в 2022 году продан на банкротных торгах» — неверно (см. 1).

После записи — python3 pipeline/facts_derive.py --write.

    python3 <этот файл>            # сухой прогон
    python3 <этот файл> --write    # записать (из корня репозитория, после review.py --write)
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

DATES = [  # id, старая дата, новая, старый date_basis, новый
    ('g9dd54742', '2022-06-12', '2022-06-10', None, 'registry'),
    ('gd4e555e3', '2022-06-30', '2022-06-27', 'publication', 'registry'),
    ('g53ebfe72', '2022-07-15', '2024-09-02', None, 'publication'),
]
RETRACT = [('g53ebfe72', 'sum', '2,1 млрд ₽'), ('g17d26389', 'sum', '$25 млн')]
LEGAL = [  # профиль, имя (для сверки), legal_short
    ('g5dcb62e3', 'Группа Океан', 'АО «УК „Группа Океан“»'),
    ('g421d113d', "McDonald's Russia", 'ООО «Система ПБО»'),
    ('gba4833c4', 'ЛУКОЙЛ-Коми', 'ООО «ЛУКОЙЛ-Коми»'),
    ('gd7a80e0f', 'Газпром добыча Краснодар', 'ООО «Газпром добыча Краснодар»'),
    ('g84a097d5', 'Лаявожнефтегаз', 'ООО «Лаявожнефтегаз»'),
    ('g969877e1', 'Новые утиные фермы', 'ООО «Новые утиные фермы»'),
    ('g94365711', 'Донстар', 'ООО «Донстар»'),
]
DESC = [('g94365711',
         'Бывший крупнейший в России производитель мяса пекинской утки (агрохолдинг «Евродон»); '
         'в 2022 году продан на банкротных торгах.',
         'Бывший крупнейший в России производитель мяса пекинской утки (агрохолдинг «Евродон»); '
         'имущественный комплекс в Миллерово продан на банкротных торгах в 2024 году.')]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for did, old, new, old_b, new_b in DATES:
        d = deals[did]
        assert d.get('date') == old, '%s: дата уже %r, ожидали %r' % (did, d.get('date'), old)
        assert d.get('date_basis') == old_b, '%s: date_basis %r' % (did, d.get('date_basis'))
        assert not any(e.get('date') == old for e in d.get('events') or []), did
        print('%s: date %s -> %s, date_basis %s -> %s' % (did, old, new, old_b, new_b))
        d['date'], d['date_basis'] = new, new_b
    for did, field, val in RETRACT:
        d = deals[did]
        cur = d.get(field)
        if cur == val:
            assert not write, '%s: %s все еще %r — сначала review.py --write' % (did, field, cur)
            print('%s: %s все еще %r (сухой прогон до review.py --write)' % (did, field, cur))
        lst = d.setdefault('retracted', {}).setdefault(field, [])
        if val not in lst:
            lst.append(val)
            print('%s: retracted.%s += %r' % (did, field, val))
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
