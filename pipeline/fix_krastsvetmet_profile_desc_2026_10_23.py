# -*- coding: utf-8 -*-
"""Описание профиля «Красцветмет» (g680e39d6): первое предложение — коротко
и о главном (его берёт строка «Покупатель» в посте карточки gf31c1d53).

Профиль заведён приёмкой той же карточки 23 октября 2026; в первом варианте
описания первое предложение было длинным перечнем, и формат поста взял
второе — «Целиком принадлежит Красноярскому краю…» — без подлежащего.

    python3 pipeline/fix_krastsvetmet_profile_desc_2026_10_23.py            # сухой прогон
    python3 pipeline/fix_krastsvetmet_profile_desc_2026_10_23.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'g680e39d6'
OLD = ('Красноярский производитель драгоценных металлов: перерабатывает минеральное и вторичное '
       'сырьё, выпускает все восемь драгметаллов, а также ювелирные (бренд Krastsvetmet) и '
       'технические изделия. Целиком принадлежит Красноярскому краю; юрлицо — ОАО «Красцветмет».')
# Юрлицо — в первом предложении: формат поста берёт первым предложение с
# именем в «ёлочках» (format_post._pick_novel_sentences), и если «ёлочки»
# стоят только в последнем, строка «Покупатель» начинается с него.
NEW = ('ОАО «Красцветмет» — красноярский завод драгоценных металлов, ювелирных и технических '
       'изделий. Перерабатывает минеральное и вторичное сырьё и выпускает все восемь драгметаллов; '
       'украшения — под брендом Krastsvetmet. Целиком принадлежит Красноярскому краю.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cur = data['companies'][CID]['desc']
    if cur == NEW:
        print('Уже применено.')
        return 0
    assert cur == OLD, cur
    print('%s: %s\n  -> %s' % (CID, OLD, NEW))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
    assert fresh['companies'][CID]['desc'] == OLD
    fresh['companies'][CID]['desc'] = NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Применено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
