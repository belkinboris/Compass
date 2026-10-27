# -*- coding: utf-8 -*-
"""`asset` карточки g420352ff («Дом.РФ»/КРТ в Петра Дубраве) повторял почти
целиком то же, что уже несет `eco.share` (участок 52,31 га, поселок,
Самарская область) — пост печатал оба подряд через тире, и предмет
читался дважды. Короче, как у аналогичных лотов («промышленно-усадебный
комплекс» у g7c536b72, «особняк барона Александра Штиглица...» у
g49431b3c): имя предмета, подробности — в eco.share.

Запуск:
    python3 pipeline/fix_samara_krt_asset_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_samara_krt_asset_2026_10_14.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g420352ff'

OLD = 'право заключить договор о КРТ участка 52,31 га в поселке Петра Дубрава (Самарская область)'
NEW = 'право заключить договор о комплексном развитии территории (КРТ)'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['asset'] == OLD, card['asset']
    if card.get('party_evidence', {}).get('target'):
        for ev in card['party_evidence']['target']:
            if ev.get('value') == OLD:
                ev['value'] = NEW

    print('ПРАВКА %s: asset' % CARD_ID)
    print('  было:  %s' % OLD)
    print('  стало: %s' % NEW)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['asset'] = NEW
    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    assert fresh_card['asset'] == OLD, 'кто-то уже поправил — перечитайте'
    idx = fresh['cards'].index(fresh_card)
    fresh['cards'][idx] = card
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
