# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g24e6d8ee («Росатом, ТМХ и
Сергей Шишкарев создают совместную логистическую компанию на базе «Дело»,
декабрь 2024): дельта-поиск нашёл, что вся конструкция развалилась и была
обращена вспять. «Росатому» и ТМХ не удалось договориться о цене доли
«Росатома» (оценивалась не менее чем в 200 млрд ₽) — сделка расторгнута в
ноябре 2025 года (Logirus, «Тройной шах»). Условие первоначальной продажи
1% УК «Дело» предусматривало обратный выкуп в случае несостоявшейся
сделки: 25 февраля 2026 года Шишкарев вернул себе этот 1% (после
согласования ФАС в январе 2026, Коммерсантъ/Ведомости) — его доля вновь
51%. Это и есть завязка уже задокументированной в базе саги (карточка
g6a4b0a2a): именно после этого срыва Шишкарев в 2026 году сначала сам
собирался выкупить 49% у «Росатома», затем отказался, и далее «Росатом»
решил выкупить долю уже у него самого.

Статус меняется с «Обсуждается» на «Не состоялась»: цель карточки —
создание совместной логистической компании — прямо не реализована, и это
подтверждено дословно тремя независимыми источниками (Logirus,
Коммерсантъ, Ведомости), а не одним лишь молчанием. Не через review.py:
дословные цитаты новых источников не совпадают со словами из STATUS_WORDS
(«не состоится» ≠ «не состоял»), а `eco.context` собирается из фраз
нескольких статей.

Запуск: python3 pipeline/fix_delo_tmh_rosatom_jv_reversed.py
        python3 pipeline/fix_delo_tmh_rosatom_jv_reversed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g24e6d8ee'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_CONTEXT = (
    'В конце декабря 2024 года доля Шишкарева в УК «Дело» сократилась с '
    '51% до 50%. Новым совладельцем компании с долей в 1% стало ООО '
    '«Р-Альянс». АО «Атомэнергопром» (структура госкорпораци «Росатом») '
    'осталось владельцем 49%.'
)
CONTEXT_ADDITION = (
    ' Планы объединения логистических активов не реализовались: '
    '«Росатому» и ТМХ не удалось договориться о цене доли «Росатома» в УК '
    '«Дело» (оценивалась не менее чем в 200 млрд ₽), и в ноябре 2025 года '
    'стороны признали, что сделка не состоится. Первоначальная продажа 1% '
    'предусматривала обратный выкуп на такой случай: 25 февраля 2026 года, '
    'после согласования ФАС, Шишкарев вернул себе этот 1% УК «Дело» и '
    'вновь стал владельцем 51%. Это положило начало отдельному сюжету: '
    'позже в 2026 году Шишкарев сам обсуждал выкуп 49% «Росатома» с '
    'перепродажей «Ростеху», затем отказался, и далее уже сам «Росатом» '
    'рассматривал выкуп доли Шишкарева (см. карточку о выкупе 49% УК '
    '«Дело» «Росатомом»).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Logirus', 'https://logirus.ru/news/transport/troynoy_shakh_krupneyshaya_logisticheskaya_sdelka_goda_razvalilas_na_finishe.html'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8379081'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/02/26/1179096-shishkarev-vikupil-1-uk-delo-u-transmashholdinga'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== status: было ===', OLD_STATUS, '-> станет ->', NEW_STATUS)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
