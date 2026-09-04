# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `gf1f6fbce`
(«Объединенная чайная компания приобрела бренд 'Беседа' у Ekaterra»,
закрыта, 2023) — дочитывание нашло оценку суммы сделки (поле было
пустым), явный список товарных знаков в предмете сделки и историю
завода в Петербурге.

Проверено (по докладу саб-агента, дословные цитаты):
- kommersant.ru/doc/5874836 (через incrussia.ru/news/pokypka-fabriki-
  ekaterra/): «По словам одного из источников "Ъ", активы оценивались
  примерно в 750 млн руб.» — единственная найденная оценка суммы,
  официально сделка её не раскрывала.
- interfax.ru/business/892079: «ФАС удовлетворила ходатайство ООО
  «Объединенная чайная компания» о приобретении основных производственных
  средств и нематериальных активов ООО «Экатерра»», включая товарные
  знаки Lipton, Saito, Brooke Bond — то есть предметом были не только
  бренд «Беседа» и завод, но и права на другие товарные знаки Ekaterra.
- kommersant.ru/doc/5491480: завод в Петербурге работал «с 2002 года»,
  площадью «4 тыс. кв. м», в 2019 году занимал «второе место в Европе»
  по объёмам производства чая, штат — «100 сотрудников».

НЕ ВНЕСЕНО: (1) юридический/финансовый консультант со стороны продавца
(Ekaterra/Unilever) — ноль по более чем 10 проверенным источникам
(Коммерсантъ ×3, РБК, Ведомости, Forbes, dp.ru, retail.ru, Интерфакс,
TAdviser, incrussia.ru, shoppers.media, mergers.ru, vc.ru, пресс-релизы
Unilever); (2) точные объёмы производства/продаж бренда «Беседа» после
перезапуска — источники говорят только «производство началось», без
цифр; (3) судьба завода/бренда после 2023 года — последняя найденная
финансовая точка (выручка 1,5 млрд ₽, убыток 73,9 млн ₽ за 2024 год) —
это финансы ВСЕЙ ОЧК, а не именно бренда «Беседа» или этого завода,
смешивать нельзя.

Запуск: python3 pipeline/fix_ochk_beseda_valuation_and_trademarks.py
        python3 pipeline/fix_ochk_beseda_valuation_and_trademarks.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf1f6fbce'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Официально сумма не раскрывалась. По оценке источника «Ъ», близкого '
    'к сделке, активы Ekaterra в России оценивались примерно в 750 млн ₽.'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'ФАС одобрила приобретение не только бренда «Беседа», но и прав на '
    'другие товарные знаки Ekaterra в России — Lipton, Saito, Brooke '
    'Bond — вместе с основными производственными средствами завода.'
)

OLD_ECO_CONTEXT = (
    'По данным ЕГРЮЛ, Александру Конову принадлежит 50%, ещё по 25% — '
    'Александру и Ларисе Прониным. Пронин раньше руководил '
    'спорткомплексом «Лужники» и был первым вице-президентом АвтоВАЗа, а '
    'по неофициальным данным работал советником главы «Ростеха» Сергея '
    'Чемезова.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Сам завод в Петербурге работает с 2002 года '
    '(площадь около 4 тыс. кв. м, штат — около 100 человек) и в 2019 '
    'году занимал второе место в Европе по объёму производства чая.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
