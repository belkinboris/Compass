# -*- coding: utf-8 -*-
"""Карточка gfbdc17f5 (очередь pending.json, приемка 26 ноября 2026): «Активы
экс-главы Ростова-на-Дону Алексея Логвиненко обращены в доход государства».

`no_parties` — служебная формулировка, а не перенос цитаты (тот же текст у
всех карточек изъятия по суду, g06adc4cc/gad9394d1/gd561d849/gb98fcce5/
g78cf801a и другие), поэтому пишется этим разовым скриптом, а не таблицей
`FIXES` в review.py (там для нее нет проверки по словарю — см.
`pipeline/archive/2026-11/reread_oneoff_m209.py`, константа `SEIZE`).

Покупателя и продавца в статьях нет: имущество изъято судом у Алексея
Логвиненко и семи связанных с ним лиц (Интерфакс, 25 ноября 2026 —
"об обращении в доход государства имущества бывшего главы администрации
города Алексея Логвиненко и иных связанных с ним лиц") и передано
государству, а не куплено кем-то поименно; профиль Росимущества как
покупателя не ставится — в отличие от g412a9a73/g67e276e2, здесь нет
юрлица, чья доля в ЕГРЮЛ перешла бы на Росимущество (предмет — паи ЗПИФ,
недвижимость, автомобили и деньги физлиц). Тот же случай, что
«Активы вице-губернатора Кубани Андрея Коробки» (g78cf801a): buyer/seller
пусты.

Запуск: python3 pipeline/archive/2026-11/fix_logvinenko_no_parties_2026_11_26.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gfbdc17f5'
NO_PARTIES = 'Изъятие по решению суда: покупателя и продавца нет, актив перешел государству.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card.get('no_parties') is None, card.get('no_parties')
    assert card.get('buyer') is None and card.get('seller') is None
    card['no_parties'] = NO_PARTIES
    if write:
        json.dump(data, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО: no_parties для %s' % CARD_ID)
    else:
        print('Сухой прогон. no_parties -> %r' % NO_PARTIES)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
