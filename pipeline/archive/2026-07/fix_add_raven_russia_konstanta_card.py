# -*- coding: utf-8 -*-
"""Заметка 493 (консоль, 4 сентября 2026): «По активу «константа» делаем
новую карточку. Только надо нормально покупателя написать. Касательно
второго актива - Если есть карточка про Kellerman, то обогатить этой
инфой, а если нет, то пока не пишем», отвечая на карточку `g3d34ac8e»
(Raven Russia продала БЦ «Примиум» ЗПИФ «РД 2», 11.07.2024).

Второй актив (бизнес-центр Kellermann в Петербурге, изъятый по иску
Генпрокуратуры у Богородова/Шувалова/Phoenix Property Group, решение
апелляции — февраль 2026) в базе карточки не имеет — поиском по имени
(«Kellermann»/«Келлерман») ничего не найдено. Per прямому указанию
владельца — карточку под это НЕ заводим сейчас.

Актив «Константа» — перепроверено прямым чтением (Коммерсантъ,
18.11.2024, kommersant.ru/doc/7310380): «ООО «Петроэстейт»,
балансодержатель бизнес-центра «Константа» в Санкт-Петербурге, перешло
в собственность ООО «Гранит»» — покупатель контролируется Еленой
Некрасовой, супругой члена Совета Федерации Александра Некрасова;
компания связана с застройщиком «Лидер Групп» и управляет соседним
комплексом «Лидер Тауэр». Точная сумма сделки не раскрыта, ранее объект
предлагался на рынке за 0,8–1 млрд ₽.

Запуск: python3 pipeline/fix_add_raven_russia_konstanta_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g0d72e1d5'
BUYER_ID = 'ggranitnekrasova'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert BUYER_ID not in data['companies']
    assert data['companies'].get('g21d61789', {}).get('name') == 'Raven Russia'

    data['companies'][BUYER_ID] = {
        'name': 'ООО «Гранит»',
        'ind': 'Недвижимость',
        'desc': ('Контролируется Еленой Некрасовой, супругой члена Совета '
                 'Федерации Александра Некрасова; связана с застройщиком '
                 '«Лидер Групп» и управляет соседним комплексом «Лидер '
                 'Тауэр» в Санкт-Петербурге.'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        # Известен месяц (ноябрь), но не день — база хранит только
        # YYYY-MM-DD, YYYY или "unknown" (test_dates_are_parseable),
        # день не выдумывается, месяц уходит в eco.context.
        'date': '2024',
        'title': 'ООО «Гранит» (Елена Некрасова) купило БЦ «Константа» у Raven Russia',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': '0,8–1 млрд ₽ (по прежним предложениям на рынке)',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7310380']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = BUYER_ID
    card['seller_id'] = 'g21d61789'
    card['eco']['context'] = (
        'Сделка закрыта в ноябре 2024 года. Балансодержателем '
        'бизнес-центра выступало ООО «Петроэстейт» — оно перешло в '
        'собственность ООО «Гранит». Raven Russia называет актив '
        'непрофильным: компания фокусируется на складских проектах.'
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
