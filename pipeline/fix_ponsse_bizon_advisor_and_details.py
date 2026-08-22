# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g99be4c1d (Ponsse/«Бизон»,
Хабаровск): месячный обыск нашёл юридического консультанта продавца —
факт был не в русскоязычных источниках карточки, а на английском сайте
самой юрфирмы и в пресс-релизе Ponsse. Дословная цитата на английском,
перевод — тем же приёмом, что уже применён в базе для иностранных
пресс-релизов (например, ALUMNI Partners/Denuo — «перевод с английского»
в подписи источника), а не через review.py, чья проверка дословности не
работает между языками.

Источники (уже забраны в кэш этой же сессией):
  https://www.borenius.com/references/borenius-advised-ponsse-on-the-divestment-of-its-subsidiary-in-russia/
    «Borenius advised Ponsse Plc... on the divestment of its subsidiary
    OOO Ponsse in Russia»; названы юристы — Erkko Korhonen (partner) и
    Juho Keinänen (advisor), оба из Хельсинки.
  https://www.ponsse.com/company/news/a_p/P4s3zYhpxHUQ/c/ponsse-divests-its-subsidiary-in-russia
    «The buyer OOO Bison is owned by Aleksey Voronkevich, whose company
    Dormashimport has been responsible for the retail of PONSSE forest
    machines in the eastern parts of Russia since 2007.» — точное
    название компании Воронкевича («Дормашимпорт»), которого не было в
    `extra` (там только «занимался розничной продажей» без юрлица).

Также найдено само подтверждение официального отказа сторон раскрывать
сумму («The companies will not disclose the price of the transaction.»)
— это не новый факт для поля `sum` (там уже честно стоит «Не раскрыта»),
а подтверждение того, что это позиция сторон, а не пробел разбора;
отдельно фиксировать не стал, чтобы не плодить то же самое во втором
поле.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g99be4c1d'
OLD_ADV = [['Стороны сделки', 'Не раскрывались',
            'Юридические консультанты в публичных источниках не раскрывались']]
NEW_ADV = [['Юридический консультант продавца (Ponsse Plc)', 'Borenius',
            'Borenius advised Ponsse Plc on the divestment of its '
            'subsidiary OOO Ponsse in Russia; команда — партнёр Erkko '
            'Korhonen и советник Juho Keinänen (перевод с английского, '
            'borenius.com)']]
OLD_EXTRA = ('Сделка по продаже российского бизнеса финской Ponsse Pls '
             '(ООО «Понссе» и ООО «Понссе-Центр») российской компании '
             '«Бизон» из Хабаровска. Владелец покупателя — Алексей '
             'Воронкевич, ранее занимавшийся розничной продажей техники '
             'Ponsse на Дальнем Востоке более 15 лет.')
NEW_EXTRA = ('Сделка по продаже российского бизнеса финской Ponsse Pls '
             '(ООО «Понссе» и ООО «Понссе-Центр») российской компании '
             '«Бизон» из Хабаровска. Владелец покупателя — Алексей '
             'Воронкевич, чья компания «Дормашимпорт» занималась '
             'розничной продажей лесозаготовительной техники Ponsse на '
             'востоке России с 2007 года (перевод с английского, '
             'пресс-релиз Ponsse).')
NEW_SRC_1 = ['Borenius (перевод с английского)',
             'https://www.borenius.com/references/borenius-advised-ponsse-on-the-divestment-of-its-subsidiary-in-russia/']
NEW_SRC_2 = ['Ponsse Plc (перевод с английского)',
             'https://www.ponsse.com/company/news/a_p/P4s3zYhpxHUQ/c/ponsse-divests-its-subsidiary-in-russia']


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['adv'] == OLD_ADV, f"law.adv: неожиданное значение {deal['law']['adv']!r}"
    assert deal['extra'] == OLD_EXTRA, f"extra: неожиданное значение {deal['extra']!r}"
    assert NEW_SRC_1 not in deal['src'] and NEW_SRC_2 not in deal['src']

    print(f"{CARD_ID} law.adv: заменён плейсхолдер на консультанта Borenius")
    print(f"{CARD_ID} extra: добавлено юрлицо покупателя («Дормашимпорт»)")
    print(f"{CARD_ID} src += 2 новых источника (перевод с английского)")

    deal['law']['adv'] = NEW_ADV
    deal['extra'] = NEW_EXTRA
    deal['src'].append(NEW_SRC_1)
    deal['src'].append(NEW_SRC_2)

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
