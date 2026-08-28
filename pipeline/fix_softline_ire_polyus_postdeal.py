# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g00773994 (Softline
приобрела контроль в производителе лазеров ИРЭ-Полюс у IPG Photonics):
дельта-поиск нашёл переименование цели и точную структуру собственности
после сделки — карточка знала только «Softline владеет мажоритарной
долей», без цифр. Все цитаты подтверждены лично прямым WebFetch.

1. С 7 марта 2025 года НТО «ИРЭ-Полюс» переименовано в VPG LaserONE
   (Softline.ru).
2. Точная структура холдинга ООО «БВПГ»: «Софтлайн Проекты» — 60%,
   Николай Евтихиев (гендиректор, на посту с 2019 года) — 19%, Артур
   Андреев — 11,5%, Светлана Алхименко — 4,8%, Евгений Серков — 4,7%
   (ComNews, со ссылкой на данные ЕГРЮЛ).
3. Уточнённая сумма сделки в валюте: «за 100% долей... покупатели
   заплатили $51,096 млн» — по курсу на 29.08.2024 это 4,67 млрд руб.,
   близко к уже стоящим в карточке 4,5 млрд ₽, но точнее (ComNews со
   ссылкой на годовой отчёт IPG Photonics).

Консультантов сделки и независимую оценку суммы дельта-поиск не нашёл ни
в одном источнике — честная пустота, не тронуто. Финансовые показатели
2025 года (выручка 7,3 млрд ₽) НЕ включены: единственный найденный
источник — пост частного автора в соцсети брокера, не редакционная
статья, дословную цитату подтвердить не удалось.

Запуск: python3 pipeline/fix_softline_ire_polyus_postdeal.py
        python3 pipeline/fix_softline_ire_polyus_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g00773994'

OLD_CONTEXT = (
    'Научно-техническое предприятие «ИРЭ-Полюс», основанное в 1991 г. '
    'российским ученым-физиком Валентином Гапонцевым, стало фундаментом '
    'и базовой компанией международной группы «IPG Photonics '
    'Corporation», представленной в России, Германии, США, Италии и '
    'других странах мира.'
)
CONTEXT_ADDITION = (
    ' С 7 марта 2025 года компания переименована в VPG LaserONE '
    '(Softline.ru). Точная структура собственности холдинга ООО «БВПГ»: '
    '«Софтлайн Проекты» — 60% уставного капитала, а среди четырёх '
    'физлиц-совладельцев — гендиректор Николай Евтихиев (19%, на посту с '
    '2019 года), Артур Андреев (11,5%), Светлана Алхименко (4,8%) и '
    'Евгений Серков (4,7%). Уточнённая сумма сделки: «за 100% долей... '
    'покупатели заплатили $51,096 млн» — эквивалент 4,67 млрд руб. по '
    'курсу на 29.08.2024, по данным годового отчёта IPG Photonics '
    '(ComNews).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Softline.ru', 'https://softline.ru/about/news/gk-softline-obyavlyaet-o-smene-nazvaniya-kompanii-nto-ire-polyus-na-vpg-laserone-s-7-marta-2025-goda'],
    ['ComNews', 'https://www.comnews.ru/content/238253/2025-03-14/2025-w11/1008/ire-polyus-zasvetilsya-kak-vpg-laserone'],
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
