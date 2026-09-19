# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№699: «Убираем вообще». Купленные 32% акций «Автобан» этим летом уже продал
обратно, а сейчас по «Уренгойдорстрою» зарегистрировано отдельное
банкротное дело (А81-8976/2026) — сделка, по всей видимости, не
состоялась; владелец решил не держать карточку в базе.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    target = [d for d in deals if d['id'] == 'gbd3416b4']
    assert len(target) == 1, target
    assert target[0]['title'] == 'Холдинг «Автобан» приобретает «Уренгойдорстрой»'

    tp = data.get('telegram_posts', {})
    assert tp.get('gbd3416b4') is None

    data['deals'] = [d for d in deals if d['id'] != 'gbd3416b4']

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gbd3416b4 удалена. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
