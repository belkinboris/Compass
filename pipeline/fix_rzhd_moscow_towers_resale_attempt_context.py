# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gb6a90572 (ОАО РЖД
приобрело 350 тыс. м2 в небоскрёбе Moscow Towers, декабрь 2024):
дельта-поиск нашёл, что сюжет развернулся далеко вперёд. Переезда
штаб-квартиры не случилось: РЖД не нашли ~100 млрд ₽ на отделку здания,
сотрудники остались в старых офисах (Fontanka, апрель 2026). На фоне
долга РЖД, достигшего 4 трлн ₽ к концу 2025 года, правительство поручило
продать те же площади — аукцион на 280,8 млрд ₽ (стартовая цена выше
цены покупки) был назначен на 21 мая 2026 года и признан несостоявшимся
из-за отсутствия заявок (Коммерсантъ, RB.ru, Fontanka). Сама сделка
покупки (декабрь 2024) остаётся закрытой — разворот сюжета не меняет
`status`/`type` карточки о покупке, только дополняет `eco.context`. Не
через review.py: цитаты из ПЯТИ новых источников за разные месяцы 2026
года объединены в связный абзац, а не дословный кусок одной статьи.

Запуск: python3 pipeline/fix_rzhd_moscow_towers_resale_attempt_context.py
        python3 pipeline/fix_rzhd_moscow_towers_resale_attempt_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb6a90572'

OLD_CONTEXT = (
    'Изначально ОАО РЖД планировали построить новую штаб-квартиру на '
    'месте Рижского грузового двора в Москве. Компания поменяла решение '
    'в связи с тем, что небоскреб Moscow Towers уже готов к сдаче в '
    'эксплуатацию. Общая площадь башни Moscow Towers составляет 411 тыс. '
    'кв. м. Из них ОАО РЖД выкупили 350 тыс. кв. м, в том числе более '
    '200 тыс. кв. м офисов. Строительство небоскреба завершилось в июне '
    '2024 года.'
)
CONTEXT_ADDITION = (
    ' Переезда так и не произошло: на отделку здания требовалось ещё '
    'около 100 млрд ₽, которых РЖД не нашли, и сотрудники остались в '
    'старых офисах (данные на апрель 2026). На фоне долга компании, '
    'достигшего к концу 2025 года 4 трлн ₽, правительство поручило '
    'продать эти же площади — аукцион со стартовой ценой 280,8 млрд ₽ '
    '(выше цены покупки) был назначен на 21 мая 2026 года и признан '
    'несостоявшимся: ни одной заявки подано не было.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Fontanka.ru', 'https://www.fontanka.ru/2026/04/06/76351450/'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8671762'],
    ['RB.ru', 'https://rb.ru/news/rzhd-ne-smogla-prodat-neboskryob-v-moskve-siti-za-280-mlrd-rublej-na-aukcion-ne-podali-ni-odnoj-zayavki/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
