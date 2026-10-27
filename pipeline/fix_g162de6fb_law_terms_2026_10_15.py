# -*- coding: utf-8 -*-
"""Второе чтение карточки g162de6fb (Nomi/«Гельтек») нашло: `law.terms`
несет план по бренду (сохранение имени, возможный редизайн), а не
условия сделки (заверения/опционы/обязательства) — ни один источник их
не называет. Факт перенесен в `extra` (отдельная FIXES-запись), здесь —
честная пустота.

Запуск:
    python3 pipeline/fix_g162de6fb_law_terms_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_g162de6fb_law_terms_2026_10_15.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g162de6fb'

OLD = 'Бренд Nomi сохранится под своим именем. В перспективе возможен его редизайн.'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['law']['terms'] == OLD, card['law']['terms']

    print('СНИМАЕМ %s: law.terms (перенесено в extra)' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    assert fresh_card['law']['terms'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh_card['law']['terms'] = '—'
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
