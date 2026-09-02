# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g78e14953
(«S8 Capital претендует на покупку шинного завода Bridgestone в
Ульяновске», статус уже «Закрыта») — заголовок и `extra` остались от
стадии «претендует», хотя карточка уже верно помечена закрытой (дата
20.12.2023 совпадает с датой публикации Коммерсанта о ЗАКРЫТИИ, а не с
более ранними переговорами) — структурные детали закрытия (юрлицо
цели, доли, судьба бренда) не были внесены.

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/6412480): «Торговые марки и бренд
Bridgestone новому собственнику не передаются»; «Стоимость российского
бизнеса японской компании может быть оценена в 3,25x–3,75x EV/EBITDA
2021» — по расчётам Павла Терентьева (Advance Capital) это «7,5–9,8
млрд руб.»; «Покупка активов Bridgestone в РФ — уже третье приобретение
шинного дивизиона S8 Capital. В мае компания закрыла сделку по
приобретению российского бизнеса Continental... В том же месяце
компания объявила о приобретении российского производителя «Кордиант»».

Проверено лично прямым WebFetch (Интерфакс,
https://www.interfax.ru/business/938388): «26 декабря получило контроль
над 99,9% уставного капитала ульяновского предприятия по производству
шин - ООО "Бриджстоун тайер мануфэкчуринг СНГ"» (АО «Кордиант»); «Ещё
0,1% теперь распоряжается АО "С8 промышленные активы"».

НЕ ВКЛЮЧЕНО в структурные поля этой карточки: у актива есть значимое
продолжение — 1 октября 2024 года весь холдинг «Кордиант» (включая этот
завод) перепродан структуре Алексея Мордашова «Севергрупп» (оценка
20–25 млрд ₽ с учётом долга, Ведомости), завод переименован в Gislaved.
Это ОТДЕЛЬНАЯ, более поздняя сделка со своими сторонами — записана в
CLAUDE.md как «Известная проблема» для решения человеком, не вписана
сюда механически. Заголовок карточки НЕ переименован («претендует» →
«закрыла сделку») — старые карточки по стилю не переименовываются
(правило CLAUDE.md), а факт закрытия и так верно отражён в `status`.

Запуск: python3 pipeline/fix_s8capital_bridgestone_ulyanovsk_details.py
        python3 pipeline/fix_s8capital_bridgestone_ulyanovsk_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g78e14953'

OLD_ECO_VAL = 'Сумма сделки, по оценкам аналитиков, могла быть сопоставима с Continental — 7–10 млрд руб.'
NEW_ECO_VAL = (
    'Сумма не раскрыта. Аналитик Advance Capital Павел Терентьев оценивал '
    'сделку в 7,5–9,8 млрд ₽ (3,25–3,75x EV/EBITDA 2021) — это уже третье '
    'приобретение S8 Capital в шинном сегменте после Continental и '
    '«Кордианта».'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    '26 декабря 2023 года 99,9% уставного капитала ООО «Бриджстоун тайер '
    'мануфэкчуринг СНГ» получило АО «Кордиант» (структура S8 Capital), '
    'ещё 0,1% — АО «С8 промышленные активы».'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = 'Торговые марки и бренд Bridgestone новому собственнику не передаются.'

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/938388'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['law']['terms'] == OLD_LAW_TERMS

    new_src = deal['src'] + NEW_SRC

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
