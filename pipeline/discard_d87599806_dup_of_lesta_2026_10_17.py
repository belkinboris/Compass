# -*- coding: utf-8 -*-
"""Очередь дублей отправила черновик RB.ru («Государство продало «Леста
Игры» — новый владелец вложит в игровую индустрию до 10 млрд ₽»,
`d87599806`) на кандидата `gd9ccfdd2` — но та карточка в тот же прогон
08:20 МСК слилась в `gd09e0945` (`merge_lesta_negotiations_stage_
2026_10_17.py`): `gd9ccfdd2` больше не существует, `resolve_duplicates.py
--queue` сам сообщил «НЕ НАЙДЕНА — id мог устареть». Единственный новый
факт черновика (размер аудитории — 6,5 млн игроков в месяц) уже перенесён
в `gd09e0945.extra` отдельной правкой (`fixes/written_gd09e0945_audience_
2026_10_17.py`); остальное (консорциум, 100% трёх юрлиц, план на 10 млрд
₽) — повтор уже записанного. Убираю запись из очереди дублей и отмечаю
источник как дополнение к `gd09e0945`, тем же приёмом, что вчера для
Pravo.ru.

Запуск:
    python3 pipeline/discard_d87599806_dup_of_lesta_2026_10_17.py            # сухой прогон
    python3 pipeline/discard_d87599806_dup_of_lesta_2026_10_17.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUPLICATES = os.path.join(ROOT, 'data', 'inbox', 'duplicates', '2026-10-17.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

DRAFT_ID = 'd87599806'
URL = ('https://rb.ru/news/gosudarstvo-prodalo-lesta-igry-novyj-vladelec-vlozhit-v-igrovuyu-'
       'industriyu-do-10-mlrd/')
TITLE = 'Государство продало «Леста Игры» — новый владелец вложит в игровую индустрию до 10 млрд ₽'
RAW_TITLE_KEY = promote.raw_key(TITLE)
TARGET_CARD = 'gd09e0945'


def main(write=False):
    dups = json.load(open(DUPLICATES, encoding='utf-8'))
    items = dups.get('items', [])
    match = [i for i in items if i.get('draft', {}).get('draft_id') == DRAFT_ID]
    assert match, '%s не найден в очереди дублей' % DRAFT_ID
    assert match[0]['draft']['title'] == TITLE, 'заголовок не совпал: %r' % match[0]['draft']['title']

    state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in state.get('discarded_urls', {}), 'URL уже отмечен в discarded_urls'

    print('ВЫКИДЫВАЮ %s: %s' % (DRAFT_ID, TITLE))
    print('  duplicates/2026-10-17.json: запись убрана из очереди')
    print('  discarded_urls += %s' % URL)
    print('  raw_titles += %s -> enrich:%s' % (RAW_TITLE_KEY, TARGET_CARD))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_dups = json.load(open(DUPLICATES, encoding='utf-8'))
    fresh_dups['items'] = [i for i in fresh_dups.get('items', [])
                           if i.get('draft', {}).get('draft_id') != DRAFT_ID]
    json.dump(fresh_dups, open(DUPLICATES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fresh_state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in fresh_state.get('discarded_urls', {}), 'URL отметили параллельно — перечитайте'
    fresh_state.setdefault('discarded_urls', {})[URL] = {
        'reason': 'кандидат на дубль (gd9ccfdd2) слит в %s в этом же прогоне — новый факт перенесён отдельной правкой' % TARGET_CARD,
        'date': datetime.now(timezone.utc).date().isoformat(),
    }
    fresh_state.setdefault('raw_titles', {})[RAW_TITLE_KEY] = 'enrich:%s' % TARGET_CARD
    json.dump(fresh_state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
