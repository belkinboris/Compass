# -*- coding: utf-8 -*-
"""Заметка 494 (консоль, 4 сентября 2026): «Делаем отдельную карточку
про сделку 2024 года и её можно обогатить дополнительной инфой про
2019», отвечая на карточку `g94dcc5cc» («Газпром может приобрести до
40% Aurus»).

`extra» карточки `g94dcc5cc» уже нёс факт: контрольный пакет 51%,
который «Газпром Тех» купил летом 2025 года, собран из доли ФГУП «НАМИ»
и ВСЕЙ доли, которая с 2019 года принадлежала арабскому фонду Tawazun, а
в декабре 2024 года перешла российской компании «Дедал» (бенефициар не
установлен). Владелец попросил отдельную карточку про сделку 2024 года
(переход доли Tawazun к «Дедалу»), обогащённую историей входа Tawazun
в 2019 году.

2019 год перепроверен прямым чтением (РИА Новости,
ria.ru/20190218/1551034824.html, 18.02.2019): фонд Tawazun (ОАЭ)
получил 36% акций Aurus, вложив 110 млн евро; соглашение подписано в
Абу-Даби на выставке IDEX-2019.

Переход доли к «Дедалу» в декабре 2024 года — по докладу саб-агента
(агрегированные результаты поиска), первоисточник напрямую не читался в
этой сессии; сумма и точная дата сделки 2024 года не установлены.

Запуск: python3 pipeline/fix_add_aurus_tawazun_dedal_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g04edfc17'
TAWAZUN_ID = 'gtawazunfund'
DEDAL_ID = 'gdedalru'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert TAWAZUN_ID not in data['companies']
    assert DEDAL_ID not in data['companies']
    assert data['companies'].get('gf4733fef', {}).get('name'), 'нет профиля Aurus'

    data['companies'][TAWAZUN_ID] = {
        'name': 'Tawazun',
        'ind': 'Автопром',
        'desc': ('Инвестиционный фонд ОАЭ; в феврале 2019 года получил 36% '
                 'акций Aurus, вложив 110 млн евро. В декабре 2024 года '
                 'долю передал российской компании «Дедал».'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    data['companies'][DEDAL_ID] = {
        'name': '«Дедал»',
        'ind': 'Автопром',
        'desc': ('Российская компания; в декабре 2024 года получила долю '
                 'Tawazun в Aurus (36%). Бенефициар не установлен.'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2024',
        'title': '«Дедал» получил долю Tawazun (36%) в Aurus',
        'ind': 'Автопром',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/8211090'],
                ['РИА Новости', 'https://ria.ru/20190218/1551034824.html']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = DEDAL_ID
    card['seller_id'] = TAWAZUN_ID
    card['target'] = 'gf4733fef'
    card['eco']['context'] = (
        'Фонд Tawazun (ОАЭ) получил 36% акций Aurus в феврале 2019 года, '
        'вложив 110 млн евро; соглашение подписано в Абу-Даби на выставке '
        'IDEX-2019. В декабре 2024 года эта доля перешла к российской '
        'компании «Дедал» — её бенефициар не установлен. Летом 2025 года '
        'именно эта доля вместе с частью пакета ФГУП «НАМИ» вошла в '
        'контрольные 51% Aurus, которые купила «Газпром Тех» (отдельная '
        'карточка g94dcc5cc).'
    )

    data['deals'].append(card)
    print(f'Добавлена карточка {NEW_ID}: {card["title"]}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
