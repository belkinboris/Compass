# -*- coding: utf-8 -*-
"""Приток 22 сентября 2026: enrich.py по эвристике «общее название в
кавычках и общие слова» ошибочно приписал карточке g7ea48d66 (флигель
старинной дачи в Петергофе) источник о СОВСЕМ ДРУГОМ объекте —
«"Дом.РФ" продает на торгах старинный деревянный дом в Екатеринбурге»
(realty.ria.ru/20260922/ekaterinburg-2119532039.html). Разные города,
разные здания — родня уже разобранной сегодня ложной находки дубля
(антикварный план Москвы vs здания ВНИИ «Эталон»). Убираю неверно
приписанный источник; сама новость о екатеринбургском доме пойдёт своей
отдельной карточкой через обычный приток.

Запуск: python3 pipeline/fix_wrong_src_g7ea48d66_2026_09_22.py --write
"""
import argparse
import json

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'g7ea48d66'
WRONG_SRC = ['РИА Недвижимость', 'https://realty.ria.ru/20260922/ekaterinburg-2119532039.html']


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert WRONG_SRC in card['src'], 'ошибочного источника уже нет в карточке'
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['src'].remove(WRONG_SRC)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано: %s — ошибочный источник убран.' % CARD_ID)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    main(args.write)
