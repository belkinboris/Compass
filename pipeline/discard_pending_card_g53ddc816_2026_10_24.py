# -*- coding: utf-8 -*-
"""Убрать из очереди предпросмотра карточку g53ddc816 (Воронежский
«Золотой Початок» завершил присоединение хохольской структуры группы) —
ворота `promote.py` пропустили её как M&A (есть buyer_name/asset), но
статья целиком прочитана и это внутригрупповая реорганизация, а не
сделка: ООО «Золотой Початок Хохольский» — дочерняя структура ТОЙ ЖЕ
группы (участники «Золотого Початка» по ЕГРЮЛ — АО «Национальные
Стратегические Активы» 94,88% и ООО «Недвижимость» 5,11%, управляющая
компания НСА), присоединение убрало техническую дочку, а не сменило
конечного владельца. Тот же класс, что уже отклонённое в этот день
слияние ОМПК («Останкино-Липецк» → «Останкино-Воронеж»).

Действие — то же самое, что кнопка «🗑 Выкинуть» в консоли: карточка
убирается из `pending.json`, URL — в `discarded_urls`, черновик —
`decided_raw`/`raw_titles` (как `raw_screen.py --drop`), чтобы
`promote.py` не пропустил тот же черновик повторно (docs/intake_run.md,
«ворота пропустили не-сделку»).

Запуск:
    python3 pipeline/discard_pending_card_g53ddc816_2026_10_24.py            # сухой прогон
    python3 pipeline/discard_pending_card_g53ddc816_2026_10_24.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

CARD_ID = 'g53ddc816'
DRAFT_ID = 'd73795914'
URL = ('https://abireg.ru/newsitem/118809-voronezhskiy-zolotoy-pochatok-'
       'zavershil-prisoedinenie-khokholskoy-struktury-gruppy/')
TITLE_PART = 'Золотой Початок'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if not card:
        print('НЕ ТРОГАЕМ %s — карточки уже нет в очереди' % CARD_ID)
        return 0
    if TITLE_PART.lower() not in str(card.get('title') or '').lower():
        print('НЕ ТРОГАЕМ %s — заголовок не совпадает: %r' % (CARD_ID, card.get('title')))
        return 1
    if card.get('draft_sent') or card.get('post_draft_sent'):
        print('НЕ ТРОГАЕМ %s — карточка уже показана в консоли, тут решает человек' % CARD_ID)
        return 1
    print('ВЫКИДЫВАЕМ %s %s' % (CARD_ID, card['title']))
    print('           внутригрупповая реорганизация (присоединение дочки той же группы), не сделка')
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
        'note': 'внутригрупповая реорганизация: ООО «Золотой Початок Хохольский» — дочка той же '
                'группы (НСА), присоединена к головному «Золотому Початку» — конечный владелец не '
                'менялся, не сделка для базы',
    }
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'auto-drop'
    state.setdefault('raw_titles', {})[promote.raw_key(card['title'])] = 'auto-drop'
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено: карточка убрана, URL и черновик записаны в память решений.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
