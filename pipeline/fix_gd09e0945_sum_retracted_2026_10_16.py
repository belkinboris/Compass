# -*- coding: utf-8 -*-
"""Приток 19:20 МСК — `enrich.py` (сухой прогон) предложил карточке
gd09e0945 (Леста Игры) сумму «10 млрд ₽» из статьи CNews: «Компания
намерена создать венчурный фонд и вложить в российскую игровую
индустрию 10 млрд руб.» Это НЕ цена сделки — это трёхлетний
инвестиционный план покупателя в отрасль (тот же факт уже верно записан
в `law.struct`), а сама цена сделки официально не раскрыта («Сумму сделки
стороны не раскрыли», mergers.ru и др.). Поле `sum` остаётся «—», но без
записи в `retracted` то же число из той же статьи, вернувшейся в ленте
завтра, снова предложило бы себя как «поле пусто» (см. урок про
Новомясово, enrich.py.is_retracted()).

Запуск: python3 pipeline/fix_gd09e0945_sum_retracted_2026_10_16.py --write
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'
WRONG_SUM = '10 млрд ₽'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    target = [d for d in data['deals'] if d.get('id') == 'gd09e0945']
    assert len(target) == 1, target
    card = target[0]
    assert card.get('sum') is None, repr(card['sum'])
    card.setdefault('retracted', {}).setdefault('sum', [])
    if WRONG_SUM not in card['retracted']['sum']:
        card['retracted']['sum'].append(WRONG_SUM)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gd09e0945: «%s» записано в retracted.sum. ЗАПИСАНО.' % WRONG_SUM)
    else:
        print('Сухой прогон: записал бы «%s» в retracted.sum. Повторите с --write.' % WRONG_SUM)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
