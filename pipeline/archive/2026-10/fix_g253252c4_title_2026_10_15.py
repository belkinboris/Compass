# -*- coding: utf-8 -*-
"""Второе чтение (15 октября 2026, карточка g253252c4): заголовок был
дословной копией заголовка РИА Недвижимость целиком, без переформулировки
— тот же класс, что уже решался 12 октября для precedента g22d3599c
(«Власти Москвы выставили на торги проект КРТ на месте Рижского рынка» →
«Москва выставила на продажу право на застройку на месте Рижского
рынка»). Заголовок — не прозовое поле `review.py` (там обязана быть
дословная цитата), поэтому правится прямым скриптом, как и прецедент.

Запуск:
    python3 pipeline/fix_g253252c4_title_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_g253252c4_title_2026_10_15.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g253252c4'
OLD = 'Власти Москвы выставили на торги проект КРТ в Южном Тушине'
NEW = 'Москва выставила на торги право на КРТ в Южном Тушине'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['title'] == OLD, 'заголовок уже не тот, что ожидался: %r' % card['title']
    print('%s\n-> %s' % (OLD, NEW))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    assert fresh_card['title'] == OLD, 'заголовок поменяли параллельно — перечитайте'
    fresh_card['title'] = NEW
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
