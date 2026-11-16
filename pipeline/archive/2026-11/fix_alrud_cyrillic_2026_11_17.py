# -*- coding: utf-8 -*-
"""АЛРУД в базе пишется по-русски (владелец, 17 ноября 2026: «у нас в базе Алруд на русском»).
В двух карточках консультант и в четырех подписи источников стояли латиницей — «ALRUD».
Без ключа — сухой прогон, запись — с --write."""
import json
import sys

PATH = 'static/data/deals_promoted.json'
ADV = {'g0fadc207', 'g66cb145a'}
SRC = {'g0fadc207', 'gf2c13b88', 'g66cb145a', 'gfca749be'}


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    n_adv = n_src = 0
    for d in data['deals']:
        if d['id'] in ADV:
            for row in (d.get('law') or {}).get('adv') or []:
                if len(row) > 1 and row[1] == 'ALRUD':
                    row[1] = 'АЛРУД'
                    n_adv += 1
        if d['id'] in SRC:
            for row in d.get('src') or []:
                if row and isinstance(row[0], str) and row[0].startswith('ALRUD'):
                    row[0] = 'АЛРУД' + row[0][len('ALRUD'):]
                    n_src += 1
    assert (n_adv, n_src) == (2, 4), (n_adv, n_src)
    print('консультантов: %d, подписей источников: %d' % (n_adv, n_src))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    json.dump(data, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
