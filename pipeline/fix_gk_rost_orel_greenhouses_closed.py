# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g42f3065c` («ГК «РОСТ» планирует выкупить два тепличных комплекса в
Орловской области», январь 2023, «Обсуждается») — сделка закрылась,
собственная карточка уже несла факт одобрения ФАС в `eco.rationale`, но
статус не был обновлён.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- rostgroup.ru/press/rost-rasshiryaet-geografiyu-i-pokupaet-teplichnyy-kompleks-ekoprodukt-v-orlovskoy-oblasti-
  (25.01.2023, официальный пресс-релиз самого покупателя): «"ЭкоПродукт"
  стал 17-м комбинатом холдинга "РОСТ"»;
- rostgroup.ru/greenhouses/uspensky/ и rostgroup.ru/greenhouses/kumir/
  (текущее состояние сайта покупателя): оба комплекса — «ЭкоПродукт»
  (пос. Успенский) и «Кумир» — числятся действующими активами группы
  «РОСТ» в разделе тепличных комбинатов.

Внесено: `status` меняется с «Обсуждается» на «Закрыта» — не через
`review.py`/FIXES (источники не в локальном кэше притока), а прямым
скриптом с `assert`. Собственное объявление покупателя о том, что актив
«стал» его комбинатом, — прямое подтверждение закрытия, без
домысливания.

НЕ ВНЕСЕНО: точная дата фактической передачи долей (пресс-релиз ROST
её не называет, только дату публикации) и сумма сделки — ни один из
проверенных источников её не раскрывает.

Запуск: python3 pipeline/fix_gk_rost_orel_greenhouses_closed.py
        python3 pipeline/fix_gk_rost_orel_greenhouses_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g42f3065c'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_ECO_CONTEXT = (
    'В 2021 году группа купила убыточные «Теплицы Белогорья», а в 2020-м '
    'объединила активы с липецкой «Долиной овощей».'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Сделка закрылась: в собственном пресс-релизе от '
    '25 января 2023 года «РОСТ» сообщил, что «ЭкоПродукт» стал 17-м '
    'комбинатом холдинга; оба комплекса, «ЭкоПродукт» и «Кумир», по сей '
    'день числятся действующими активами группы.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5785646'],
]
NEW_SRC = OLD_SRC + [
    ['ГК «РОСТ»', 'https://rostgroup.ru/press/rost-rasshiryaet-geografiyu-i-pokupaet-teplichnyy-kompleks-ekoprodukt-v-orlovskoy-oblasti-/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
