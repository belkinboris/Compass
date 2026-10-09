# -*- coding: utf-8 -*-
"""Приток 21:20 МСК 9 октября 2026: правительство Республики Коми выставило
на торги 100% акций региональной авиакомпании «Комиавиатранс» — с условием
сохранить авиасообщение (аэропорты Сыктывкара, Воркуты, Ухты, Усинска,
посадочные площадки в Печоре и Усть-Цильме) и не менее 1435 рабочих мест.
Цена и дата торгов источник не называет (ПРАЙМ со ссылкой на минимущество
Коми во «ВКонтакте»). Ворота не распознали (заголовок «власти выставили на
торги», а не явное «X продаёт Y»). Продавец — региональное правительство,
профиль не заводим (та же логика, что Роснедра, прецедент «Голдрупп»).

Запуск: python3 pipeline/build_komiaviatrans_2026_10_09.py [--write]
"""
import json
import sys

sys.path.insert(0, 'pipeline/ingest')
import promote  # noqa: E402

PENDING = 'static/data/pending.json'
URL = 'https://1prime.ru/20261009/vlasti-874128098.html'

DRAFT = {
    'draft_id': 'd-komiaviatrans-2026-10-09',
    'title': 'Власти Коми продают 100% авиакомпании «Комиавиатранс» с условием сохранить рейсы',
    'date': '2026-10-09',
    'src': [['ПРАЙМ', URL]],
    'sum': None,
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'events': [],
    'buyer_name': None,
    'asset': '100% акций авиакомпании «Комиавиатранс»',
    'seller': 'Правительство Республики Коми',
    'parsed_parties': {'buyer': None,
                        'asset': '100% акций авиакомпании «Комиавиатранс»',
                        'seller': 'Правительство Республики Коми'},
    'ind': 'Транспорт и логистика',
    'needs_review': True,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    card['eco']['context'] = (
        'Конкурс объявлен минимуществом Коми. Покупатель обязан сохранить транспортное '
        'назначение ключевых объектов — аэропортов Сыктывкара, Воркуты, Ухты и Усинска, а '
        'также посадочных площадок у Печоры и Усть-Цильмы — и не менее 1435 рабочих мест. '
        'Власти региона рассчитывают, что частный капитал поможет обновить здания, '
        'оборудование и взлётно-посадочные полосы; цену лота и срок подачи заявок источник '
        'не называет.'
    )
    card['themes'] = ['Продажа с торгов']
    card['pending_since'] = '2026-10-09T21:20:00+00:00'
    if not write:
        print('Сухой прогон. Карточка была бы: %s' % deal_id)
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return
    pending['cards'].append(card)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано: %s добавлена в pending.json' % deal_id)


if __name__ == '__main__':
    main('--write' in sys.argv)
