# -*- coding: utf-8 -*-
"""Приток 17:20 МСК 9 октября 2026: Фонд НТИ (Национальная технологическая
инициатива) получил 3% в ООО «Спутникс» (космическая «дочка» АФК
«Система»/структур Владимира Евтушенкова) — изменения в ЕГРЮЛ внесены
7 октября, доля «ГК «Спутникс» (структуры Евтушенкова) сократилась с
75,04% до 72,04%. Источник — телеграм-канал «Русский Венчур», сам
ссылающийся на прямые данные ЕГРЮЛ (не на чужую статью) — первоисточник
здесь и есть реестр. Заголовок канала обрезан на полуслове — не
показываю как есть, формулирую сам. Ворота не распознали (нет «X продаёт
Y», только разбор долей по ЕГРЮЛ).

Запуск: python3 pipeline/build_sputniks_nti_2026_10_09.py [--write]
"""
import json
import sys

sys.path.insert(0, 'pipeline/ingest')
import promote  # noqa: E402

PENDING = 'static/data/pending.json'
URL = 'https://t.me/rusven/7781'

DRAFT = {
    'draft_id': 'd-sputniks-nti-2026-10-09',
    'title': 'Фонд НТИ получил 3% в космической «Спутникс» — доля структур Евтушенкова размыта',
    'date': '2026-10-07',
    'src': [['Телеграм-канал «Русский Венчур»', URL]],
    'sum': None,
    'type': 'Инвестиция',
    'status': 'Закрыта',
    'events': [],
    'buyer_name': 'Фонд НТИ',
    'asset': '3% ООО «Спутникс»',
    'seller': None,
    'parsed_parties': {'buyer': 'Фонд НТИ',
                        'asset': '3% ООО «Спутникс»',
                        'seller': None},
    'ind': 'Машиностроение',
    'needs_review': True,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    card['eco']['share'] = (
        '3% ООО «Спутникс» перешли Фонду НТИ; доля ООО «ГК «Спутникс» (структуры '
        'Владимира Евтушенкова, АФК «Система») сократилась с 75,04% до 72,04%. Среди '
        'остальных учредителей — Ирина Козловская (15,01%), Владислав Иваненко '
        '(6,95%), Станислав Карпенко (1,29%), Анатолий Копик (1,08%), Роман Жарких '
        '(0,63%).'
    )
    card['eco']['context'] = (
        'Изменения внесены в ЕГРЮЛ 7 октября. «Спутникс» занимается разработкой и '
        'производством спутниковых компонентов и технологий.'
    )
    card['themes'] = ['Инвестиция']
    card['pending_since'] = '2026-10-09T17:20:00+00:00'
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
