# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gf962d8a9` («Российская «Инваста Капитал» купила петербургский завод
Teknos», июль 2022, Закрыта) — судьба завода после сделки не
прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- audit-it.ru/contragent/1057749663311_ooo-talatu: «В 2025 году
  среднесписочная численность работников ООО "ТАЛАТУ" составила 268
  человек. Это на 55 человек больше, чем в 2024 году»; выручка 2025
  года — «2,7 млрд руб.» с ростом «на 25,6%»; убыток 2025 года —
  «661 млн руб.».

НЕ ВНЕСЕНО: (1) состав владельцев «Инваста Капитал» после сделки —
источники противоречат друг другу (один снимок называет прежний состав
2022 года, другой — уже изменённый через ООО «КВАРК» и Дудинову Елену
Михайловну), расхождение не разрешено, требует прямой выписки ЕГРЮЛ,
не агрегатора; (2) снят ли залог долей в пользу ВТБ — не нашлось ни
подтверждения, ни опровержения; (3) точная выручка 2024 года — есть
только расчётная величина (2,145 млрд ₽, выведена из процента роста), а
не прямая цитата.

Запуск: python3 pipeline/fix_talatu_teknos_2025_financials.py
        python3 pipeline/fix_talatu_teknos_2025_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf962d8a9'

OLD_ECO_CONTEXT = (
    'Приобретённый у финской компании актив владеет земельным участком '
    'площадью 5 га в индустриальном парке «Марьино» в Петергофе, '
    'зданием и оборудованием для выпуска до 15 тыс. тонн продукции в '
    'год, а также тремя торговыми марками: «Командор» '
    '(архитектурно-строительные краски), «Охтек» (порошковые) и Massco '
    '(промышленные покрытия).'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По итогам 2025 года выручка завода выросла на '
    '25,6% до 2,7 млрд ₽, но компания осталась убыточной — убыток '
    'составил 661 млн ₽; численность выросла до 268 человек.'
)

OLD_SRC = [['Деловой Петербург', 'https://www.dp.ru/a/2022/10/26/Krasochnij_peredel?ysclid=ldhg8t1a38506310379']]
NEW_SRC = OLD_SRC + [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1057749663311_ooo-talatu'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
