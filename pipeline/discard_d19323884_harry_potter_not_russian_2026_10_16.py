# -*- coding: utf-8 -*-
"""Ворота пропустили не-сделку: «Редкое издание «Гарри Поттера» с
множеством опечаток продали белее чем за £300 000» (`d19323884`,
Forbes.ru) — аукцион редкой книги у британского аукционного дома Heritage
Auctions, без связи с российским рынком и без сторон-компаний; поля
автосборки — мусор (`seller`: заголовок целиком, `asset`: «белее чем за
£300 000»). Замечено до записи (`promote.py` без `--write` показал
«ПУСТИТЬ»), поэтому карточка не создаётся вовсе — отметка в
`raw_titles`/`discarded_urls` ставится тем же способом, что и у уже
созданных и выброшенных карточек (Текслер, Дима Билан).

Запуск:
    python3 pipeline/discard_d19323884_harry_potter_not_russian_2026_10_16.py            # сухой прогон
    python3 pipeline/discard_d19323884_harry_potter_not_russian_2026_10_16.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

URL = ('https://www.forbes.ru/forbeslife/570481-redkoe-izdanie-garri-pottera-s-mnozestvom-'
       'opecatok-prodali-belee-cem-za-gbp300-000')
TITLE = 'Редкое издание «Гарри Поттера» с множеством опечаток продали белее чем за £300 000'
RAW_TITLE_KEY = promote.raw_key(TITLE)
REASON = ('не сделка для этой базы: аукцион редкой книги у британского аукционного дома '
          'Heritage Auctions — не российский рынок, нет сторон-компаний')


def main(write=False):
    state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in state.get('discarded_urls', {}), 'URL уже отмечен в discarded_urls'

    print('ОТКЛОНЯЮ до записи: %s' % TITLE)
    print('  discarded_urls += %s' % URL)
    print('  raw_titles += %s -> drop' % RAW_TITLE_KEY)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in fresh_state.get('discarded_urls', {}), 'URL отметили параллельно — перечитайте'
    fresh_state.setdefault('discarded_urls', {})[URL] = {
        'reason': REASON,
        'date': datetime.now(timezone.utc).date().isoformat(),
    }
    fresh_state.setdefault('raw_titles', {})[RAW_TITLE_KEY] = 'drop'
    json.dump(fresh_state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
