# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g514c4225 (Фонд 3 STREAMS
вложил 45 млн рублей в производителя мебели VMMGame): дельта-поиск нашёл
финансовые показатели ООО «Куб» (юрлицо VMMGame) за 2025 год — рост,
которого ожидали от инвестиций, не подтвердился: выручка снизилась, а
компания показала убыток. Цифры подтверждены лично прямым WebFetch
(companies.rbc.ru).

Отдельный источник (агрегатор vbankcenter.ru) утверждал, что компания —
банкрот с введённым наблюдением, но с внутренне противоречивыми датами
(наблюдение якобы введено ПОСЛЕ даты, которой то же дело названо
«закрытым») и без единого новостного подтверждения. Прямая проверка
companies.rbc.ru («на 28 августа 2026 года ООО «КУБ» «действует»», ни
слова о банкротстве или несостоятельности) этому утверждению ПРОТИВОРЕЧИТ
— факт о банкротстве в карточку НЕ идёт, это ложная тревога одного
агрегатора, не подтверждённая независимо.

`eco.context` расширен только той частью, что подтвердилась дважды
(тенденция роста-затем-падения видна и по прежней записи карточки, где
уже стояла выручка 2023 года 223 млн ₽).

Запуск: python3 pipeline/fix_vmmgame_postdeal_financials.py
        python3 pipeline/fix_vmmgame_postdeal_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g514c4225'

OLD_TARGET_FIN = (
    'Выручка проекта, по данным системы «Контур.Фокус», по итогам 2023 '
    'года составила почти 223 млн рублей, что в 1,5 раза превышает '
    'показатель 2022 года. Чистая прибыль достигла 4 млн рублей против 1 '
    'млн годом ранее.'
)
TARGET_FIN_ADDITION = (
    ' По данным на начало 2025 года выручка ООО «Куб» выросла до 317,2 '
    'млн рублей, но уже за 2025 год снизилась до 193,9 млн рублей, а '
    'компания получила чистый убыток 60,8 млн рублей (companies.rbc.ru) — '
    'рост, на который рассчитывали инвесторы, не подтвердился.'
)
NEW_TARGET_FIN = OLD_TARGET_FIN + TARGET_FIN_ADDITION

NEW_SRC = [
    ['РБК Компании', 'https://companies.rbc.ru/id/1205000013184-obschestvo-s-ogranichennoj-otvetstvennostyu-kub/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
