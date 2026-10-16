# -*- coding: utf-8 -*-
"""Ворота пропустили вторую карточку той же сделки: «Национализированную
«Леста Игры» продали частным инвесторам» (`g004b707a`, Pravo.ru) — тот же
переход прав на группу «Леста Игры», что уже в карточке `gd09e0945`
(построена по Коммерсанту/Ведомостям/Frank Media/CNews). `near_duplicate()`
не поймал совпадение (заголовок разный: «продали» вместо «приобрела», нет
общих слов сверх порога), а автосборка полей дала мусор — `asset`:
«частным», `seller`: «Национализированную «Леста Игры»», `sum`: «10 млрд ₽»
(это не цена сделки, а трёхлетний инвестиционный план покупателя).

Полный текст Pravo.ru прочитан — ни одного факта сверх уже записанных в
`gd09e0945` (консорциум, 100% трёх юрлиц, план на 10 млрд ₽, пять новых
продуктов, прежнее руководство); единственная деталь вне карточки —
комментарий замминистра Моисеева в СЕНТЯБРЕ про ожидаемую «очень дорогую»
оценку без суммы — слишком расплывчато и это факт момента ДО закрытия,
не стоит того, чтобы вносить (см. KNOWN_ISSUES.md про анонс vs закрытие).

Запуск:
    python3 pipeline/discard_g004b707a_dup_of_lesta_2026_10_16.py            # сухой прогон
    python3 pipeline/discard_g004b707a_dup_of_lesta_2026_10_16.py --write    # применить
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

CARD_ID = 'g004b707a'
URL = 'https://pravo.ru/news/266362/'
TITLE_PART = 'Национализированную «Леста Игры» продали частным инвесторам'
RAW_TITLE_KEY = promote.raw_key(TITLE_PART)
TARGET_CARD = 'gd09e0945'


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending['cards'] if c['id'] == CARD_ID), None)
    assert card is not None, '%s не найдена в pending.json' % CARD_ID
    assert card['title'] == TITLE_PART, 'заголовок не совпал: %r' % card['title']

    state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in state.get('discarded_urls', {}), 'URL уже отмечен в discarded_urls'

    print('ВЫКИДЫВАЮ %s: %s (дубль %s)' % (CARD_ID, card['title'], TARGET_CARD))
    print('  discarded_urls += %s' % URL)
    print('  raw_titles += %s -> enrich:%s' % (RAW_TITLE_KEY, TARGET_CARD))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_pending = json.load(open(PENDING, encoding='utf-8'))
    fresh_pending['cards'] = [c for c in fresh_pending['cards'] if c['id'] != CARD_ID]
    json.dump(fresh_pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fresh_state = json.load(open(STATE, encoding='utf-8'))
    assert URL not in fresh_state.get('discarded_urls', {}), 'URL отметили параллельно — перечитайте'
    fresh_state.setdefault('discarded_urls', {})[URL] = {
        'reason': 'та же сделка, что в %s — дубль без нового факта' % TARGET_CARD,
        'date': datetime.now(timezone.utc).date().isoformat(),
    }
    fresh_state.setdefault('raw_titles', {})[RAW_TITLE_KEY] = 'enrich:%s' % TARGET_CARD
    json.dump(fresh_state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
