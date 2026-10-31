# -*- coding: utf-8 -*-
"""Карточка g9995eb50 («Страна девелопмент»/Марьино, ЦФТ): предыдущий
скрипт (`fix_strana_marino_project_name_context.py`) дописал в
`eco.context` факт об одобрении сделки советом директоров покупателя —
`test_approval_is_not_left_in_prose` справедливо это отклонил (упомянут
орган «совет директоров» + слово «одобрение» в прозе, а `law.appr» при
этом оставался заглушкой). Тот же класс, что уже чинился для g24e6d8ee и
g6a4b0a2a (`fix_delo_tmh_fas_approval_to_law_appr.py`,
`fix_shishkarev_delo_fas_approval_to_law_appr.py`) — переносит ИМЕННО
согласование в `law.appr`, остальной текст `eco.context` не трогает.

Запуск: python3 pipeline/fix_strana_marino_board_approval_to_law_appr.py
        python3 pipeline/fix_strana_marino_board_approval_to_law_appr.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9995eb50'

OLD_CONTEXT = (
    'Сумма 8,8 млрд ₽ — оценка октября 2022 года, сделанная на этапе '
    'одобрения сделки советом директоров покупателя («Ведомости»: '
    '«покупная цена за 100% ЦФТ не должна превышать 8,8 млрд руб.»); '
    'независимого источника с итоговой ценой на момент закрытия в '
    'декабре 2024 года не нашлось. Прямым покупателем выступило ООО '
    '«Элит строй», принадлежащее «Стране девелопмент». Строительство '
    'первой очереди начато: разрешение получено в августе 2024 года, '
    'продажи стартовали в октябре того же года. Проект называется '
    '«Страна.Заречная» (рабочее название «Страна.Иловайская»), '
    'застройщик по проектной декларации — АО «Специализированный '
    'застройщик «Деметра»» (структура, которой ранее принадлежали '
    'участки ЦФТ); строительство разделено на три очереди со сроком '
    'завершения к 2030 году.'
)
NEW_CONTEXT = OLD_CONTEXT.replace(
    ' — оценка октября 2022 года, сделанная на этапе одобрения сделки '
    'советом директоров покупателя («Ведомости»: «покупная цена за 100% '
    'ЦФТ не должна превышать 8,8 млрд руб.»);',
    ' — оценка октября 2022 года («Ведомости»: «покупная цена за 100% '
    'ЦФТ не должна превышать 8,8 млрд руб.»);',
)

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'Сделку в октябре 2022 года одобрил совет директоров покупателя '
    '(«Элит строй»/«Страна девелопмент»).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['law']['appr'] == OLD_APPR, \
        f"law.appr: неожиданное значение {deal['law']['appr']!r}"

    print('=== eco.context: одобрение вырезано ===')
    print(NEW_CONTEXT)
    print('=== law.appr: станет ===')
    print(NEW_APPR)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['law']['appr'] = NEW_APPR
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
