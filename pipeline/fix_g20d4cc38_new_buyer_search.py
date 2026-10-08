# -*- coding: utf-8 -*-
"""Карточка `g20d4cc38` (ЛУКОЙЛ/Carlyle, LUKOIL International GmbH) —
дополнение после отказа OFAC: компания ищет нового покупателя, риск
блокировки счетов LIG, оценка сделки в $20 млрд, причина санкций.
Append к eco.context/eco.val/law.appr — review.py не годится для append.

Источник: https://pravo.ru/news/266214/

    python3 pipeline/fix_g20d4cc38_new_buyer_search.py           # показать
    python3 pipeline/fix_g20d4cc38_new_buyer_search.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g20d4cc38'

OLD_CONTEXT_TAIL = (
    'При этом в сентябре сообщалось, что OFAC продлило до 22 октября '
    'лицензию, которая разрешает ведение переговоров и вступление в '
    'условные соглашения с «Лукойлом» для продажи Lukoil International '
    'GmbH.'
)
ADDED_CONTEXT = (
    'Теперь компания ищет нового покупателя на группу компаний LIG. '
    'Лицензия OFAC, позволяющая вести переговоры о продаже, передаче или '
    'отчуждении компании, работает до 22 октября. Руководство надеется, '
    'что нужные лицензии будут продлены до завершения сделки. Если же '
    'OFAC продлит санкции, то банковские счета LIG могут быть '
    'заблокированы.'
)

OLD_VAL = (
    'По оценке Шапошникова, эти активы стоят около $10 млрд, но Carlyle '
    'заплатит за них $3–4 млрд.'
)
ADDED_VAL = 'Сама сделка оценивается в $20 млрд.'

OLD_APPR = 'Сделка зависит от получения регуляторных согласований, включая одобрение OFAC США.'
ADDED_APPR = (
    '«Лукойл» подпал под санкции США в октябре прошлого года. OFAC '
    'обосновал их «отсутствием серьезной заинтересованности России в '
    'мирном процессе».'
)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert deal['eco']['context'].endswith(OLD_CONTEXT_TAIL), deal['eco']['context']
    assert deal['eco']['val'] == OLD_VAL, deal['eco']['val']
    assert deal['law']['appr'] == OLD_APPR, deal['law']['appr']
    deal['eco']['context'] = deal['eco']['context'] + ' ' + ADDED_CONTEXT
    deal['eco']['val'] = OLD_VAL + ' ' + ADDED_VAL
    deal['law']['appr'] = OLD_APPR + ' ' + ADDED_APPR
    print('Дополнено: поиск нового покупателя, оценка $20 млрд, причина санкций OFAC')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
