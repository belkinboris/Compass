# -*- coding: utf-8 -*-
"""Прогон притока 10:20/11:20 МСК (13 октября 2026) пропустил через ворота
две не-сделки — оба случая классические: черновик, у которого единственный
содержательный след — обрывок заголовка в `buyer_name`/`asset`, то есть
ворота не нашли предмет и стороны, но пропустили по формальному признаку.

`g0caf400c` («Страны Европы активно покупают российскую нефть, заявил
Песков») — не сделка вовсе: заявление пресс-секретаря о макропотоках нефти,
без единой стороны, без компании, без суммы. `buyer_name` = «Страны Европы
активно» и `asset` = «российскую нефть, заявил Песков» — оба поля —
обрывки одного и того же предложения, разрезанного по слову «покупают».

`g7c764169` («Paramount купила Warner, а заодно HBO, CNN, CBS... и $80 млрд
долга! И казалось бы, при чём тут Эллисон?») — источник Smart-Lab, блог-пост
с кликбейтным заголовком; сама заметка внутри — не о слиянии Paramount и
Warner, а разбор рынка облигаций (`events[0].note` — обрывок про рейтинг BB,
никак не о сделке). И даже если бы заметка была по существу, это сделка
американского медиарынка без какой-либо связи с российским рынком — ровно
тот класс, что уже описан в `docs/intake_run.md` (Eni/Индонезия, 12 октября
2026): заголовок на русском, но ни продавца, ни покупателя, ни актива,
называющих что-то российское.

Действие — то же самое, что кнопка «🗑 Выкинуть»: карточки убираются из
`pending.json`, URL — в `discarded_urls`, черновик — `decided_raw[...]=
'auto-drop'` и `raw_titles` (как делает `raw_screen.py --drop`, но эти
черновики не попали в hold-файл — прошли ворота как «ПУСТИТЬ», поэтому
`raw_screen.py --drop` их не видит, и запись сделана тем же способом вручную).

Запуск:
    python3 pipeline/discard_pending_cards_2026_10_13_peskov_paramount.py            # сухой прогон
    python3 pipeline/discard_pending_cards_2026_10_13_peskov_paramount.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

CARDS = [
    {
        'id': 'g0caf400c',
        'draft_id': 'd30592972',
        'url': 'https://ria.ru/20261013/peskov-2124168153.html',
        'title_part': 'Страны Европы активно покупают российскую нефть',
        'reason': 'не сделка: заявление пресс-секретаря о покупках нефти странами Европы — '
                  'без сторон, без компании, без суммы; buyer_name/asset — обрывки одного '
                  'предложения заголовка',
    },
    {
        'id': 'g7c764169',
        'draft_id': 'd11301095',
        'url': 'https://smart-lab.ru/blog/1361993.php',
        'title_part': 'Paramount купила Warner',
        'reason': 'не сделка для базы: блог-пост с кликбейтным заголовком о рынке облигаций '
                  '(текст — не о сделке Paramount/Warner); и даже по заголовку — сделка '
                  'американского медиарынка без связи с российским рынком',
    },
]


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    by_id = {c['id']: c for c in pending['cards']}
    state = json.load(open(STATE, encoding='utf-8'))

    to_remove = []
    for spec in CARDS:
        card = by_id.get(spec['id'])
        if not card:
            print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % spec['id'])
            continue
        if spec['title_part'].lower() not in str(card.get('title') or '').lower():
            print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (spec['id'], card.get('title')))
            continue
        if card.get('draft_sent') or card.get('post_draft_sent'):
            print('НЕ ТРОГАЕМ %s — уже показана в консоли, решает человек' % spec['id'])
            continue
        to_remove.append(spec)
        print('ВЫКИДЫВАЕМ %s %s' % (spec['id'], card['title']))

    if not to_remove:
        print('Нечего применять.')
        return 0
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    remove_ids = {s['id'] for s in to_remove}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in remove_ids]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    for spec in to_remove:
        state.setdefault('discarded_urls', {})[spec['url']] = {
            'id': spec['id'],
            'title': by_id[spec['id']]['title'],
            'at': datetime.now(timezone.utc).isoformat(),
            'note': spec['reason'],
        }
        state.setdefault('decided_raw', {})[spec['draft_id']] = 'auto-drop'
        state.setdefault('raw_titles', {})[promote.raw_key(by_id[spec['id']]['title'])] = 'auto-drop'
        state.setdefault('auto_drop_reasons', {})[spec['draft_id']] = spec['reason']
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: %d карточек убрано.' % len(to_remove))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
