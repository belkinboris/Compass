# -*- coding: utf-8 -*-
"""Пять привязок, которые `link_parties.py` пропускал, потому что текст
стороны был не голым именем, а именем В ОБЁРТКЕ («Акции Selectel»,
«Группа Циан», «Sucden (через ООО «СДС»)», «14% в группе
«Полипластик»», «100% долей в ООО «Кэн-пак завод упаковки» и ООО
«Кэн-пак»») — ключ близнецов сравнивает строки целиком и не видит
совпадения, когда вокруг имени стоят лишние слова (доля, падеж,
пояснение в скобках). Профиль в каждом случае уже существует в базе
(задача #122, 13 сентября 2026, первый шаг перед кампанией чтения
новых профилей): все пять совпадений проверены глазами, ни одного
омонима.

`ООО «ТД Эдельвейс»`/`АО «Эдельвейс»` из того же прохода НЕ включён —
это уже прочитанная и отвергнутая пара в `link_parties.NOT_THE_SAME`
(торговый дом и акционерное общество — разные юрлица одной группы).

Assert на исходном состоянии — как везде.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, поле-ссылка, текстовое поле, ожидаемый текст, id профиля)
LINKS = [
    ('gmru-sucden-poetti', 'buyer', 'buyer_name', 'Sucden (через ООО «СДС»)', 'gb933c2b2'),
    ('gacc757b6', 'target', 'asset', 'Акции Selectel', 'gd4a7c612'),
    ('g925a9d17', 'target', 'asset', 'Группа Циан', 'g163cfc8b'),
    ('gmru-prime-pervy-poliplastik', 'target', 'asset', '14% в группе «Полипластик»', 'g5dd3e034'),
    ('g2349d667', 'target', 'asset',
     '100% долей в ООО «Кэн-пак завод упаковки» и ООО «Кэн-пак»', 'g6c930a0d'),
]


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    by_id = {d['id']: d for d in data['deals']}

    for cid, id_field, text_field, expected_text, pid in LINKS:
        card = by_id[cid]
        assert card.get(text_field) == expected_text, (cid, text_field, card.get(text_field))
        assert not card.get(id_field), (cid, id_field, 'уже привязано')
        assert pid in comps, (cid, 'профиль не существует:', pid)

    for cid, id_field, text_field, expected_text, pid in LINKS:
        card = by_id[cid]
        card[id_field] = pid
        if id_field == 'buyer':
            card.pop('buyer_name', None)
        print('%s: %s -> %s (%s)' % (cid, id_field, pid, comps[pid]['name']))

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
