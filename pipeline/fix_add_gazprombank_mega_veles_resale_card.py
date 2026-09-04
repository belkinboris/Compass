# -*- coding: utf-8 -*-
"""Заметка 491 (консоль, 4 сентября 2026): «Да, отдельная карта», отвечая
на карточку `g4f1b5909» (Газпромбанк купил портфель ТЦ «Мега» у Ingka
Centres, 28.09.2023).

`extra» карточки `g4f1b5909» уже нёс факт перепродажи (найден при
дочитывании месячной очереди, «Известные проблемы» CLAUDE.md): в ноябре
2025 года Газпромбанк перепродал весь портфель управляющей компании
«Велес Менеджмент» — по словам источника, близкого к сделке (Pravo.ru),
это была продажа за 300 млрд ₽, хотя официальная формулировка самого
Газпромбанка была осторожнее («передача управления»). Покупатель
следующего звена — под санкциями США (The Insider). Владелец подтвердил:
делаем отдельную карточку.

Оба источника (Pravo.ru, The Insider) уже были привязаны к исходной
карточке при добавлении факта в `extra` — используются те же ссылки.

Запуск: python3 pipeline/fix_add_gazprombank_mega_veles_resale_card.py [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'gaec5231e'
BUYER_ID = 'gvelesmanagement'


def main(write=False):
    import promote

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    ids = {c['id'] for c in data['deals']}
    assert NEW_ID not in ids
    assert BUYER_ID not in data['companies']
    assert data['companies'].get('gf1f56e08', {}).get('name') == 'Газпромбанк'

    data['companies'][BUYER_ID] = {
        'name': '«Велес Менеджмент»',
        'ind': 'Недвижимость',
        'desc': ('Управляющая компания; в ноябре 2025 года купила у '
                 'Газпромбанка портфель из 14 ТЦ «Мега». Внесена в '
                 'санкционный список США.'),
        'kpi': ['Профиль', 'Автоматический'],
    }

    draft = {
        'date': '2025',
        'title': '«Велес Менеджмент» купил портфель ТЦ «Мега» у Газпромбанка',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Закрыта',
        'sum': '300 млрд ₽ (неофициально)',
        'src': [['Pravo.ru', 'https://pravo.ru/news/261060/'],
                ['The Insider', 'https://theins.ru/news/286523']],
    }
    card = promote.to_card(draft, NEW_ID)
    card['buyer'] = BUYER_ID
    card['seller_id'] = 'gf1f56e08'
    card['target'] = 'g68aca909'
    card['eco']['sum'] = '300 млрд ₽ (неофициально)'
    card['eco']['context'] = (
        'Официальная формулировка самого Газпромбанка осторожнее — '
        '«передача управления», а не продажа. Источник, близкий к '
        'сделке, называет её продажей сети ТЦ «Мега» за 300 млрд ₽. '
        '«Велес Менеджмент» внесена в санкционный список США.'
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
