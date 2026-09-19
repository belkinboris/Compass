# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№698: «Убирай карту это стройка». Владелец считает предмет карточки
строительным/девелоперским вопросом, а не M&A-сделкой, которую стоит вести
в базе, — удаляем целиком.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    target = [d for d in deals if d['id'] == 'gb49e3668']
    assert len(target) == 1, target
    assert target[0]['title'] == 'Dogma выкупила две площадки ГК ПИК в Москве'

    tp = data.get('telegram_posts', {})
    assert tp.get('gb49e3668') is None

    data['deals'] = [d for d in deals if d['id'] != 'gb49e3668']

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gb49e3668 удалена. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
