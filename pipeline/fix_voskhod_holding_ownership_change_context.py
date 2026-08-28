# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g81a22b7c (Рыбопромышленный
холдинг «Восход» приобрел 75% ООО «Викта», ноябрь 2024): дельта-поиск
нашёл, что сам холдинг «Восход» сменил структуру владения в апреле 2026
года — ЗПИФ «Море Финанс» (под управлением АО «Инновационная компания НЗ»)
стал владельцем 33% РПХ «Восход», а оставшиеся 67% долей перешли в залог
той же управляющей структуре (Коммерсантъ). «Викта» остаётся в периметре
холдинга наравне с «Камчатка Проект», «Лойд Фиш» и «Лойд Авто» — их
совокупная выручка в 2025 году снизилась на 25,7%, до 4,38 млрд руб. Не
через review.py: цитата из НОВОГО источника, описывающая событие ПОСЛЕ
самой сделки с «Виктой», в поле, уже содержащем текст о структуре
владения холдингом на момент сделки.

Запуск: python3 pipeline/fix_voskhod_holding_ownership_change_context.py
        python3 pipeline/fix_voskhod_holding_ownership_change_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g81a22b7c'

OLD_CONTEXT = (
    'ООО РПХ «Восход» принадлежит компании АО «Море Проект» (по состоянию '
    'на лето 2023 года АО было в собственности структуры ПАО АФК '
    '«Система», сейчас данные о владельце этой компании скрыты).'
)
CONTEXT_ADDITION = (
    ' В апреле 2026 года структура владения самим холдингом изменилась: '
    'владельцем 33% в ООО «РПХ «Восход»» стал ЗПИФ «Море Финанс» под '
    'управлением АО «Инновационная компания НЗ», а «67% оставшихся на '
    'балансе этой структуры долей в РПХ «Восход» перешли в залог ИК НЗ» '
    '(Коммерсантъ). «Викта» остаётся в периметре холдинга наравне с '
    '«Камчатка Проект», «Лойд Фиш» и «Лойд Авто» — их совокупная выручка '
    'в 2025 году снизилась на 25,7%, до 4,38 млрд руб.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8710295'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
