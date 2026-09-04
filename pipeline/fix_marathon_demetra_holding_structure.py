# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g38ce6e22` («Выход Marathon Group из состава владельцев Деметра-
Холдинга», закрыта, 2023-08-10) — дочитывание нашло состав холдинга и
структуру параллельной сделки ВТБ (уже упомянутой в `extra`), но НЕ
подтвердило, кто именно купил долю Marathon Group/«СПН».

Проверено (по докладу саб-агента, дословные цитаты):
- kommersant.ru/doc/6149973: «В состав «Деметра-Холдинга» входят …
  «Новороссийский зерновой терминал» (100%), «Новороссийский комбинат
  хлебопродуктов» (35,36%), зерновой терминальный комплекс «Тамань»
  (50%)» — состав активов холдинга.
- vedomosti.ru/business/articles/2023/07/10/984636-u-zernotreidera-
  demetra-holding-poyavitsya-investor-iz-omana: «технически сделка
  сложноструктурированная, один из ее этапов – допэмиссия»; «оманская
  Southern Sea Investment LLC – не прямой покупатель доли ВТБ, а
  якорный инвестор» — структура параллельной сделки по доле ВТБ (45%).

ВАЖНО — НЕ ВНЕСЕНО, оставлено как есть: кто купил долю САМОЙ Marathon
Group («СПН», 10,57%). Вторичные пересказы (fomag.ru, business-vector.
info, ppress.ru, zerno.ru) складывают долю ВТБ (45%) и долю СПН
(10,57%) в «55,57%», проданных вместе Southern Sea Investment, — и
арифметика сходится, но НИ ОДИН первоисточник (Коммерсантъ, Интерфакс,
Ведомости) не называет СПН и Southern Sea в одном предложении:
Коммерсантъ и Интерфакс по этой конкретной сделке прямо пишут, что
покупатель доли СПН не назван. `buyer`/`buyer_name` карточки НЕ
заполняются на основании одной лишь арифметики — это ровно тот класс
недоказанной, но удобной находки, который CLAUDE.md просит не обменивать
на честную неопределённость.

НЕ ВНЕСЕНО также: (1) юридический/финансовый консультант — ноль по всем
проверенным источникам (Коммерсантъ, Интерфакс, Ведомости, Forbes,
agrotrend.ru, versia.ru, zerno.ru; ТАСС — 403); (2) сумма сделки — нигде
не раскрыта; (3) реестровые данные (list-org.com), по которым структура
Marathon Group ВСЁ ЕЩЁ числится учредителем холдинга — прямо
противоречат новости о выходе, требуют прямой выписки ЕГРЮЛ, а не
агрегатора, не вносятся без неё.

Запуск: python3 pipeline/fix_marathon_demetra_holding_structure.py
        python3 pipeline/fix_marathon_demetra_holding_structure.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g38ce6e22'

OLD_ECO_CONTEXT = (
    'Marathon Group вошла в капитал «Деметра-Холдинга» в 2020 году и '
    'владела 10,57% холдинга через ООО «СПН».'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В состав «Деметра-Холдинга» входят '
    '«Новороссийский зерновой терминал» (100%), «Новороссийский комбинат '
    'хлебопродуктов» (35,36%) и зерновой терминальный комплекс «Тамань» '
    '(50%).'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Параллельная сделка по доле ВТБ (45%) была сложноструктурированной '
    'и включала допэмиссию; сама оманская Southern Sea Investment LLC '
    'выступила в ней не прямым покупателем, а якорным инвестором. Кто '
    'именно выкупил долю Marathon Group («СПН», 10,57%), источники не '
    'называют.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['law']['struct'] == OLD_LAW_STRUCT

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['law']['struct'] = NEW_LAW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
