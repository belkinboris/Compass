# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ga75a4d0a (ГК «Евроонко»
покупает московскую клинику «Юниклиник»): дельта-поиск нашёл, что сделка
ДАВНО закрыта формально — по ЕГРЮЛ 20 июня 2025 года «812 Капитал» стал
100% учредителем ООО «Юни Медика», сменив ДВУХ прежних совладельцев (по
50% каждый), а не одного, как было записано. СМИ (Коммерсантъ,
Медвестник) независимо подтверждают покупку как свершившуюся: клиника
описана подробнее (стационар на 20 коек, реанимация, операционный блок,
>7 тыс. кв. м), а прямым покупателем выступило АО «Тетра» — структура
Евгения Туголукова, конечного бенефициара «Евроонко». Статус карточки
(«Обсуждается») и продавец (только один из двух Ферoянов) были неверны
больше года.

Запуск: python3 pipeline/fix_evroonko_uniklinik_closed.py
        python3 pipeline/fix_evroonko_uniklinik_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga75a4d0a'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2025-01-22'
NEW_DATE = '2025-06-20'

OLD_SELLER = 'Роман Фероян'
NEW_SELLER = 'Роман Суренович Фероян и Шеке Синотович Фероян'

OLD_STRUCT = (
    'ЕК Менеджмент» 16 января стала управляющей организацией ООО «Юни '
    'медика», которому принадлежит московская клиника «Юнимедик», '
    'следует из данных «СПАРК-Интерфакса». Конечные владельцы «ЕК '
    'Менеджмент» – «812 капитал» и «Центр инновационных медицинских '
    'технологий», управляющие сетью специализированных онкоцентров, '
    'работающих под брендом «Евроонко».'
)
STRUCT_ADDITION = (
    ' По данным ЕГРЮЛ, 20 июня 2025 года ООО «812 Капитал» стало 100% '
    'учредителем ООО «Юни Медика» — доли обоих прежних совладельцев '
    '(Романа и Шеке Феронянов, по 50% каждый) изменились на 0%. Прямым '
    'покупателем выступило АО «Тетра» — структура Евгения Туголукова, '
    'конечного бенефициара «Евроонко».'
)
NEW_STRUCT = OLD_STRUCT + STRUCT_ADDITION

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Клиника располагает стационаром на 20 коек, реанимацией и '
    'операционным блоком; общая площадь помещений комплекса превышает 7 '
    'тыс. кв. м. Официальная сумма сделки не раскрывалась, эксперты '
    'оценивают актив в 1,2–2 млрд руб.'
)

NEW_SRC = [
    ['tbank.ru', 'https://www.tbank.ru/business/contractor/legal/1207700193282/'],
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8463640'],
    ['medvestnik.ru', 'https://medvestnik.ru/content/news/ukrupnyaisya-sam-ili-dai-drugomu-sliyaniya-i-poglosheniya-na-rynke-meduslug-rossii-za-2025-god.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['seller'] == OLD_SELLER
    assert deal['law']['struct'] == OLD_STRUCT
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== status ===', NEW_STATUS)
    print('=== date ===', NEW_DATE)
    print('=== seller ===', NEW_SELLER)
    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['seller'] = NEW_SELLER
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
