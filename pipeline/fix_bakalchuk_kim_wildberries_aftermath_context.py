# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gcdf7065a (Владислав
Бакальчук продал 1% доли в Wildberries Татьяне Ким, декабрь 2025):
дельта-поиск нашёл, что после сделки Бакальчук возглавил «М.Видео»
(гендиректор с марта 2026, пришёл в компанию в конце августа 2025) и
строит на его базе маркетплейс-конкурента Wildberries (оборот за первое
полугодие 2026 — 17,7 млрд ₽, рост в 4 раза), а также зарегистрировал
ООО «ВБ Ритейл» и вошёл в совет директоров «ВсеИнструменты.ру». Судебный
раздел имущества обязал его выплатить Ким 217 млн ₽ компенсации за то,
что доставшееся ему имущество (в т.ч. «ВБ Девелопмент») превысило его
долю — «ВБ Девелопмент» признан банкротом в марте 2026 года по иску
подрядчика. Конфликт продолжился уже в новой форме: в марте 2026
Бакальчук как гендиректор «М.Видео» подал жалобу на Wildberries в ФАС.
Не через review.py: цитаты из НЕСКОЛЬКИХ новых источников за разные
месяцы 2026 года объединены в связный абзац.

Запуск: python3 pipeline/fix_bakalchuk_kim_wildberries_aftermath_context.py
        python3 pipeline/fix_bakalchuk_kim_wildberries_aftermath_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcdf7065a'

OLD_CONTEXT = (
    'В прошлом году произошло объединение активов маркетплейса и '
    'рекламной группы Russ - по итогам которого было учреждено ООО «РВБ» '
    '(на 65% принадлежит ООО «Вайлдберриз», остальное у ООО «Стинн», '
    'которое ранее являлось компанией-владельцем Russ). Бакальчук '
    'выступил против сделки и пытался ее оспорить в судебной плоскости.'
)
CONTEXT_ADDITION = (
    ' После сделки Бакальчук возглавил ритейлера «М.Видео» (гендиректор '
    'с марта 2026 года) и строит на его базе маркетплейс-конкурента '
    'Wildberries — оборот за первое полугодие 2026 года превысил '
    '17,7 млрд ₽, увеличившись примерно в четыре раза; также вошёл в '
    'совет директоров «ВсеИнструменты.ру» и зарегистрировал ООО «ВБ '
    'Ритейл». По условиям раздела имущества Бакальчук был обязан '
    'выплатить Ким 217 млн ₽ компенсации, поскольку доставшееся ему '
    'имущество (включая компанию «ВБ Девелопмент») превысило его долю — '
    '«ВБ Девелопмент» признана банкротом в марте 2026 года по иску '
    'подрядчика. Конфликт продолжился в новой форме: в марте 2026 года '
    'Бакальчук как гендиректор «М.Видео» подал жалобу на Wildberries в '
    'ФАС.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2026-03-13_byvshij_muzh_tatyany_kim_i'],
    ['IF24', 'https://www.if24.ru/bakalchuk-stroit-konkurenta-vajldberriz/'],
    ['Shoppers Media', 'https://shoppers.media/news/27294_sud-priznal-bankrotom-vb-development-vladislava-bakalcuka'],
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
