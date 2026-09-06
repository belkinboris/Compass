# -*- coding: utf-8 -*-
"""Заметка 499 (консоль, 4 сентября 2026): «Конечно отдельная
карточка», отвечая на карточку `g46cc9712» (VK приобрела 25% акций
банка «Точка», конец 2023 года).

`extra» уже нёс находку месячной очереди (ComNews, 17.04.2026): 16
апреля 2026 года VK полностью вышла из капитала «Точки», продав долю
холдингу «Интеррос» Владимира Потанина не менее чем за 21,2 млрд ₽ —
вся «Точка» оценена в 84,8 млрд ₽ против 46,5 млрд ₽ на момент покупки
VK. Контроль переходит к «Т-Технологиям», которые намерены
консолидировать 100% через допэмиссию к концу 2026 года (по докладу
саб-агента со ссылкой на Коммерсантъ — не перепроверено отдельным
WebFetch в этой сессии).

Запуск: python3 pipeline/fix_add_vk_tochka_interros_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'g2b4f839e'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    # 6 сентября 2026: карточка оказалась дублем уже стоявшей в базе g2b1fe015 и слита в неё
    # (pipeline/merge_duplicate_deals_batch.py) — повторный запуск завёл бы дубль заново.
    assert NEW_ID not in data.get('merged', {}), 'карточка слита в %s, скрипт больше не запускать' % data['merged'].get(NEW_ID)
    assert NEW_ID not in ids
    assert data['companies'].get('g4e694234', {}).get('name') == 'VK'
    assert data['companies'].get('g088e8f9f', {}).get('name') == '«Интеррос»'
    assert data['companies'].get('g09ccbaca', {}).get('name'), 'нет профиля Точки'

    draft = {
        'date': '2026-04-16',
        'title': 'VK продала долю в банке «Точка» холдингу «Интеррос»',
        'ind': 'Банки',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': 'не менее 21,2 млрд ₽',
        'src': [['Ведомости',
                 'https://www.vedomosti.ru/finance/news/2026/04/16/1190812-vk-prodala-dolyu'],
                ['ComNews',
                 'https://www.comnews.ru/content/244816/2026-04-17/2026-w16/1008/vk-postavila-banku-tochku-interros-teper-u-rulya']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = 'g088e8f9f'
    card['seller_id'] = 'g4e694234'
    card['target'] = 'g09ccbaca'
    card['eco']['sum'] = 'не менее 21,2 млрд ₽'
    card['eco']['context'] = (
        'VK приобрела этот пакет в IV квартале 2023 года за 11,6 млрд ₽ '
        '(отдельная карточка g46cc9712) и получила за время владения '
        '4,3 млрд ₽ дивидендов. «Интеррос» планирует передать пакет '
        '«Т-Технологиям» по закрытой подписке — они заявили о планах '
        'консолидировать до 100% акций «Точки», завершение ожидается в '
        'конце 2026 года после определения параметров допэмиссии.'
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
