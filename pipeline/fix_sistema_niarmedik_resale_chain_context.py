# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gc9f8d104 (АФК «Система»
выкупила долю Сбера в ГК «Ниармедик» и консолидировала 100%, ноябрь 2024):
дельта-поиск нашёл, что 100%-й контроль «Системы» продержался чуть больше
года. В декабре 2025 года «Система» продала свои 50% партнёру по развитию
актива — ООО «Доктор рядом холдинг», которое консолидировало 100% сети
(Интерфакс). Тот же «Доктор рядом холдинг» почти сразу перепродал 14
клиник сети (в Москве и Обнинске) компании «АВС-медицина» — оценка сделки
от гендиректора Eqiva Дарьи Шубиной, 1,5 млрд руб. (medvestnik.ru). Обе
цитаты подтверждены лично прямым WebFetch. Не через review.py: цитаты из
НЕСКОЛЬКИХ новых источников описывают цепочку событий ПОСЛЕ самой сделки.

Запуск: python3 pipeline/fix_sistema_niarmedik_resale_chain_context.py
        python3 pipeline/fix_sistema_niarmedik_resale_chain_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc9f8d104'

OLD_CONTEXT = (
    'Управляющими компаниями всех трех юрлиц является фармхолдинг из '
    'портфеля АФК «Система» — «Биннофарм Групп». Гендиректором «Нового '
    'инвестиционного холдинга» является руководитель «Биннофарм Групп» '
    'Рустем Муратов.'
)
CONTEXT_ADDITION = (
    ' 100%-й контроль «Системы» продержался чуть больше года: в декабре '
    '2025 года «ПАО АФК «Система» продало принадлежащие ему 50% в сети '
    'клиник «Ниармедик» партнеру по развитию актива – ООО «Доктор рядом '
    'холдинг»», которое консолидировало 100% сети (Интерфакс). Почти сразу '
    'после этого «Доктор рядом холдинг» перепродал 14 клиник сети (в '
    'Москве и Обнинске) компании «АВС-медицина» — оценка сделки от '
    'гендиректора Eqiva Дарьи Шубиной составила 1,5 млрд руб. '
    '(medvestnik.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1064046'],
    ['Medvestnik', 'https://medvestnik.ru/content/news/avs-medicina-vykupila-kliniki-niarmedik.html'],
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
