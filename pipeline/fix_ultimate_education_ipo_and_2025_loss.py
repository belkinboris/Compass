# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gd96404f2` («Vershina Capital инвестировала в холдинг Ultimate
Education», 2022, Закрыта) — судьба холдинга после раунда не
прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- vedomosti.ru/investments/news/2024/10/08/1067183-ultimate-education-planiruet:
  гендиректор Павел Мосекин — холдинг «планирует выйти на биржу в
  ближайшие два-три года», готовится через pre-IPO и облигации; аналитик
  Алексей Примак оценивал компанию в 2–2,5 млрд ₽;
- akm.ru/news/ubytok_ultimate_education_za_2025_god_po_msfo_sostavil_179_951_mln_rub/:
  «Убыток Ultimate Education за 2025 год по МСФО составил 179,951 млн
  руб. против прибыли 366,486 млн руб. годом ранее»; «Выручка снизилась
  на 24,2% до 1,867 млрд руб.».

НЕ ВНЕСЕНО: точная сумма, привлечённая на pre-IPO (упоминались 565 млн ₽
и 600 млн ₽ заявок в разных источниках) — встретилась только в
агрегированной выдаче поиска, не в дословно прочитанной странице;
сделка по выкупу 18% Fashion Factory School — тоже только сниппет, не
проверено лично.

Запуск: python3 pipeline/fix_ultimate_education_ipo_and_2025_loss.py
        python3 pipeline/fix_ultimate_education_ipo_and_2025_loss.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd96404f2'

OLD_ECO_CONTEXT = 'Годовая выручка холдинга в пересчёте по итогам Q3 превышает 1,2 млрд р.'
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Холдинг готовился к IPO — в 2024 году гендиректор '
    'говорил о выходе на биржу «в ближайшие два-три года» через pre-IPO и '
    'облигации, — но 2025 год оказался убыточным: выручка упала на 24,2%, '
    'до 1,867 млрд ₽, а прибыль 366,5 млн ₽ годом ранее сменилась '
    'убытком 180 млн ₽ по МСФО.'
)

OLD_SRC = [
    ['@dealsma (Telegram)', 'https://t.me/dealsma/3628'],
]
NEW_SRC = OLD_SRC + [
    ['Ведомости', 'https://www.vedomosti.ru/investments/news/2024/10/08/1067183-ultimate-education-planiruet'],
    ['АК&М', 'https://www.akm.ru/news/ubytok_ultimate_education_za_2025_god_po_msfo_sostavil_179_951_mln_rub/'],
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
