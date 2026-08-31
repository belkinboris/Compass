# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g0ab7863c (Продажа бизнес-центра «Белая площадь» компании «МБП») —
карточка несла год 2024, хотя сделка закрылась в конце августа 2025
года, а единственный источник был Telegram-агрегатором. Проверено
лично прямым WebFetch двух источников.

Год сделки (2024 → 2025) — НЕ через `review.py` (смена года — отдельный
скрипт). Дословно (РИА Недвижимость, 29.08.2025, 11:05): «Связанная со
Сбербанком компания МБП стала победителем торгов по продаже актива
инвесткомпании O1 Properties — бизнес-центра "Белая площадь"», «МБП
получит актив за 46,5 миллиарда рублей (при начальной цене почти 62
миллиарда рублей)» — независимо подтверждено CRE.ru и МСК1.ру той же
датой.

`src` заменён: `@dealsma` — на РИА Недвижимость (первоисточник факта и
суммы).

`eco.context` (дополнено). Дословно (Ведомости, 22.10.2025): «"Яндекс"
ведет переговоры с УК "Современные фонды недвижимости" (СФН, ранее
принадлежала структурам Сбербанка) об аренде офисных площадей в
бизнес-центре "Белая площадь"» — ответ на открытый в карточке вопрос
«что Сбербанк будет делать с "Белой площадью"».

НЕ ВКЛЮЧЕНО: сюжет о массовом уходе действующих арендаторов из-за
повышения ставок (Москвич Mag, 23.01.2026) и упаковка актива в ЗПИФ с
целевой доходностью 19,5% (vc.ru, январь 2026, имя оценочной компании
не названо явно) — оба факта существенны, но требуют отдельной,
самостоятельной проверки цитат перед внесением (особенно vc.ru — не
перепроверено дословно вторым чтением); имя продавца (O1 Properties)
уже перенесено в контекст выше, но структурные поля `seller`/`target`
карточки не переписаны — решение об этом за отдельным заходом.
Структура/бенефициары МБП, завершение банкротства «Квартал 674–675» и
консультанты сделки — не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_belaya_ploshchad_year_and_tenant.py
        python3 pipeline/fix_belaya_ploshchad_year_and_tenant.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0ab7863c'

OLD_DATE = '2024'
NEW_DATE = '2025'

OLD_SRC = [['@dealsma (Telegram)', 'https://t.me/dealsma/6306']]
NEW_SRC = [
    ['РИА Недвижимость', 'https://realty.ria.ru/20250829/mbp-2038271423.html'],
]

OLD_CONTEXT = (
    'Она стала крупнейшей в этом году (если не считать продажу '
    'Malltech, но там совсем все не ясно). Теперь осталось понять, что '
    'Сбербанк будет делать с «Белой площадью».'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Ответ появился позже: «"Яндекс" ведет переговоры с УК '
    '"Современные фонды недвижимости" (СФН, ранее принадлежала '
    'структурам Сбербанка) об аренде офисных площадей в бизнес-центре '
    '"Белая площадь"» (Ведомости, 22 октября 2025).'
)

NEW_SRC_VEDOMOSTI = ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/10/22/1149003-struktura-nashla-arendatora']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['src'] == OLD_SRC
    assert deal['eco']['context'] == OLD_CONTEXT

    all_new_src = NEW_SRC + [NEW_SRC_VEDOMOSTI]

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== src: станет ===')
    for s in all_new_src:
        print(s)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['date'] = NEW_DATE
        deal['src'] = all_new_src
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
