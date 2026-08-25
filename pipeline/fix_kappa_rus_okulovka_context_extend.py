# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gc215d8b0 («Каппа РУС»
приобрела Окуловскую бумажную фабрику): дельта-поиск нашёл цель сделки
(вертикальная интеграция), контекст продавца (фабрика вышла из ГК
«Росмарк» в январе 2025) и первый пост-сделочный инвестпроект новых
владельцев (соглашение на ПМЭФ-2026, 120 млн ₽ на линию формованной
бумажной массы). Точная сумма сделки по-прежнему нигде не названа. Не
через review.py: цитаты из ТРЁХ новых источников (kapparus.ru, rosmark.ru,
okulovka.com) в поле, уже содержащем текст из другого источника.

Запуск: python3 pipeline/fix_kappa_rus_okulovka_context_extend.py
        python3 pipeline/fix_kappa_rus_okulovka_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc215d8b0'

OLD_CONTEXT = (
    'Новый владелец — АО «Каппа РУС» — образован в результате '
    'реорганизации ОАО «Производственно-экспериментальная фабрика '
    '«СОЮЗ»». В мае 2017 года компания была продана Smurfit Kappa '
    'Packaging Sweden Aktiebolag. В марте 2023 года группа Smurfit Kappa '
    'ушла с российского рынка, продав 100% акций шведской компании с '
    'одним сотрудником Sverige International Holdings AB. Бенефициарным '
    'владельцем называется швед Стром Юн-Улов Патрик.'
)
CONTEXT_ADDITION = (
    ' Приобретение фабрики стало шагом в стратегии вертикальной '
    'интеграции «Каппа РУС» — компания рассчитывает объединить '
    'последовательные этапы производственного процесса. В январе 2025 '
    'года фабрика вышла из состава группы компаний «Росмарк», а 14 '
    'февраля 2025 года была переименована в ООО «Каппа Рус Окуловка». В '
    'июне 2026 года на ПМЭФ подписано соглашение о модернизации '
    'производства — установке автоматической линии по выпуску '
    'формованной бумажной массы и упаковки для яиц (около 3,2 млн '
    'контейнеров в месяц), объём инвестиций 120 млн руб., срок '
    'реализации — до конца 2026 года.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['kapparus.ru', 'https://kapparus.ru/kompaniya-ao-kappa-rus-priobrela-ooo-okulovskaya-bumazhnaya-fabrika-rasshiryaya-biznes-i-ukreplyaya-liderskie-poziczii-v-otrasli/'],
    ['rosmark.ru', 'https://www.rosmark.ru/news/ooo-okulovskaya-bumazhnaya-fabrika-vyshla-iz-sostava-gk-rosmark-/'],
    ['okulovka.com', 'https://okulovka.com/news/10304'],
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
