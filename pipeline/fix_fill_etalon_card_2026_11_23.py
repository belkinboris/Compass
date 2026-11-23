# -*- coding: utf-8 -*-
"""Карточка g9b852635 родилась пустой заглушкой (обычные ворота `promote.py`
нашли её сами, без решения владельца «в работу» — заголовок РИА называет
продавца и предмет прямо). Этот скрипт заполняет структурные поля;
прозу — `pipeline/ingest/fixes/written_2026_11_23_etalon.py` через
`review.py --write`.

ИСТОЧНИК: РИА Недвижимость, https://realty.ria.ru/20261123/etalon-2133385948.html
(первоисточник — цитата представителя «Эталона»; цена 8,1 млрд ₽ там же
со ссылкой на телеграм-каналы, сама компания цену не подтвердила).

Запуск:
    python3 pipeline/fix_fill_etalon_card_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_fill_etalon_card_2026_11_23.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

RIA_URL = 'https://realty.ria.ru/20261123/etalon-2133385948.html'
CARD_ID = 'g9b852635'
SELLER_ID = 'ga37e3cf6'  # «Эталон Груп», уже есть в data['companies']


def build_card(card):
    card.update({
        'title': 'Участки «Эталона» в Нагатинской пойме выставлены на продажу за 8,1 млрд рублей',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['РИА Недвижимость', RIA_URL]],
        'eco': {'sum': '8,1 млрд ₽ (по данным Telegram-каналов)', 'share': '—', 'val': '—',
                'target_fin': '—', 'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'sum': '8,1 млрд ₽ (по данным Telegram-каналов)',
        'seller': '«Эталон»',
        'seller_id': SELLER_ID,
        'seller_src': 'text',
        'asset': 'Участки в Нагатинской пойме',
        'party_evidence': {
            'seller': [{'value': '«Эталон»', 'field': 'seller',
                        'method': 'explicit_news_title', 'url': RIA_URL}],
            'target': [{'value': 'Участки в Нагатинской пойме', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': RIA_URL}],
        },
        'accepted_notes': {
            'no_profile': {
                'buyer': 'Покупателя пока нет — участки только выставлены на продажу.',
            },
            'searched': ('РИА Недвижимость, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py) — комментарий самой компании «Эталон»; цена '
                          '8,1 млрд ₽ там же приведена со ссылкой на телеграм-каналы, сама '
                          'компания цену не подтвердила.'),
        },
    })
    return card


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in by_id, 'заглушки %s не нашлось' % CARD_ID

    import tag_themes
    card = build_card(dict(by_id[CARD_ID]))
    themes = tag_themes.add_themes(card)
    print('Карточка: %s' % CARD_ID)
    print('  title: %s' % card['title'])
    print('  themes: %s' % themes)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    cur_by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in cur_by_id, 'заглушка пропала при повторном чтении'
    pending['cards'] = [card if c['id'] == CARD_ID else c for c in pending['cards']]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: карточка заполнена в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
