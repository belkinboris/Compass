# -*- coding: utf-8 -*-
"""Карточка `gcf05509a` — Телеграм-канал @LawFirms называет юридического
консультанта АФК «Система» в сделке по продаже 4,85% «Медси»
Альфа-банку: White Square. `law.adv` до этого момента был placeholder
«консультанты не раскрывались» — убран, вместо него запись в формате,
которым уже отмечены другие сделки White Square в этой базе (роль,
фирма, примечание с источником). Консультант покупателя (Альфа-банка)
публично не назван — отдельной строки для него не ставим, как и на
других карточках, где известна только одна сторона.

Источник: Телеграм-канал @LawFirms https://t.me/LawFirms/11525

Запуск:
    python3 enrich_medsi_lawadv_2026_10_13.py            # сухой прогон
    python3 enrich_medsi_lawadv_2026_10_13.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'gcf05509a'
LAWFIRMS = ['Телеграм-канал @LawFirms', 'https://t.me/LawFirms/11525']

OLD_ADV = [['Стороны сделки', 'Не раскрывались',
            'Юридические консультанты в публичных источниках не раскрывались']]
NEW_ADV = [['Юридический консультант АФК «Система» (продавца)', 'White Square',
            'Сопровождение АФК «Система» в продаже 4,85% акций группы «Медси» Альфа-Банку. '
            'Источник: https://t.me/LawFirms/11525']]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['law']['adv'] == OLD_ADV

    print('ПРАВКА %s: law.adv (White Square — консультант продавца), +src' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['law']['adv'] = NEW_ADV
    existing = {s[1] for s in card.get('src', []) if len(s) > 1}
    if LAWFIRMS[1] not in existing:
        card.setdefault('src', []).append(list(LAWFIRMS))

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card['law']['adv'] == OLD_ADV, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
