# -*- coding: utf-8 -*-
"""Второй проход ворот пропустил ту же историю: «Украденную нацистами
картину Кандинского продали с аукциона за три миллиарда рублей»
(`gbc24d6f4`) — пересказ Lenta.ru того же аукциона Christie's (Лондон),
что уже отклонён как `ge8be176f` (та же картина, та же сумма: £27 млн ≈
3 млрд ₽). Рубли в сумме и русское имя художника замаскировали отсутствие
российского рынка — тот же класс, что уже чинился для Netflix/ЧМ-2030 и
первого прохода Кандинского (KNOWN_ISSUES.md, 14-15 октября). Парсинг
заголовка дал тот же мусор: seller = «Украденную нацистами картину
Кандинского», asset = «с аукциона за три миллиарда рублей» — не имена,
обрывки предложения.

Карточка дошла до pending.json через resolve_duplicates.py (ответ
`separate` на ложное совпадение с gc2abcc97 по словам «миллиард»/
«рублей» — другая, не связанная сделка о покупке юаней ЦБ), а не через
обычный гейт promote.py — тот же механический провал, что обсуждается
в KNOWN_ISSUES.md для match.py.

Запуск:
    python3 pipeline/discard_gbc24d6f4_kandinsky_not_russian_market_2026_10_15.py            # сухой прогон
    python3 pipeline/discard_gbc24d6f4_kandinsky_not_russian_market_2026_10_15.py --write    # применить
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

CARD_ID = 'gbc24d6f4'
URL = ('https://lenta.ru/news/2026/10/15/'
       'ukradennuyu-natsistami-kartinu-kandinskogo-prodali-s-auktsiona-za-tri-milliarda-rubley/')
TITLE_PART = 'Украденную нацистами картину Кандинского'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % CARD_ID)
        return 0
    if TITLE_PART not in str(card.get('title') or ''):
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (CARD_ID, card.get('title')))
        return 1
    if card.get('draft_sent') or card.get('post_draft_sent'):
        print('НЕ ТРОГАЕМ %s — уже показана в консоли, решает человек' % CARD_ID)
        return 1
    print('ВЫКИДЫВАЕМ %s %s' % (CARD_ID, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    data['cards'] = [c for c in data['cards'] if c['id'] != CARD_ID]
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    state = json.load(open(STATE, encoding='utf-8'))
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID,
        'title': card['title'],
        'at': datetime.now(timezone.utc).isoformat(),
        'note': 'не российский рынок: тот же аукцион Christie\'s (Лондон), что уже отклонён как '
                'ge8be176f — пересказ Lenta.ru с переводом суммы в рубли',
    }
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
