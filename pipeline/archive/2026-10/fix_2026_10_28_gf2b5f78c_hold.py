# -*- coding: utf-8 -*-
"""gf2b5f78c (Муслюмовский участок недр): карточка придержана до появления
продавца. Партнер одобрил ее 28 октября 2026, но у продажи с торгов продавец
(организатор аукциона) обязан быть назван (test_auction_deal_names_its_seller),
а источник (Ufa1.ru) его не называет; извещение на torgi.gov.ru (лот
№ 22000039810000000164) и площадка ЭТП ГПБ из контейнера не открылись.
Придерживаем, а не выдумываем: пустое поле честнее. Снимается кнопкой
«Опубликовать» после того, как продавец записан по источнику.

Запуск: python3 pipeline/fix_2026_10_28_gf2b5f78c_hold.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
WHY = ('придержана: у продажи с торгов не назван продавец (организатор аукциона) — '
       'источник Ufa1.ru его не называет; нужно извещение torgi.gov.ru, лот 22000039810000000164')


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in pending['cards'] if c['id'] == 'gf2b5f78c')
    assert not card.get('held'), 'уже придержана'
    assert not card.get('seller'), 'продавец уже назван: %r' % card.get('seller')
    print('  gf2b5f78c -> held, причина: %s' % WHY)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))      # перечитать перед записью
    card = next(c for c in pending['cards'] if c['id'] == 'gf2b5f78c')
    card['held'] = True
    card['held_why'] = WHY
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
