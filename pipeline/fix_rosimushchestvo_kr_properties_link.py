# -*- coding: utf-8 -*-
"""Один непривязанный случай «Росимущества» — сквозной паттерн аудита 13
сентября 2026 (пункт 9), измерено: из 11 карточек, называющих Росимущество
продавцом, 9 уже были верно привязаны к существующему профилю `g9fd82fee`,
и лишь эта одна (родительный падеж «Росимущества» в поле `seller`, из
оборота «выкупает активы... у Росимущества») осталась без `seller_id`.
Дописываю только ссылку, текст поля не трогаю — та же граница, что у
уже привязанных карточек (текст остаётся как есть, ссылка добавляется).
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf3c5069f'
PROFILE_ID = 'g9fd82fee'


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    assert PROFILE_ID in data['companies'], 'профиль Росимущества пропал из базы'
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card.get('seller') == 'Росимущества', 'seller уже другой: %r' % card.get('seller')
    assert not card.get('seller_id'), 'seller_id уже привязан'
    card['seller_id'] = PROFILE_ID
    print('%s: seller_id -> %s' % (CARD_ID, PROFILE_ID))
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
