# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c: третий круг второго чтения нашел, что `title` все
еще подает платформу «Поток» как факт ЗАКРЫТОГО раунда без оговорки —
ту же проблему, что во втором круге сняли с buyer_name/law.struct/
eco.share/eco.val, но не пересмотрели в заголовке. Заголовок переписан
без привязки к платформе (сумма и статус подтверждены источником о
закрытии, платформа — нет).

Запуск:
    python3 pipeline/fix_visiology_title_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_title_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'
OLD_TITLE = 'Visiology привлекла 200 млн рублей через краудинвестинговую платформу «Поток»'
NEW_TITLE = 'Visiology привлекла 200 млн рублей в инвестиционном раунде'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in data['cards']}[CARD_ID]
    assert card['title'] == OLD_TITLE, 'title уже не тот: %r' % card['title']
    print('%s: title %r -> %r' % (CARD_ID, OLD_TITLE, NEW_TITLE))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc['title'] == OLD_TITLE, 'title поменяли параллельно — перечитайте'
    fc['title'] = NEW_TITLE
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
