# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `gfe16916c`
(«Lanxess продал завод в Липецке Владимиру Якушину», закрыта 30.05.2023) —
дальнейшая судьба завода после сделки не была отражена.

Проверено лично прямым WebFetch, сайт покупателя,
https://nortex-chem.ru/news/Kompaniya-Nortex-priobrela-zavod-Lanxess/,
дата публикации 02.06.2023: «Химический завод «Ланксесс Липецк» немецкой
компании Lanxess перешел под контроль ООО «Нортекс». Теперь компания
переименована в ООО «Нортекс-Липецк»» (управляющая компания переименована
в ООО «НЛ-Интернейшнл»); «На производственных мощностях завода Nortex
продолжит выпускать высокотехнологичные полимеросвязанные добавки для
шин и резинотехнических изделий под торговой маркой «Нортгран»» (прежний
бренд Rhenogran уже назван в `eco.rationale` карточки).

НЕ ВНЕСЕНО: цифры о числе сотрудников и регионах сбыта с
rubber-expo.ru/ru/media/news/index.php?id4=20742 — страница технически
открылась, но текст испорчен кодировкой; повторное дословное
цитирование дало разные, противоречащие друг другу числа при двух
запросах — источник фактически нечитаем, вносить нельзя. `law.terms`/
`law.appr` — ни один источник не называет условий сделки или органа
согласования; оставлены как честная пустота (сумма сделки — 216,6 млн
₽ выручки цели, вероятно, ниже порога обязательного согласования ФАС).

Запуск: python3 pipeline/fix_lanxess_lipetsk_rebrand_aftermath.py
        python3 pipeline/fix_lanxess_lipetsk_rebrand_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfe16916c'

OLD_ECO_CONTEXT = (
    'ООО «Нортекс» зарегистрировано в 2005 году. Уставный капитал – 1 млн '
    'рублей. Выручка в 2022 году составила 21,3 млрд, чистая прибыль – 1,9 '
    'млрд рублей'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + '. После сделки завод и управляющая компания '
    'переименованы в ООО «Нортекс-Липецк» и ООО «НЛ-Интернейшнл» '
    'соответственно, продукция выпускается под новой торговой маркой '
    '«Нортгран».'
)

NEW_SRC = [
    ['Nortex', 'https://nortex-chem.ru/news/Kompaniya-Nortex-priobrela-zavod-Lanxess/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
