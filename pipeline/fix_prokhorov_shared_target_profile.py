# -*- coding: utf-8 -*-
"""«Продажа Михаилом Прохоровым» — один профиль на ДВЕ несвязанные сделки.

ЧТО СЛОМАНО. Последний, отложенный случай из группы «имя профиля —
глагол сделки» (`fix_deal_composition_company_names.py`,
`fix_investment_target_names.py`): профиль `g9f76045c` служил `target`
СРАЗУ у двух сделок без ничего общего, кроме случайного совпадения
заголовков на «Продажа X»:

* `ge42fa8fc` — Михаил Прохоров продал 51% акций Brooklyn Nets и
  Barclays Center Джозефу Цаю (2019).
* `gb944ce5d` — семейный траст Rigi Trust ОЛЕГА ТИНЬКОВА продал 5,3%
  ГДР TCS Group (2020) — к Прохорову эта сделка отношения не имеет
  вовсе, продавец другой человек и предмет другой.

Прошлые два прогона чинили похожие случаи переименованием на месте, но
здесь так нельзя — у профиля два разных предмета, переименование в
любую сторону оставит вторую сделку с чужим именем.

ЧТО ДЕЛАЕТ. `g9f76045c` переименовывается в «Brooklyn Nets и Barclays
Center» (сделка `ge42fa8fc` продолжает на него ссылаться — id не
меняется, старые адреса не рвутся) и получает верную отрасль
(«Медиа» → «Развлечения»: баскетбольный клуб и арена, не медиа-актив).
Для TCS Group заводится НОВЫЙ профиль (`ga75f0f33`) — не слит с уже
существующим «Тинькофф» (`g6b8f7488`): «Тинькофф» описывает бренд
цифрового банка (нынешний «Т-Банк»), а TCS Group Holding — отдельное
юридическое лицо, публичный держатель ГДР, через которое торговался
пакет в этой сделке. Тот же принцип осторожности, что при находке
«Mail»/VK — переименование не заменяет слияние, когда неясно, тот же
это субъект или связанный, но другой. Сделка `gb944ce5d` перенаправлена
на новый профиль.

Запуск:
    python3 pipeline/fix_prokhorov_shared_target_profile.py            # сухой прогон
    python3 pipeline/fix_prokhorov_shared_target_profile.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

RENAME_ID = 'g9f76045c'
RENAME_OLD_NAME = 'Продажа Михаилом Прохоровым'
RENAME_NEW_NAME = 'Brooklyn Nets и Barclays Center'
RENAME_OLD_IND = 'Медиа'
RENAME_NEW_IND = 'Развлечения'
RENAME_DESC = ('Профессиональный баскетбольный клуб НБА и принадлежащая ему '
               'арена в Бруклине; в 2019 году контроль перешёл от Михаила '
               'Прохорова к Джозефу Цаю.')

NEW_ID = 'ga75f0f33'
NEW_NAME = 'TCS Group'
NEW_IND = 'Банки'
NEW_DESC = ('Кипрская холдинговая компания, публичный держатель ГДР '
            'группы «Тинькофф» (ныне Т-Банк); акции и депозитарные '
            'расписки торговались на Лондонской и Московской биржах.')

DEAL_STAYS_ID = 'ge42fa8fc'      # target остаётся RENAME_ID
DEAL_MOVES_ID = 'gb944ce5d'      # target переезжает на NEW_ID


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    c = companies.get(RENAME_ID)
    assert c, 'профиля %s нет в базе' % RENAME_ID
    assert c['name'] == RENAME_OLD_NAME, 'имя %s уже другое: %r' % (RENAME_ID, c['name'])
    assert c['ind'] == RENAME_OLD_IND, 'отрасль %s уже другая: %r' % (RENAME_ID, c['ind'])
    assert NEW_ID not in companies, 'id %s уже занят' % NEW_ID

    full_text_refs = sorted(d['id'] for d in deals if RENAME_ID in json.dumps(d, ensure_ascii=False))
    assert full_text_refs == sorted([DEAL_STAYS_ID, DEAL_MOVES_ID]), (
        'профиль %s встречается не в тех сделках: %r' % (RENAME_ID, full_text_refs))

    d_stays = next(d for d in deals if d['id'] == DEAL_STAYS_ID)
    d_moves = next(d for d in deals if d['id'] == DEAL_MOVES_ID)
    assert d_stays['target'] == RENAME_ID, '%s.target уже другой' % DEAL_STAYS_ID
    assert d_moves['target'] == RENAME_ID, '%s.target уже другой' % DEAL_MOVES_ID

    print('ПЕРЕИМЕНОВЫВАЕМ  %s: %r -> %r (ind: %s -> %s)'
          % (RENAME_ID, RENAME_OLD_NAME, RENAME_NEW_NAME, RENAME_OLD_IND, RENAME_NEW_IND))
    print('СОЗДАЁМ  %s (%s), отрасль %s' % (NEW_ID, NEW_NAME, NEW_IND))
    print('ПЕРЕНАПРАВЛЯЕМ  target сделки %s -> %s' % (DEAL_MOVES_ID, NEW_ID))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    c['name'] = RENAME_NEW_NAME
    c['ind'] = RENAME_NEW_IND
    c['desc'] = RENAME_DESC
    data['match_keys'][RENAME_ID] = [RENAME_NEW_NAME.lower()]

    companies[NEW_ID] = {
        'name': NEW_NAME,
        'ind': NEW_IND,
        'desc': NEW_DESC,
        'kpi': ['Профиль', 'Автоматический'],
    }
    data['match_keys'][NEW_ID] = [NEW_NAME.lower()]

    d_moves['target'] = NEW_ID

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
