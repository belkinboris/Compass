# -*- coding: utf-8 -*-
"""Ворота пропустили «Картину Кандинского «Красочная жизнь» продали на
торгах за 27 млн фунтов» (`ge8be176f`) — заголовок про картину и аукцион
по-русски замаскировал то, что у истории нет НИ ОДНОГО признака
российского рынка: лондонский Christie's, продавец — наследники
нидерландской семьи Левенштейн (возврат картины после реституции
нацистской конфискации), покупатель не назван, ни одной российской
стороны. Кандинский родился в России, но это не делает аукцион его
картины в Лондоне российской сделкой. Тот же класс, что уже чинился
для Netflix/ЧМ-2030 (KNOWN_ISSUES.md, 14 октября) — предмет по-русски
маскирует отсутствие связи с рынком. Заодно парсинг заголовка дал
бессмысленные значения (seller = «Картину Кандинского...», asset =
«на торгах») — ещё один сигнал, что гейт здесь ошибся.

Запуск:
    python3 pipeline/discard_ge8be176f_kandinsky_not_russian_market_2026_10_15.py            # сухой прогон
    python3 pipeline/discard_ge8be176f_kandinsky_not_russian_market_2026_10_15.py --write    # применить
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

CARD_ID = 'ge8be176f'
URL = 'https://www.kommersant.ru/doc/9026811'
TITLE_PART = 'Картину Кандинского «Красочная жизнь»'


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
        'note': 'не российский рынок: аукцион Christie\'s в Лондоне, продавец — наследники '
                'нидерландской семьи Левенштейн, ни одной российской стороны',
    }
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL записан в discarded_urls.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
