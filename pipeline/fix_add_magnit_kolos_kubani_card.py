# -*- coding: utf-8 -*-
"""Заметка 497 (консоль, 4 сентября 2026): «Отдельная сделка и отдельная
карточка, да», отвечая на карточку `g8e7eee71» (АО «СХП «Колос»»
приобрела 50% ООО «Колос Кубани», декабрь 2023 года).

`extra» уже нёс находку месячной очереди (Коммерсантъ, doc/8477794): 2
марта 2026 года «Колос Кубани» продали целиком «Магниту» за оценочные
1,8 млрд ₽; к этому моменту владельцем числился уже не АО «СХП «Колос»»
или ЗАО «Династия», а Денис Таран — связь его со сторонами исходной
сделки 2023 года публично не раскрыта.

Запуск: python3 pipeline/fix_add_magnit_kolos_kubani_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'gd741513a'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    # 6 сентября 2026: карточка оказалась дублем уже стоявшей в базе ge386fb20 и слита в неё
    # (pipeline/merge_duplicate_deals_batch.py) — повторный запуск завёл бы дубль заново.
    assert NEW_ID not in data.get('merged', {}), 'карточка слита в %s, скрипт больше не запускать' % data['merged'].get(NEW_ID)
    assert NEW_ID not in ids
    assert data['companies'].get('gd19e26bf', {}).get('name') == 'Магнит'
    assert data['companies'].get('gf4207471', {}).get('name'), 'нет профиля Колос Кубани'

    draft = {
        'date': '2026-03-02',
        'title': '«Магнит» купил ООО «Колос Кубани» у Дениса Тарана',
        'ind': 'Агро',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': '1,8 млрд ₽ (по оценке)',
        'seller': 'Денис Таран',
        'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/8477794']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = 'gd19e26bf'
    card['target'] = 'gf4207471'
    card['eco']['sum'] = '1,8 млрд ₽ (по оценке)'
    card['eco']['context'] = (
        'К моменту продажи «Магниту» владельцем «Колос Кубани» числился '
        'Денис Таран — не АО «СХП «Колос»» и не ЗАО «Династия», '
        'выступавшие сторонами в исходной сделке 2023 года (отдельная '
        'карточка g8e7eee71). Связь Тарана с этими сторонами публично '
        'не раскрыта.'
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
