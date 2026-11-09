# -*- coding: utf-8 -*-
"""gaa5d4eb6 (ГК «ССК» / ГК «Носта»): второе чтение нашло, что 161.ru
подтверждает только половину сделки (актив на Гвардейской площади) — вторую
половину (ООО СЗ «Весенний бриз»/ЖК «Приморский») подтверждает только
телеграм-пост @dealsma, которого `source_names.settle_sources()` увел в
`discovery_src`, когда появился 161.ru. review.py не умеет вернуть источник
из discovery_src в src (`has_source()` считает его уже учтенным) — правка
одноразовым скриптом.

Запуск: python3 pipeline/archive/2026-11/restore_dealsma_src_gaa5d4eb6_2026_11_09.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'gaa5d4eb6'
TG = ['Телеграм-канал: Сделки M&A', 'https://t.me/dealsma/7554']


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CID)
    assert card.get('src') == [['161.RU', 'https://161.ru/text/business/2026/11/02/76740160/']], card.get('src')
    assert TG in (card.get('discovery_src') or []), card.get('discovery_src')
    card['src'].append(TG)
    card['discovery_src'] = [s for s in card['discovery_src'] if s != TG]


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    print('%s: src + %s (снят из discovery_src)' % (CID, TG[1]))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv))
