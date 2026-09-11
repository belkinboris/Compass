#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки — имя компании, а не пересказ её занятий.

Две карточки, найденные новым правилом `ASSET_IS_A_DESCRIPTION` в
`review.py` (11 сентября 2026, после жалобы владельца на карточку
Positive Technologies/CyberOK). Тот же дефект, только меньшего размера:
в поле `asset`, которое схема сделки печатает как «Предмет сделки»,
стоит родовое описание компании, а её имя — в самом конце фразы.

Правка механическая: описание вырезается, имя остаётся дословной
подстрокой прежнего значения — ничего не сочиняется. Ровно та граница,
что уже применялась в «Имя компании — не место для доли».

Запуск:
    python3 pipeline/fix_asset_is_a_name_not_a_description.py
    python3 pipeline/fix_asset_is_a_name_not_a_description.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

FIXES = [
    dict(id='gc5951fac',
         old='разработчик системы для управления автомобильными грузоперевозками CARGO.RUN',
         new='CARGO.RUN',
         why='заголовок карточки называет предмет прямо: «купили 25% '
             'разработчика сервиса CARGO.RUN»'),
    dict(id='g3f0400db',
         old='российский производитель решений в области кибербезопасности «Кодмастер»',
         new='«Кодмастер»',
         why='имя стоит в конце описания, в кавычках'),
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    for fix in FIXES:
        card = by_id.get(fix['id'])
        assert card is not None, 'нет карточки %s' % fix['id']
        assert card.get('asset') == fix['old'], \
            '%s: предмет уже другой — %r' % (fix['id'], card.get('asset'))
        # Имя обязано быть дословным куском прежнего значения: так правка
        # остаётся вырезанием, а не переписыванием.
        assert fix['new'] in fix['old'], \
            '%s: новое имя не является частью старого значения' % fix['id']
        print('%s | %s' % (fix['id'], card['title'][:70]))
        print('    %r' % fix['old'])
        print(' -> %r  (%s)' % (fix['new'], fix['why']))
        card['asset'] = fix['new']

    if not write:
        print('\n(сухой прогон, для записи — --write)')
        return

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('\nЗаписано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
