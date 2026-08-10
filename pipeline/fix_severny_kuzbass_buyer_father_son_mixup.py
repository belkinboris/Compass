# -*- coding: utf-8 -*-
"""У карточки `g1a58d740` («Талтэк продаёт «Северный Кузбасс»») покупателем
был назван «Михаил Лупий, генеральный директор АО «СУЭК-Кузбасс»» — и
заголовок карточки утверждал, что покупатель — сама компания
«СУЭК-Кузбасс». Источник карточки (kommersant.ru/doc/5951599, уже
привязан) называет покупателем «кемеровского предпринимателя Станислава
Лупия» и ни разу не упоминает СУЭК-Кузбасс вовсе.

Живой поиск (WebSearch) объяснил путаницу: Михаил Лупий и Станислав
(Михайлович) Лупий — РАЗНЫЕ люди, отец и сын. Михаил Лупий действительно
гендиректор СУЭК-Кузбасс (с 4 октября 2022 года) — но это не имеет
отношения к покупке «Северного Кузбасса». Покупатель актива — его сын,
предприниматель Станислав Лупий (после сделки — гендиректор самой
«Угольной компании «Северный Кузбасс»», по данным Компромат.ру и
ЕГРЮЛ-агрегаторов). Компактный импорт спутал отца с сыном и заодно
приписал сделку не тому юрлицу.

Профиль-покупатель `g064aec42` («Михаил Лупия» — имя ещё и стояло в
косвенном падеже) используется только этой одной карточкой (проверено:
других сделок с этим buyer_id в базе нет) — переименование безопасно, не
затронет чужие карточки.

Запуск: python3 pipeline/fix_severny_kuzbass_buyer_father_son_mixup.py
        python3 pipeline/fix_severny_kuzbass_buyer_father_son_mixup.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g1a58d740'
BUYER_ID = 'g064aec42'

OLD_TITLE = ('Группа «Талтэк» продает АО «Угольная компания «Северный '
             'Кузбасс»» компании СУЭК-Кузбасс')
NEW_TITLE = ('Группа «Талтэк» продает АО «Угольная компания «Северный '
             'Кузбасс»» предпринимателю Станиславу Лупию')

OLD_RATIONALE = (
    'Продажа АО «Угольная компания «Северный Кузбасс»» (две шахты, '
    'углеобогатительная фабрика, погрузочно-транспортное управление) из '
    'портфеля Группы «Талтэк» покупателю Михаилу Лупию, генеральному '
    'директору АО «СУЭК-Кузбасс».'
)
NEW_RATIONALE = (
    'Продажа АО «Угольная компания «Северный Кузбасс»» (две шахты, '
    'углеобогатительная фабрика, погрузочно-транспортное управление) из '
    'портфеля Группы «Талтэк» покупателю Станиславу Лупию, кемеровскому '
    'предпринимателю, совладельцу нескольких предприятий, включая два '
    'золотодобывающих в Хабаровском крае и Кузбассе.'
)

OLD_BUYER_NAME = 'Михаил Лупия'
NEW_BUYER_NAME = 'Станислав Лупий'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    company = data['companies'][BUYER_ID]

    done = (card['title'] == NEW_TITLE and card['eco']['rationale'] == NEW_RATIONALE
            and card['extra'] == NEW_RATIONALE and company['name'] == NEW_BUYER_NAME)
    if done:
        print('УЖЕ ПРИМЕНЕНО')
        return

    assert card['title'] == OLD_TITLE, 'title уже другой'
    assert card['eco']['rationale'] == OLD_RATIONALE, 'eco.rationale уже другое'
    assert card['extra'] == OLD_RATIONALE, 'extra уже другое'
    assert company['name'] == OLD_BUYER_NAME, 'имя покупателя уже другое'
    assert sum(1 for d in data['deals'] if d.get('buyer') == BUYER_ID) == 1, (
        'профиль используется не только этой карточкой — переименование небезопасно')

    print('ПРАВИМ  %s title: покупатель назван верно (Станислав Лупий, не '
          'СУЭК-Кузбасс)' % CARD_ID)
    print('ПРАВИМ  %s eco.rationale/extra: отец и сын Лупий больше не '
          'спутаны' % CARD_ID)
    print('ПРАВИМ  %s (профиль покупателя): «%s» -> «%s»'
          % (BUYER_ID, OLD_BUYER_NAME, NEW_BUYER_NAME))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['title'] = NEW_TITLE
    card['eco']['rationale'] = NEW_RATIONALE
    card['extra'] = NEW_RATIONALE
    company['name'] = NEW_BUYER_NAME
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
