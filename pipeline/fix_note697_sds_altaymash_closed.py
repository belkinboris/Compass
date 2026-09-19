# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№697: «Говорим закрыта». По совокупности четырёх независимых косвенных
сигналов (назначение экс-главы ремзавода «Талтэка» гендиректором
«Алтайвагона» в январе 2024 с явной связью со сменой владельца в статье;
новый каталог активов Михаила Федяева летом 2025 года снова не включает
«Алтаймаш») владелец решил считать сделку закрытой, хотя официального
документа по-прежнему нет.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'
OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g401b169a')
    assert card['status'] == OLD_STATUS

    card['status'] = NEW_STATUS

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g401b169a: статус -> Закрыта. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
