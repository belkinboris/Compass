# -*- coding: utf-8 -*-
"""«"Норникель" выкупил по оферте 95,5% выпуска облигаций с погашением в
мае 2030 г. на $477,65 млн» (`g0e2f181f`) — казначейская операция с
собственным долгом эмитента, не сделка со сменой контроля: карточка несла
buyer_name="«Норникель»", asset="95,5% выпуска облигаций..." — бессмыслица
(эмитент не может купить сам себя). Прошла оба гейта, потому что
`classify.looks_like_deal()` не различал выкуп ДОЛИ/АКЦИЙ (buyback,
профильная сделка) и выкуп компанией СОБСТВЕННЫХ облигаций по оферте
(казначейская операция) — правило `BOND_BUYBACK` добавлено в classify.py
тем же прогоном.

ПЕРВАЯ ВЕРСИЯ этого скрипта целилась в pending.json (карточка ждала
решения) — но пока правка готовилась, рутина публикации применила таймаут
молчания раньше: карточка уже в `deals_promoted.json`
(`Публикация: 2 карточки вышли по таймауту...`, 22 августа). Telegram-пост
по ней НЕ уходил (`telegram_posts.get('g0e2f181f')` — `None`), поэтому
удаление из базы ничего не оставляет висеть в канале.

Запуск: python3 pipeline/fix_norilsk_bond_buyback_false_positive.py           # проверка
        python3 pipeline/fix_norilsk_bond_buyback_false_positive.py --write   # запись
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g0e2f181f'
EXPECTED_TITLE = ('«Норникель» выкупил по оферте 95,5% выпуска облигаций '
                   'с погашением в мае 2030 г. на $477,65 млн')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json — уже почищена?' % CARD_ID
    assert card['title'] == EXPECTED_TITLE, 'заголовок изменился, не трогаю: %r' % card['title']
    assert not data.get('telegram_posts', {}).get(CARD_ID), (
        '%r несёт telegram_posts — пост в канал уже ушёл, автоматическое '
        'удаление карточки оставило бы мёртвую ссылку в канале; решать '
        'вручную' % CARD_ID)

    print('УДАЛЯЮ %s из базы: облигационная оферта, не сделка (не M&A и не смена контроля)'
          % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    state = promote.load_state()
    now = datetime.now(timezone.utc)
    for s in card.get('src') or []:
        if len(s) > 1 and str(s[1]).startswith('http'):
            state.setdefault('discarded_urls', {})[str(s[1])] = {
                'id': card['id'], 'title': card.get('title'),
                'at': now.isoformat(timespec='seconds')}
    promote.save_state(state)

    data['deals'] = [c for c in data['deals'] if c['id'] != CARD_ID]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
