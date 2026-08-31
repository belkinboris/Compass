# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gc681c2b6
(ГК «Альянс» приобретает 100% акций ПАО «АГ Майнинг» у Kopy Goldfields)
— искали, закрылась ли сделка фактически после президентского
разрешения (март 2025) и почему шведская Kopy Goldfields выходила из
актива.

Фактического закрытия НЕ найдено ни в одном источнике — все найденные
материалы останавливаются на этапе разрешения. Статус «Обсуждается» НЕ
менялся: честная пустота сохранена, а не заменена предположением.

Проверено лично прямым WebFetch причины выхода. Интерфакс (26.03.2025,
interfax.ru/business/1016640): «В октябре Kopy Goldfields провела
делистинг с площадки Nasdaq First North Growth Market в Стокгольме».
Interfax (англ., 24.05.2024, interfax.com/newsroom/top-stories/102605/):
«The company is increasingly coming under pressure from sanctions and
other legislative initiatives in both Russia and the European Union»,
«Kopy Goldfields intends to delist if the main shareholders' stake
exceeds 90% upon the results of the transaction» — то есть делистинг был
заранее объявленным условием именно ЭТОЙ сделки, а не совпадением по
времени.

`eco.context` дополнен фактом о делистинге и его причине.

НЕ ВКЛЮЧЕНО: точная сумма сделки — единственная встретившаяся цифра
($119,6 млн) относится к ДРУГОЙ, более ранней сделке 2020 года
(обратное поглощение «Амур Золота»), а не к цене выкупа доли Kopy
Goldfields в 2025 году — тот же класс осторожности, что уже применён к
другим карточкам («Число может быть верным фактом и относиться не к той
сделке»). Возможное переименование Kopy Goldfields в шведском реестре
(редирект сайта на dumala.se/«Duvemala Förvaltning AB») — не проверено
прямым чтением реестра (Bolagsverket) или шведской прессы, осталось
непроверенной зацепкой. Кадровая динамика «АГ Майнинг»/«Амур Золото»
(рост штата 537 → 1099 человек, 2018-2025) — источник (Циклопедия)
недостаточно авторитетен для карточки и не привязан к самой сделке.

Запуск: python3 pipeline/fix_alliance_ag_mining_kopy_delisting_context.py
        python3 pipeline/fix_alliance_ag_mining_kopy_delisting_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc681c2b6'

OLD_CONTEXT = (
    'Kopy Goldfields в 2020 году провела сделку по обратному поглощению '
    '«Амур Золота», контроль в объединенной компании получили акционеры '
    '«Группы Альянс» (Идрисов, Муса, Дени и Магомед Бажаевы).'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Продавец заранее готовился уйти с российского рынка: «Kopy '
    'Goldfields intends to delist if the main shareholders\' stake '
    'exceeds 90% upon the results of the transaction» на фоне '
    'санкционного давления (Интерфакс, 24 мая 2024 года). «В октябре '
    'Kopy Goldfields провела делистинг с площадки Nasdaq First North '
    'Growth Market в Стокгольме» (Интерфакс, 26 марта 2025 года).'
)

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1016640'],
    ['Interfax', 'https://www.interfax.com/newsroom/top-stories/102605/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
