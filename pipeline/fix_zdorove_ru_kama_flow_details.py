# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gbdec3442` («"Здоровье.ру" привлекла 307 млн рублей инвестиций»,
март 2023) — `eco.val` пустовал, хотя аудитория сервиса и состав
со-инвесторов раунда названы в открытых источниках.

Проверено лично прямым WebFetch:
- Медвестник, https://medvestnik.ru/content/news/Platforma-Zdorove-ru-privlekla-300-mln-rublei-investicii.html:
  «Аудитория сервисов составляет около 600 тыс. человек.»; «Лид-
  инвестором выступила инвестиционная компания Kama Flow, также в
  сделке приняли участие инвесторы венчурного клуба «Синдикат».»

Отдельно проверена и НЕ внесена (уже верно отражена в карточке)
находка о судьбе более раннего раунда с «Медси» (февраль 2022, 135
млн ₽, 12% доли): между источниками есть расхождение — vc.ru
утверждает, что сделка ЗАВЕРШИЛАСЬ («доля в итоге достигла 12%»,
проверено лично прямым WebFetch), а Медвестник, Vademecum и spark.ru
(по докладу саб-агента) независимо утверждают, что сделка была
«заморожена и впоследствии расторгнута». Уже стоящий в карточке текст
(`eco.context`) верно следует версии большинства источников
(«расторгнута») — она же подтверждается косвенно текущим составом
учредителей по агрегатору list-org.com (Медси среди них не значится).
Менять текст не требуется — правка НЕ вносится, только фиксируется
здесь как проверенный факт.

НЕ ВНЕСЕНО: точная доля Kama Flow и со-инвесторов «Синдиката» в этом
раунде (307 млн ₽) — ни один источник её не называет; выручка ~100
млн ₽ (cnews.ru, spark.ru) без ясного указания года — не вносится,
чтобы не приписать цифру не тому году (родня урока «Число может быть
верным фактом и совсем не той величиной»); развитие компании после
2023 года — WebSearch за 2024-2026 годы не нашёл ни новых раундов, ни
поглощения, ни закрытия.

Запуск: python3 pipeline/fix_zdorove_ru_kama_flow_details.py
        python3 pipeline/fix_zdorove_ru_kama_flow_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gbdec3442'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Аудитория сервисов «Здоровье.ру» — около 600 тыс. человек. Кроме'
    ' лид-инвестора Kama Flow, в раунде участвовали инвесторы'
    ' венчурного клуба «Синдикат».'
)

NEW_SRC = [
    ['Медвестник', 'https://medvestnik.ru/content/news/Platforma-Zdorove-ru-privlekla-300-mln-rublei-investicii.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
