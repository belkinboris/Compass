# -*- coding: utf-8 -*-
"""Ворота пропустили не-сделку: «Челябинский губернатор Текслер купит
подарки к Новому году за 11 миллионов» (`g3bd97268`) — автосборка увидела
в заголовке «купит» и завела карточку типа M&A с buyer_name=«Челябинский
губернатор Текслер», asset=«подарки к Новому году». Это госзакупка
региональным правительством новогодних подарков, не корпоративная
M&A-сделка, — вне предмета этой базы (ни покупателя-компании, ни
продавца, ни рыночного актива).

Запуск:
    python3 pipeline/discard_g3bd97268_not_corporate_deal_2026_10_16.py            # сухой прогон
    python3 pipeline/discard_g3bd97268_not_corporate_deal_2026_10_16.py --write    # применить
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

CARD_ID = 'g3bd97268'
URL = 'https://ura.news/news/1053136718'
TITLE_PART = 'Челябинский губернатор Текслер купит подарки'
RAW_TITLE_KEY = promote.raw_key(
    'Челябинский губернатор Текслер купит подарки к Новому году за 11 миллионов: '
    'что будет в подарочном мешке. Фото')
REASON = ('не сделка для этой базы: закупка губернатором новогодних подарков — '
          'госзакупка, не корпоративная M&A сделка')


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, '%s не найдена в pending.json' % CARD_ID
    assert TITLE_PART in card['title'], 'заголовок не совпал: %r' % card['title']

    state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in state.get('discarded_urls', {}), 'URL уже отмечен в discarded_urls'

    print('ВЫКИДЫВАЮ %s: %s' % (CARD_ID, card['title']))
    print('  discarded_urls += %s' % URL)
    print('  raw_titles += %s -> drop' % RAW_TITLE_KEY)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_pending = json.load(open(PENDING, encoding='utf-8'))
    fresh_pending['cards'] = [c for c in fresh_pending['cards'] if c['id'] != CARD_ID]
    json.dump(fresh_pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

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
