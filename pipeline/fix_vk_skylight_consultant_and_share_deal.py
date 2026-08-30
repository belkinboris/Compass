# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
ga1152200 (VK выкупила офисную башню в бизнес-центре Skylight) —
юридический консультант покупателя не был известен, а сумма покупки
самого пакета акций «Линдера» (отдельная от рыночной оценки актива
величина) не была отражена. Проверено лично прямым WebFetch двух
источников.

`law.adv` (заполнено, было «не раскрывались»). Дословно (Право.ру):
«Команда ALUMNI Partners выступила юридическим консультантом группы
VK в сделке по приобретению 27-этажной башни бизнес-центра Skylight».
Про консультанта продавца источник не сообщает.

`eco.context` (дополнено). Найдена ДРУГАЯ, но не противоречащая
величина: цена самого пакета акций АО «Линдер» (юрлица-собственника
башни) с учётом его долга — не то же самое, что рыночная оценка
здания (12–13 млрд ₽, уже в `sum`/`eco.sum`). Дословно (CNews):
«Сумма сделки составила 3,4 млрд руб. Эта сумма включает в себя
задолженность "Линдера" перед VK и третьими лицами.» — то есть VK
уже была кредитором «Линдера» до покупки долей, и цена акций оказалась
кратно ниже рыночной стоимости актива именно из-за зачёта долга.

НЕ ВКЛЮЧЕНО: более сильное подтверждение O1 Properties как продавца —
CNews повторяет ту же осторожную формулировку, что уже в карточке
(«структуры, связанные с» O1 Properties, а не прямой продавец);
текущее использование башни и связанные более поздние сделки VK с
недвижимостью — ничего нового не нашлось.

Запуск: python3 pipeline/fix_vk_skylight_consultant_and_share_deal.py
        python3 pipeline/fix_vk_skylight_consultant_and_share_deal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga1152200'

OLD_ADV = [
    ['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались'],
]
NEW_ADV = [
    ['Юридический консультант VK (покупателя)', 'ALUMNI Partners', 'Приобретение башни «А» бизнес-центра Skylight. Источник: 300.pravo.ru'],
]

OLD_CONTEXT = 'предыдущим владельцем «Ахилла» мог быть девелопер O1 Properties'
NEW_CONTEXT = OLD_CONTEXT + (
    '. Отдельная величина — цена самого пакета акций АО «Линдер» с '
    'учётом его задолженности перед VK и третьими лицами: «Сумма '
    'сделки составила 3,4 млрд руб.» (CNews) — это не рыночная оценка '
    'здания (12–13 млрд ₽), а цена долей юрлица-собственника с зачётом '
    'долга.'
)

NEW_SRC = [
    ['Право.ру', 'https://300.pravo.ru/news/246162/'],
    ['CNews', 'https://www.cnews.ru/news/top/2024-05-31_vk_potratil_34_milliarda_na'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV, deal['law']['adv']
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.adv: станет ===')
    print(NEW_ADV)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['adv'] = NEW_ADV
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
