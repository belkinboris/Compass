# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g09242ae2 (Концерн «Детскосельский»/ООО
«Плодородие»): дельта-поиск нашёл, что часть изданий называла
вероятным конечным бенефициаром покупателя группу «Агроэко»
Владимира Маслова — а сама «Агроэко» это прямо опровергла. Тот же
класс, что уже записан в «Известных проблемах» CLAUDE.md (S8 Capital/
«МТ-Интеграция», БКС/«Форштадт»): версия названа в прессе и прямо
опровергнута названной стороной. Не меняем `buyer`/`law.struct` —
формальный покупатель (ООО «Плодородие», Чистяков/Шишлянникова) уже
верно записан в карточке независимо от этого спора; добавляем обе
стороны истории в `eco.context`, решение оставляем читателю. Не через
`review.py`: два источника (retailer.ru — версия, Коммерсантъ —
опровержение) не образуют с уже записанным текстом `eco.context`
(agrovesti.net/ЕГРЮЛ) непрерывный кусок.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://retailer.ru/aktivy-voronezhskogo-koncerna-detskoselskij-pereshli-k-novomu-vladelcu/
https://www.kommersant.ru/doc/8038618

Запуск: python3 pipeline/fix_detskoselsky_agroeko_denial_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g09242ae2'

OLD_CONTEXT = (
    'Сам концерн, созданный в 2007 г. его президентом Юрием Брагинцем, '
    'управляет воронежским заводом растительных масел «Бутурлиновский». '
    'Он также владеет агропредприятиями в Ленинградской области и '
    'Белоруссии. По данным ЕГРЮЛ, в начале сентября 2025 года новым '
    'владельцем обеих компаний стало ООО «Плодородие», которое в '
    'равных долях принадлежит Максиму Чистякову и Людмиле '
    'Шишлянниковой.'
)
CONTEXT_ADDITION = (
    ' По информации источника, знакомого с руководством '
    '«Детскосельского», в качестве покупателя могла выступить группа '
    '«Агроэко» бизнесмена Владимира Маслова (retailer.ru) — но в самой '
    '«Агроэко» это опровергли: «в компании сообщили, что ООО '
    '«Плодородие» не входит в их структуру» (Коммерсантъ), хотя тот же '
    'Максим Чистяков в 2018–2021 годах возглавлял ООО «Экополе», '
    'позже перешедшее под управление ООО «Агроэко-менеджмент».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += версия про «Агроэко» и её '
          f'опровержение')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
