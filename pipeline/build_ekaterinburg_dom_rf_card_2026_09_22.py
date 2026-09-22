# -*- coding: utf-8 -*-
"""Приток 22 сентября 2026: enrich.py ошибочно счёл статью про старинный
деревянный дом в Екатеринбурге (РИА Недвижимость) дополнением к карточке
g7ea48d66 (флигель дачи в Петергофе) — разные города, разные здания
(см. pipeline/fix_wrong_src_g7ea48d66_2026_09_22.py, где ошибочный
источник убран). На самом деле это отдельная сделка «Дом.РФ» — тем же
путём, что и другие её лоты (флигель в Петергофе, гостиница «Мадрид»),
собираю отдельную карточку предпросмотра напрямую через promote.to_card(),
с дословными цитатами из полного текста источника
(data/inbox/raw/2026-09-22-articles.jsonl).

Запуск: python3 pipeline/build_ekaterinburg_dom_rf_card_2026_09_22.py --write
"""
import argparse
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, 'pipeline/ingest')
import promote  # noqa: E402

PENDING = 'static/data/pending.json'
URL = 'https://realty.ria.ru/20260922/ekaterinburg-2119532039.html'

DRAFT = {
    'draft_id': 'd-ekb-domrf-2026-09-22',
    'title': '«Дом.РФ» продаёт на торгах старинный деревянный дом в Екатеринбурге',
    'date': '2026-09-22',
    'src': [['РИА Недвижимость', URL]],
    'sum': None,
    'type': 'Продажа с торгов',
    'status': 'Обсуждается',
    'events': [],
    'buyer_name': None,
    'asset': 'старинный деревянный усадебный дом в историческом центре Екатеринбурга',
    'seller': '«Дом.РФ»',
    'parsed_parties': {'buyer': None,
                        'asset': 'старинный деревянный усадебный дом в историческом центре Екатеринбурга',
                        'seller': '«Дом.РФ»'},
    'ind': 'Недвижимость',
    'needs_review': True,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    card['eco']['sum'] = 'Начальная цена лота - 15,28 миллиона рублей.'
    card['eco']['share'] = ('Победитель торгов получит в собственность здание площадью '
                             '363 квадратных метра и участок в 0,04 гектара.')
    card['eco']['context'] = ('Деревянное строение 1880-х годов находится в удовлетворительном '
                               'состоянии и отличается богатым резным декором фасадов, мезонином '
                               'и сложной геометрией кровли, состоящей из куполов и башенок. '
                               'Памятник деревянной архитектуры находится по адресу: улица '
                               'Белинского, 6Б, и является частью ансамбля городской усадьбы '
                               'мещанина Григория Елизарьева. Объект имеет статус памятника '
                               'культурного наследия регионального значения.')
    card['law']['struct'] = ('Заявки на участие в торгах принимаются до 28 сентября. Аукцион '
                              'состоится 2 октября.')
    card['law']['terms'] = ('Победитель торгов будет обязан провести работы по реставрации и '
                             'сохранению здания.')
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
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
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    main(args.write)
