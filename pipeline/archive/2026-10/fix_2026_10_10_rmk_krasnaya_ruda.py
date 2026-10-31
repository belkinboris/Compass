# -*- coding: utf-8 -*-
"""Качество, 10 октября 2026 — недельная очередь: `gee625a0f` (РМК /
«Красная руда»). Два факта сверх уже известного, оба из НОВЫХ источников
(не было в `src`):

1. `seller` — у АО «Дарбшир» назван руководитель: Никита Кучин, гендиректор
   инвестиционной компании Altus Capital (Коммерсантъ, отдельная статья
   30.09.2026, другой адрес, чем уже привязанный).
2. `eco.rationale` — конкретные цифры по рынку меди вместо общей фразы
   («обновили максимум») — MarketPower (перепечатка со ссылкой на
   Коммерсантъ, те же цифры нигде не звучали раньше в карточке).

Запуск:
    python3 pipeline/fix_2026_10_10_rmk_krasnaya_ruda.py            # сухой прогон
    python3 pipeline/fix_2026_10_10_rmk_krasnaya_ruda.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_SELLER = 'АО «Дарбшир»'
NEW_SELLER = 'АО «Дарбшир» (гендиректор — Никита Кучин, также руководит инвестиционной компанией Altus Capital)'
SRC_KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8989985']

OLD_RATIONALE = (
    'РМК пополняет портфель поисковых лицензий на фоне благоприятной '
    'конъюнктуры рынка меди — цены на металл в сентябре обновили максимум '
    'на Лондонской бирже металлов. Интерес к лицензиям без завершенных '
    'поисково-оценочных работ может объясняться близостью участков к ранее '
    'отработанным залежам, включая советские месторождения.'
)
ADD_RATIONALE = (
    ' В сентябре цена меди на Лондонской бирже металлов достигала $14,7 '
    'тыс. за тонну, а Fitch Ratings повысило прогноз средней цены на 2026 '
    'год до $13,5 тыс. за тонну.'
)
SRC_MARKETPOWER = ['Market Power', 'https://marketpower.pro/publications/rmk-priobrela-kompaniiu-s-litsenziiami-na-poisk-zolota-i-medi-na-altae']


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    by_id = {d['id']: d for d in deals}
    card = by_id['gee625a0f']

    assert card['seller'] == OLD_SELLER, card['seller']
    assert card['eco']['rationale'] == OLD_RATIONALE, card['eco']['rationale']

    card['seller'] = NEW_SELLER
    card['eco']['rationale'] = OLD_RATIONALE + ADD_RATIONALE
    src = card.setdefault('src', [])
    for pair in (SRC_KOMMERSANT, SRC_MARKETPOWER):
        if pair not in src:
            src.append(pair)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gee625a0f: seller дополнен именем руководителя продавца; eco.rationale дополнен ценами на медь. ЗАПИСАНО.')
    else:
        print('Сухой прогон: применил бы две правки выше. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
