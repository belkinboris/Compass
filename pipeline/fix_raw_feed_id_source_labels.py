# -*- coding: utf-8 -*-
"""Служебный id ленты («tg:rusven», «web:mergers.ru») протёк на экран пятью
записями в трёх карточках — тот же дефект, что уже чинили 6 августа для
«web:kommersant.ru» (см. докстрока pipeline/source_names.py), только в
`events[].source`, а не в верхнеуровневом `src`: конструктор карточки
(`promote.to_card()`) резолвит имя издания через `source_names.edition_label()`
для `src`, а код, добавляющий ЭТАПЫ (`events`), в найденных случаях копировал
внутренний id ленты напрямую, минуя резолвер.

Найдено замером по всей базе (регэксп `^(tg|web):` по первому элементу пары
[имя, url] в `src` и в `events[].source`): 5 записей, 4 карточки. Владелец
нашёл первую (`gcaa03820`, «tg:rusven») глазами 18 августа; чинится не одна
она, а весь класс — заодно поймано ещё 4.

`source_names.py` в этом же прогоне научился резолвить домен t.me по
username канала из пути ссылки (раньше не резолвил вовсе, отдавал голый
домен «T.me») — используем его здесь же, а не пишем вторую копию логики.

Запуск: python3 pipeline/fix_raw_feed_id_source_labels.py           # проверка
        python3 pipeline/fix_raw_feed_id_source_labels.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
import source_names  # noqa: E402

DATA = os.path.join(REPO_ROOT, 'static', 'data', 'deals_promoted.json')
RAW_ID = re.compile(r'^(tg|web):', re.I)

# (id карточки, старая метка) — проверка исходного состояния перед записью.
EXPECTED = {
    'gmru-vtb-otkrytie-office-rwb': ['tg:dealsma'],
    'g5647e100': ['tg:dealsma'],
    'gcaa03820': ['tg:rusven', 'tg:rusven'],
    'ga525c46b': ['web:mergers.ru'],
}


def fix_pair(pair):
    """[метка, url] -> новая пара, если метка похожа на служебный id ленты."""
    if not (isinstance(pair, list) and len(pair) > 1 and RAW_ID.match(str(pair[0] or ''))):
        return pair, None
    old = pair[0]
    new = source_names.edition_label(pair[1])
    return [new, pair[1]], (old, new)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}

    changes = []
    for cid, expected_labels in EXPECTED.items():
        card = cards[cid]
        found = []
        new_src = []
        for pair in card.get('src') or []:
            fixed, change = fix_pair(pair)
            new_src.append(fixed)
            if change:
                found.append(change)
        for ev in card.get('events') or []:
            src = ev.get('source')
            if not src:
                continue
            fixed, change = fix_pair(src)
            ev['source'] = fixed
            if change:
                found.append(change)
        assert [old for old, _new in found] == expected_labels, (
            '%s: ожидались метки %r, нашлись %r — состояние изменилось'
            % (cid, expected_labels, [old for old, _new in found]))
        card['src'] = new_src
        changes.append((cid, found))

    for cid, found in changes:
        for old, new in found:
            print('%s: %r -> %r' % (cid, old, new))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
