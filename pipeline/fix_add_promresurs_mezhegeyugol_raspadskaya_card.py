# -*- coding: utf-8 -*-
"""Почасовой приток 4 сентября 2026 — вторая карточка того же сюжета,
что и `ge0cc0dfe» (Северсталь/«Улугхемуголь»/«Промресурс»): найдена при
обязательном поиске дополнительных источников (шаг 9а) по той же
сделке — «Промресурс» в те же дни купила у «Распадской» ВТОРОЙ угольный
актив в Туве, 81,3% «УК Межегейуголь» (оформлено в ЕГРЮЛ 3 сентября, на
неделю позже сделки с «Северсталью»). Разные продавцы — отдельная
карточка, не дополнение к первой.

Источник — smart-lab.ru (репост со ссылкой на Интерфакс), текст
скачан (`fetch_article_texts.py`), карточка построена вручную
(`promote.to_card()`), потому что заголовок описывает ДВЕ сделки сразу
и не проходит автоматические ворота.

Кладётся в `pending.json`, а не в базу напрямую — как и любая новая
находка притока, ждёт решения владельца через консоль.

Запуск: python3 pipeline/fix_add_promresurs_mezhegeyugol_raspadskaya_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'gd3556cc0'
RASPADSKAYA_ID = 'graspadskaya'
PROMRESURS_ID = 'gpromresurs'


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    ids = {c['id'] for c in base['deals']} | {c['id'] for c in pending['cards']}
    assert NEW_ID not in ids
    assert RASPADSKAYA_ID not in base['companies']
    assert PROMRESURS_ID not in base['companies']

    base['companies'][RASPADSKAYA_ID] = {
        'name': 'Распадская',
        'ind': 'Уголь',
        'desc': 'Угольная компания, структура Evraz.',
        'kpi': ['Профиль', 'Автоматический'],
    }
    base['companies'][PROMRESURS_ID] = {
        'name': 'ООО «Промресурс»',
        'ind': 'Уголь',
        'desc': ('Новосибирская компания, принадлежит Сергею Дьяконову; '
                 'специализируется на оптовой торговле твёрдым топливом. '
                 'В августе-сентябре 2026 года купила два угольных '
                 'актива в Туве — «Улугхемуголь» у «Северстали» '
                 '(отдельная карточка) и «УК Межегейуголь» у '
                 '«Распадской».'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2026-09-03',
        'title': '«Промресурс» купил у «Распадской» 81,3% «УК Межегейуголь» в Туве',
        'ind': 'Уголь',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['smart-lab.ru (со ссылкой на Интерфакс)',
                 'https://smart-lab.ru/blog/news/1347964.php']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = PROMRESURS_ID
    card['seller_id'] = RASPADSKAYA_ID
    card['eco']['share'] = (
        '«УК Межегейуголь» (81,3%): бывший актив «Распадской» (структура '
        'Evraz). Разработка Межегейского месторождения (мощность — 1 '
        'млн т коксующегося угля марки Ж в год, запасы по JORC — 86 '
        'млн т). Также владеет лицензией на участок Восточный '
        '(приостановлена из-за задержки строительства ж/д '
        'Кызыл-Курагино).'
    )
    card['eco']['rationale'] = (
        '«Распадская»: подтвердила завершение сделки, актив больше не '
        'входит в состав компании.'
    )
    card['eco']['context'] = (
        'История активов связана с нереализованным проектом '
        'строительства железнодорожной ветки «Кызыл-Курагино» '
        '(госвложения оценивались в ₽49 млрд, частные — ₽81 млрд). В те '
        'же дни «Промресурс» купила у «Северстали» второй угольный '
        'актив в Туве — 100% «Улугхемуголь» (оформлено в ЕГРЮЛ 27 '
        'августа, на неделю раньше) — отдельная сделка с другим '
        'продавцом, своя карточка.'
    )

    pending['cards'].append(card)

    print(f'Добавлена карточка {NEW_ID} в pending.json: {card["title"]}')

    if write:
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
