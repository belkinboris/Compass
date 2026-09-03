# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g37066bfe` («Финская Reima продала активы в России консорциуму
Детского мира и Валан менеджмент», закрыта 28.02.2023) —
`law.struct` и `eco.target_fin` пустовали, хотя раздел долей,
обязательство ребрендинга и финансы предмета названы в открытых
источниках.

Проверено лично прямым WebFetch:
- CRE.ru, https://cre.ru/news/90158: «Выручка ООО «Рейма» за 2021 год
  составляла 5,7 млрд, чистая прибыль – 1,2 млрд рублей.»; «Покупателями
  выступили... АО «Валан менеджмент» (75%) и структура «Детского
  мира» (25%).»
- Profashion, https://profashion.ru/business/finance/finskiy-brend-detskoy-odezhdy-reima-prodal-aktivy-v-rossii/:
  «соглашение о продаже предусматривает смену названия торговой сети»
  (обязательство ребрендинга — сеть переименована в Nordy).
- audit-it.ru, https://www.audit-it.ru/contragent/1227700289002_ao-valan-menedzhment:
  решение о ликвидации АО «Валан Менеджмент» принято 11 марта 2026
  года, ликвидация завершена 3 июля 2026 года.

НЕ ВНЕСЕНО: связь между ребрендингом розницы в Nordy и параллельным
переименованием юрлица «Рейма» в «Ласси» (по докладу саб-агента, ни
один источник не объясняет, как эти два трека соотносятся друг с
другом) — не вносится, чтобы не досочинить связь; финансовые убытки
«Ласси» за 2024-2025 годы — из агрегатора (star-pro.ru), не
перепроверены второй независимой регистровой ссылкой (rusprofile.ru
и b2b.house вернули 403); передавалась ли 75%-я доля «Валан
Менеджмент» перед ликвидацией — источник сам противоречит себе (в
одном месте пишет, что компания не значится учредителем ничьих
юрлиц), не разрешается здесь.

Запуск: python3 pipeline/fix_reima_valan_dm_details.py
        python3 pipeline/fix_reima_valan_dm_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g37066bfe'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Доли распределены 75% (АО «Валан Менеджмент») и 25% (структура'
    ' «Детского мира»). Соглашение о продаже предусматривало смену'
    ' названия торговой сети — магазины Reima переименованы в Nordy.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка ООО «Рейма» за 2021 год составила 5,7 млрд ₽, чистая'
    ' прибыль — 1,2 млрд ₽.'
)

OLD_ECO_CONTEXT = (
    'Компания создана ещё в 1944 году: сначала она перешивала военные'
    ' палатки в спецодежду, а затем стала выпускать детские'
    ' комбинезоны, куртки и пуховики.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По данным реестрового агрегатора audit-it.ru,'
    ' АО «Валан Менеджмент» (один из покупателей) ликвидировано: решение'
    ' о ликвидации принято 11 марта 2026 года, ликвидация завершена 3'
    ' июля 2026 года.'
)

NEW_SRC = [
    ['CRE.ru', 'https://cre.ru/news/90158'],
    ['Profashion', 'https://profashion.ru/business/finance/finskiy-brend-detskoy-odezhdy-reima-prodal-aktivy-v-rossii/'],
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1227700289002_ao-valan-menedzhment'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
