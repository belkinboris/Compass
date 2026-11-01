# -*- coding: utf-8 -*-
"""Решение владельца в консоли 1 ноября 2026 (заметка 1154): «Сливай. Я удалил 132».

Пара 103 разбора G15 (`pipeline/archive/2026-10/fix_g15_base_duplicates_2026_10_31.py`):
ЗПИФ «ВИМ Недвижимость» купил БЦ «Фрейм» у Forma — одна сделка под двумя id,
у каждой свой пост в канале. Владелец удалил пост 132 (карточка gffe3c2d0)
руками; за сделкой остается пост 130 (g73dba9d6).

Слияние — общим `merge_duplicate_deals_batch.Merge`: источники TAdviser и
@LawFirms переезжают, `merged[gffe3c2d0] = g73dba9d6`. Юрконсультант
покупателя (ALUMNI Partners) переносится в `law.adv` выжившей карточки.
Запись удаленного поста 132 снимается из `telegram_posts` и
`telegram_post_state` ДО слияния: поста в канале больше нет, и рутина не
должна пытаться его править.

    python3 pipeline/fix_frame_merge_2026_11_01.py           # сухой прогон
    python3 pipeline/fix_frame_merge_2026_11_01.py --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'pipeline'))
import merge_duplicate_deals_batch as mdb  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
KEEP, DROP, KEEP_POST, DROP_POST = 'g73dba9d6', 'gffe3c2d0', 130, 132

SPEC = dict(
    keep=KEEP, drop=DROP,
    reason='Одна сделка: ЗПИФ «ВИМ Недвижимость» под управлением УК «ВИМ Сбережения» купил БЦ «Фрейм» у Forma.',
    add_src=[['TAdviser', 'https://www.tadviser.ru/a/968020'],
             ['Телеграм-канал @LawFirms', 'https://t.me/LawFirms/11469']],
)
ADV = [['Юридический консультант покупателя', 'ALUMNI Partners',
        'Сопровождала ЗПИФ «ВИМ Недвижимость» под управлением УК «ВИМ Сбережения» в приобретении у девелопера '
        'Forma строящегося бизнес-центра FRAME Workplace.']]


def run(data: dict, write: bool) -> list[str]:
    errors = []
    posts = data.get('telegram_posts', {})
    if posts.get(KEEP) != KEEP_POST:
        errors.append(f'telegram_posts[{KEEP}] = {posts.get(KEEP)!r}, ожидался {KEEP_POST}')
    if posts.get(DROP) != DROP_POST:
        errors.append(f'telegram_posts[{DROP}] = {posts.get(DROP)!r}, ожидался {DROP_POST}')
    by_id = {d['id']: d for d in data['deals']}
    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    if not keep or not drop:
        return errors + ['нет одной из карточек (уже слита?)']
    if (keep.get('law') or {}).get('adv'):
        errors.append(f'law.adv у {KEEP} уже заполнен')
    if (drop.get('law') or {}).get('adv') != ADV:
        errors.append(f'law.adv у {DROP} не совпадает с переносимым')
    # Удаленный владельцем пост снимается до слияния, иначе Merge откажет
    # («у обеих карточек свои посты»).
    posts.pop(DROP, None)
    data.get('telegram_post_state', {}).pop(DROP, None)
    m = mdb.Merge(data, SPEC, mdb.industries(), {t for d in data['deals'] for t in (d.get('themes') or [])})
    m.check()
    print(f'{DROP} -> {KEEP}: пост {DROP_POST} снят (удален владельцем), пост {KEEP_POST} остается')
    for line in m.plan:
        print(line)
    print('  law.adv <- ALUMNI Partners')
    errors += m.errors
    print(f'FIXES на {DROP}: {mdb.strip_fixes({DROP}, write=False)}')
    if errors or not write:
        return errors
    m.apply()
    keep = next(d for d in data['deals'] if d['id'] == KEEP)
    keep.setdefault('law', {})['adv'] = ADV
    assert DROP not in {d['id'] for d in data['deals']} and data['merged'][DROP] == KEEP
    assert data['telegram_posts'][KEEP] == KEEP_POST and DROP not in data['telegram_posts']
    mdb.strip_fixes({DROP}, write=True)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    errors = run(json.load(open(DATA, encoding='utf-8')), write=False)
    if errors:
        print('ОТКАЗ:', *errors, sep='\n  ')
        return 1
    if not args.write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    errors = run(json.load(open(DATA, encoding='utf-8')), write=True)   # перечитать перед записью
    if errors:
        print('ОТКАЗ при записи:', *errors, sep='\n  ')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
