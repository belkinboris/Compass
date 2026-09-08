# -*- coding: utf-8 -*-
"""Приток 8 сентября 2026 (10:20 МСК) — карточка g0edf3b89 («Рок-музыкант
инвестировал в косметическую фабрику «Свобода»», Retailer.ru) — тот же
сюжет, что уже был построен вчера (7 сентября) как карточка g66c1e0ec
(Максим Севрюков / «Свобода», три источника Коммерсанта) и затем ОТКЛОНЁН
решением из консоли: все три адреса Коммерсанта уже стоят в
`discarded_urls` под id g66c1e0ec (отметка «at»: 2026-09-07T17:27:08Z).
Раз история этой сделки уже отклонена по существу, пересказ того же
сюжета другим изданием не должен всплывать снова под новым id — карточка
снимается, а адрес Retailer.ru добавляется в тот же список отклонённых.

Заодно ворота пропустили и здесь родовое описание вместо имени
(«Рок-музыкант» вместо «Максим Севрюков», «косметическая фабрика
«Свобода»» вместо «Свобода») — тот же класс дефекта, что и раньше, но
он вторичен: главная причина снятия — уже принятое решение отклонить.

Запуск: python3 pipeline/fix_discard_svoboda_retailer_duplicate.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://retailer.ru/rok-muzykant-investiroval-v-kosmeticheskuju-fabriku-svoboda/'
CARD_ID = 'g0edf3b89'
PRIOR_DISCARD_ID = 'g66c1e0ec'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID}, найдено {len(matches)}'
    card = matches[0]
    assert any(len(s) > 1 and s[1] == URL for s in (card.get('src') or []))
    assert URL not in state.get('discarded_urls', {})
    prior = [v for v in state.get('discarded_urls', {}).values() if v.get('id') == PRIOR_DISCARD_ID]
    assert prior, f'ожидалась уже отклонённая карточка {PRIOR_DISCARD_ID} в discarded_urls'

    pending['cards'] = [c for c in pending['cards'] if c['id'] != CARD_ID]
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID, 'title': card.get('title'),
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    }

    print(f'Снята карточка {CARD_ID} (тот же сюжет, что уже отклонён под {PRIOR_DISCARD_ID}).')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
