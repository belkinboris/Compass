# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g221e4969 («Bonum Capital вышла из капитала ООО «Паскаль медикал»,
продав 49% долей», закрыта 19 мая 2023) — финансы предмета и масштаб
производства не были заполнены, а структура владения после сделки
известна только на момент закрытия (Сарманов/Конозаков).

Проверено лично прямым WebFetch (Фармвестник,
https://pharmvestnik.ru/content/news/Bonum-Capital-vyshla-iz-kapitala-zavoda-po-proizvodstvu-igl-Paskal-medikal.html):
«выручка предприятия в 2022 году составила 992 млн руб., прибыль —
102 млн руб.»

Проверено лично прямым WebFetch (Vademecum,
https://vademec.ru/news/2024/10/03/paskal-medikal-investiroval-1-mlrd-rubley-v-rasshirenie-proizvodstva-shpritsev-i-igl/,
октябрь 2024): «ООО «Паскаль Медикал» на 50% принадлежит... Владимиру
Конозакову, еще 49% владеет гендиректор Максим Сарманов, 1% –
Евгения Нистратова» (тот же расклад, третий совладелец с 1%
появился позже мая 2023, но не меняет ролей сторон сделки); «Суммарный
объем инвестиций в предприятие оценивается в 3 млрд рублей»;
производственные мощности — «более 1,2 млн шприцев в сутки», до 450
млн шприцев и 500 млн игл в год; проект второй очереди (инфузионные
системы, катетеры, 1,5 млрд ₽) «заморожен».

НЕ ВКЛЮЧЕНО: сумма самой сделки 2023 года — ни один из проверенных
источников её не раскрывает; признаков сохранения фактического
контроля Bonum Capital/Мурата Алиева после номинальной передачи не
нашлось ни в одном источнике (только экспертная оценка о номинальности
самой передачи, уже отражённая в карточке) — не додумывается; отдельный
профиль компании для Bonum Capital/Мурата Алиева — по объёму материала
заслуживает внимания, но не факт для ЭТОЙ карточки.

Запуск: python3 pipeline/fix_paskal_medikal_finances_and_scale.py
        python3 pipeline/fix_paskal_medikal_finances_and_scale.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g221e4969'

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = 'Выручка предприятия за 2022 год — 992 млн ₽, прибыль — 102 млн ₽.'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'К октябрю 2024 года доли распределены так: 50% — Владимир Конозаков, '
    '49% — Максим Сарманов, 1% — Евгения Нистратова. Суммарные инвестиции '
    'в предприятие оцениваются в 3 млрд ₽; мощности позволяют выпускать '
    'более 1,2 млн шприцев в сутки (до 450 млн шприцев и 500 млн игл в '
    'год после модернизации). Проект второй очереди (инфузионные системы, '
    'катетеры, 1,5 млрд ₽) заморожен.'
)

NEW_SRC = [
    ['Фармвестник', 'https://pharmvestnik.ru/content/news/Bonum-Capital-vyshla-iz-kapitala-zavoda-po-proizvodstvu-igl-Paskal-medikal.html'],
    ['Vademecum', 'https://vademec.ru/news/2024/10/03/paskal-medikal-investiroval-1-mlrd-rubley-v-rasshirenie-proizvodstva-shpritsev-i-igl/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
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
