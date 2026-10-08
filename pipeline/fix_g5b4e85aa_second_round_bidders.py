# -*- coding: utf-8 -*-
"""Карточка `g5b4e85aa` (аукцион по продаже изъятого агробизнеса Боброва и
Бикова) — первый раунд провалился без заявок (событие от 29 сентября уже
в базе). Повторная продажа посредством публичного предложения получила
двух претендентов; торги/определение победителя — сегодня, 8 октября.
Статус не меняю: ни слова из review.STATUS_WORDS['Обсуждается'] в цитате
нет, а победитель ещё не объявлен — рано говорить и о «Закрыта».

Источник: https://ura.news/news/1053134588

    python3 pipeline/fix_g5b4e85aa_second_round_bidders.py           # показать
    python3 pipeline/fix_g5b4e85aa_second_round_bidders.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g5b4e85aa'

NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-10-08',
    'title': 'Повторная продажа: допущены два претендента',
    'note': ('На торги по продаже четырех национализированных агрохолдингов, '
             'ранее связанных с бизнесменами Алексеем Бобровым и Артемом '
             'Биковым, поступили две заявки. Обоих претендентов допустили к '
             'покупке активов с начальной стоимостью 571,3 млн рублей. '
             'Заявки поступили 2 октября, решение о допуске приняли 7 '
             'октября. Имена участников в выписке не раскрываются. Продажа '
             'проходит посредством публичного предложения: условия '
             'позволяют снизить начальную цену до 285,6 млн рублей. Торги '
             'назначили на 8 октября, в карточке лота указан статус '
             '«Определение победителя».'),
    'source': ['URA.RU', 'https://ura.news/news/1053134588'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    existing = {(e.get('kind'), e.get('date')) for e in (deal.get('events') or [])}
    assert (NEW_EVENT['kind'], NEW_EVENT['date']) not in existing, 'событие уже есть'
    deal['events'] = (deal.get('events') or []) + [NEW_EVENT]
    deal['events'].sort(key=lambda e: (e.get('date') or '', e.get('kind') or ''))
    print('Добавлено событие: повторная продажа, два претендента (8 октября 2026)')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
