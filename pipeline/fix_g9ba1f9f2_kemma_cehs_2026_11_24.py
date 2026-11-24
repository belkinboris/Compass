# -*- coding: utf-8 -*-
"""Карточка g9ba1f9f2, автоматически отпущенная resolve_duplicates.py
(--apply separate) как отдельная сделка, доcобрана по полному тексту
источника: завод «Кемма» в Челябинске выставил на продажу два цеха с
офисами на своей территории за 387 млн рублей — анонимное объявление на
Авито (продавец назван в заголовке, покупателя нет).

ИСТОЧНИК: URA.RU, https://ura.news/news/1053146951

Запуск:
    python3 pipeline/fix_g9ba1f9f2_kemma_cehs_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9ba1f9f2_kemma_cehs_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
CARD_ID = 'g9ba1f9f2'
URL = 'https://ura.news/news/1053146951'


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    card['title'] = 'Завод «Кемма» в Челябинске выставил на продажу два цеха за 387 млн рублей'
    card['ind'] = 'Промышленность'
    card['sum'] = '387 млн ₽'
    card['seller'] = 'Завод «Кемма»'
    card['asset'] = 'Два цеха с офисами на территории завода «Кемма» в Челябинске'
    card['party_evidence'] = {
        'seller': [{'value': 'Завод «Кемма»', 'field': 'seller', 'method': 'explicit_news_title', 'url': URL}],
        'target': [{'value': 'Два цеха с офисами на территории завода «Кемма» в Челябинске',
                    'field': 'asset', 'method': 'explicit_news_title', 'url': URL}],
    }
    card['accepted_notes'] = {
        'no_profile': {
            'seller': ('«Кемма» названа в источнике только как завод, на территории которого находятся '
                       'продаваемые цеха; юридическое лицо-продавец и объявление на «Авито» не называют '
                       'напрямую — честная пустота, профиль не заводим.'),
            'buyer': 'объявление о продаже — покупателя еще нет, профиль не заводим.',
            'target': ('Два цеха с офисами на территории завода «Кемма» — анонимное объявление, '
                       'юрлицо-владелец не названо; профиль не заводим.'),
        },
        'searched': ('URA.RU, 24.11.2026 (первоисточник, прочитан целиком через '
                      'fetch_article_texts.py) — единственная найденная публикация об этом объявлении.'),
    }


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('Карточка %s обновлена: %s' % (CARD_ID, data['cards'][
        next(i for i, c in enumerate(data['cards']) if c['id'] == CARD_ID)]['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
