# -*- coding: utf-8 -*-
"""Карточка `g20d4cc38` (ЛУКОЙЛ/Carlyle, LUKOIL International GmbH) —
дополнение: собственное заявление LIG (первое заявление стороны сделки
в этой карточке, не только пересказ прессы) и справка FT о Тодде Боули.
Append к eco.context — review.py не годится для append.

Источник: https://1prime.ru/20261008/srok-874080998.html

    python3 pipeline/fix_g20d4cc38_lig_own_statement.py           # показать
    python3 pipeline/fix_g20d4cc38_lig_own_statement.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g20d4cc38'

OLD_CONTEXT_TAIL = (
    'Если же OFAC продлит санкции, то банковские счета LIG могут быть '
    'заблокированы.'
)
ADDED_CONTEXT = (
    '«В конце июля срок действия соглашения купли-продажи истек, так '
    'как OFAC не одобрило его. В настоящее время ведутся активные '
    'переговоры с другими заинтересованными сторонами о возможной '
    'покупке LIG», - говорится в отчете компании. Согласование сделки '
    'уже почти 10 месяцев как затерялось между американскими '
    'ведомствами в ожидании окончательного одобрения администрации '
    'президента США Дональда Трампа, сообщила в сентябре газета '
    'Financial Times со ссылкой на информированные источники. Позднее '
    'FT сообщала с ссылкой на источники, что американский инвестор '
    'Тодд Боули получил поддержку властей США и представителей стран '
    'Персидского залива для возможного приобретения иностранных '
    'активов "Лукойла".'
)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert deal['eco']['context'].endswith(OLD_CONTEXT_TAIL), deal['eco']['context']
    deal['eco']['context'] = deal['eco']['context'] + ' ' + ADDED_CONTEXT
    print('Дополнено: собственное заявление LIG и справка FT о Тодде Боули')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
