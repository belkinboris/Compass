# -*- coding: utf-8 -*-
"""Карточка g25aaf2c0 родилась механическими воротами (`promote.py`) с
перепутанными сторонами: заголовок РИА «Старинный купеческий особняк в
центре Москвы купил производитель колбас» разобрался так, что в buyer_name
попал предмет, а в asset — покупатель. Разбор всей статьи показывает:
ООО «Дэнир» (связано с группой Velcom — уже есть профиль g4de3e3ed, тот
же, что покупал бывший бизнес Valio/Viola) выиграло аукцион «Росэлторга» на
купеческий особняк XVIII века на Пятницкой улице, 15 в Москве — заплатило
620,68 млн ₽ при начальной цене 263 млн ₽. Продавец — АО «Центр управления
городским имуществом» (управляет недвижимостью Москвы).

ИСТОЧНИК: РИА Недвижимость, https://realty.ria.ru/20261123/moskva-2133449100.html

Запуск:
    python3 pipeline/fix_add_denir_pyatnitskaya_mansion_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_denir_pyatnitskaya_mansion_2026_11_23.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
RIA_URL = 'https://realty.ria.ru/20261123/moskva-2133449100.html'
CARD_ID = 'g25aaf2c0'
BUYER_ID = 'g4de3e3ed'  # «Дэнир», уже есть в data['companies']


def build_card(card):
    card.update({
        'title': '«Дэнир» купил на торгах старинный особняк на Пятницкой улице в Москве',
        'ind': 'Недвижимость',
        'type': 'Продажа с торгов',
        'status': 'Закрыта',
        'src': [['РИА Недвижимость', RIA_URL]],
        'eco': {'sum': '620,68 млн ₽', 'share': '—', 'val': '—', 'target_fin': '—', 'fin': '—',
                'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'sum': '620,68 млн ₽',
        'buyer': BUYER_ID,
        'seller': 'АО «Центр управления городским имуществом»',
        'seller_src': 'text',
        'asset': 'Особняк на Пятницкой улице',
        'party_evidence': {
            'buyer': [{'value': 'Дэнир', 'field': 'buyer',
                       'method': 'manual_source_review', 'url': RIA_URL}],
            'seller': [{'value': 'АО «Центр управления городским имуществом»', 'field': 'seller',
                        'method': 'explicit_news_title', 'url': RIA_URL}],
            'target': [{'value': 'Особняк на Пятницкой улице', 'field': 'asset',
                        'method': 'manual_source_review', 'url': RIA_URL}],
        },
        'accepted_notes': {
            'no_profile': {
                'seller': ('АО «Центр управления городским имуществом» — найден только нечеткий лид '
                           '(один агрегатор, OpenSanctions, называет ИНН 9722088628), который сам '
                           'источник предупреждает не путать с одноименным ГУП г. Москвы по тому же '
                           'адресу (другая правовая форма) — второй источник не нашелся, профиль не '
                           'заводим.'),
            },
            'notes': ('Механические ворота (`promote.py`) перепутали стороны заголовка — buyer_name '
                      'получил предмет сделки, а asset — покупателя; разобрано заново по полному '
                      'тексту статьи.'),
            'searched': ('РИА Недвижимость, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py); WebSearch «АО Центр управления городским '
                          'имуществом ИНН ОГРН Москва» — нашел только лид с одного агрегатора, без '
                          'подтверждения вторым источником и с явным риском спутать с ГУП того же '
                          'имени.'),
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

    pending = json.load(open(PENDING, encoding='utf-8'))
    cur_by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in cur_by_id, 'заглушка пропала при повторном чтении'
    pending['cards'] = [card if c['id'] == CARD_ID else c for c in pending['cards']]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: карточка заполнена в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
