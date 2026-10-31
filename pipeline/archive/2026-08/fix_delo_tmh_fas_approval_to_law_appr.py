# -*- coding: utf-8 -*-
"""Карточка g24e6d8ee (ТМХ/Дело/Шишкарев): предыдущий скрипт
(`fix_delo_tmh_rosatom_jv_reversed.py`) дописал в `eco.context` факт о
согласовании ФАС обратного выкупа 1% — `test_approval_is_not_left_in_
prose` справедливо это отклонил (упомянут госорган ФАС + слово
«согласование» в прозе, а `law.appr` при этом оставался заглушкой). Тот
же класс, что уже чинился для сестринской карточки g6a4b0a2a
(`fix_shishkarev_delo_fas_approval_to_law_appr.py`) — переносит ИМЕННО
согласование ФАС в `law.appr`, остальной текст `eco.context` не трогает.

Запуск: python3 pipeline/fix_delo_tmh_fas_approval_to_law_appr.py
        python3 pipeline/fix_delo_tmh_fas_approval_to_law_appr.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g24e6d8ee'

FAS_SENTENCE = ', после согласования ФАС,'

OLD_CONTEXT = (
    'В конце декабря 2024 года доля Шишкарева в УК «Дело» сократилась с '
    '51% до 50%. Новым совладельцем компании с долей в 1% стало ООО '
    '«Р-Альянс». АО «Атомэнергопром» (структура госкорпораци «Росатом») '
    'осталось владельцем 49%. Планы объединения логистических активов не '
    'реализовались: «Росатому» и ТМХ не удалось договориться о цене доли '
    '«Росатома» в УК «Дело» (оценивалась не менее чем в 200 млрд ₽), и в '
    'ноябре 2025 года стороны признали, что сделка не состоится. '
    'Первоначальная продажа 1% предусматривала обратный выкуп на такой '
    'случай: 25 февраля 2026 года, после согласования ФАС, Шишкарев '
    'вернул себе этот 1% УК «Дело» и вновь стал владельцем 51%. Это '
    'положило начало отдельному сюжету: позже в 2026 году Шишкарев сам '
    'обсуждал выкуп 49% «Росатома» с перепродажей «Ростеху», затем '
    'отказался, и далее уже сам «Росатом» рассматривал выкуп доли '
    'Шишкарева (см. карточку о выкупе 49% УК «Дело» «Росатомом»).'
)
NEW_CONTEXT = OLD_CONTEXT.replace(
    '25 февраля 2026 года, после согласования ФАС, Шишкарев вернул',
    '25 февраля 2026 года Шишкарев вернул',
)

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'Обратный выкуп 1% УК «Дело» Шишкаревым у ТМХ был согласован ФАС в '
    'январе 2026 года.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['law']['appr'] == OLD_APPR, \
        f"law.appr: неожиданное значение {deal['law']['appr']!r}"

    print('=== eco.context: ФАС-упоминание вырезано ===')
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
