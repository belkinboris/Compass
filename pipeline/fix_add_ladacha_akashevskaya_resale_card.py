# -*- coding: utf-8 -*-
"""Заметка 490 (консоль, 4 сентября 2026): «Новая карточка», отвечая на
карточку `gb31c796f» (продажа базы отдыха «Ла дача Астрахань» Наталии
Дубовицкой, закрыта 1 сентября 2023 года).

`extra» карточки `gb31c796f» уже нёс факт следующей перепродажи (найден
при дочитывании месячной очереди, «Известные проблемы» CLAUDE.md,
проверено лично прямым WebFetch, Коммерсантъ/РИА Недвижимость/Lenta.ru):
через три недели, 11 октября 2023 года, актив перешёл к ООО
«Птицефабрика «Акашевская»», которым через «Марфининвест» владеет Мария
Лисицина — по неофициальным данным, представляет интересы семьи
экс-губернатора Краснодарского края Александра Ткачёва. Владелец прямо
попросил завести под это отдельную карточку.

Сумма этой конкретной перепродажи не раскрывалась ни в одном источнике
(рыночная оценка Ivashkevich Hospitality — около 1 млрд ₽ — относится к
объекту в целом, а не к цене именно этой сделки); честно оставлена
пустой.

Запуск: python3 pipeline/fix_add_ladacha_akashevskaya_resale_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g76f31c63'
BUYER_ID = 'gakashevskaya'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert BUYER_ID not in data['companies']
    assert data['companies'].get('ge49c632a', {}).get('name') == 'Наталия Дубовицкая'

    data['companies'][BUYER_ID] = {
        'name': 'Птицефабрика «Акашевская»',
        'ind': 'Недвижимость',
        'desc': ('Владеет активами через «Марфининвест»; конечный '
                 'бенефициар — Мария Лисицина, по неофициальным данным '
                 'представляющая интересы семьи экс-губернатора '
                 'Краснодарского края Александра Ткачёва.'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2023-10-11',
        'title': 'ООО «Птицефабрика «Акашевская»» купило базу отдыха «Ла дача Астрахань» у Наталии Дубовицкой',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/6281365'],
                ['РИА Недвижимость',
                 'https://realty.ria.ru/20231017/villa-1903249316.html']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = BUYER_ID
    card['seller_id'] = 'ge49c632a'
    card['target'] = 'g58674c9f'
    card['eco']['context'] = (
        'С 11 октября 2023 года базу отдыха «Ла дача Астрахань» приобрело '
        'ООО «Птицефабрика «Акашевская»», которым через «Марфининвест» '
        'владеет Мария Лисицина — по неофициальным данным, она '
        'представляет интересы семьи экс-губернатора Краснодарского края '
        'Александра Ткачёва. Наталия Дубовицкая владела активом меньше '
        'двух месяцев. Рыночную стоимость объекта Ivashkevich Hospitality '
        'оценивала в 1 млрд ₽, и на прибыль от цепочки перепродаж (объект '
        'уже сменил нескольких владельцев за 2023 год) продавец, скорее '
        'всего, не вышел.'
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
