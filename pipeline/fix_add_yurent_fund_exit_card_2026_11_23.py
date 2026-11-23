# -*- coding: utf-8 -*-
"""Новая карточка: МТС купил 10,49% «Юрента» у ЗПИФ «Цифровые горизонты».

ЧТО БЫЛО НЕ ТАК. Сырье d02193838 (t.me/rusven/7862, первоисточник —
«Коммерсантъ», https://www.kommersant.ru/doc/9127061) владелец утром
23 ноября 2026 признал сделкой («это сделка — в работу»), а прогон притока
12:24 UTC пометил его `enrich:ga95746a3` — дополнением к карточке «МТС купил
68,8% «Юрента»» (январь 2024) — и ничего в нее не внес. Владелец вечером:
«Почему не проработал?». Это ОТДЕЛЬНАЯ сделка ноября 2026: фонд вышел из
капитала, его 10,49% перешли структуре МТС, доля МТС выросла до 95,1%.
Правило — `known_issues/intake.md`: выход фонда из капитала с переходом доли
мажоритарию — отдельная сделка, а не дополнение к старой карточке покупки
контроля.

ЧТО ДЕЛАЕТ СКРИПТ.
  1. Снимает неверную отметку: `decided_raw[d02193838]` и два ключа
     `raw_titles` (заголовок «Коммерсанта» и текст поста rusven) —
     `enrich:ga95746a3` -> `take` (решение владельца, как пишет его
     `approve.py`).
  2. Кладет карточку в `static/data/pending.json` (структурные поля; сумма,
     основание даты и проза — партией FIXES через `review.py --write` /
     `write_card.py`, приемка и второе чтение — свежими агентами).

Связь с прежними карточками «Юрента» (ga95746a3 — покупка контроля, 2024;
gdde6bef5 — несостоявшееся объединение с Whoosh; g211615eb, gc64703e2) — через
общий профиль `g30d7fdce` (блок «Другие сделки» на карточке и в профиле) и
через текст «Контекста».

Цитаты («Коммерсантъ», 23.11.2026):
  дата/стороны/доля — «Закрытый паевой инвестфонд «Цифровые горизонты» под
    управлением АО «УК "Молния"» 5 ноября 2026 года вышел из числа
    совладельцев операционного лица компании кикшеринга «Юрент» — ООО
    «Юрентбайк.ру», обнаружил “Ъ” в базе СПАРК. Доля фонда в 10,49% перешла
    структуре мажоритарного акционера МТС, чье участие теперь составляет
    95,1%.»

Запуск:
    python3 pipeline/fix_add_yurent_fund_exit_card_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_yurent_fund_exit_card_2026_11_23.py --write    # запись
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

KOMM_URL = 'https://www.kommersant.ru/doc/9127061'
DRAFT_ID = 'd02193838'
OLD_MARK = 'enrich:ga95746a3'
RAW_TITLE = 'Фонд «Цифровые горизонты» вышел из капитала «Юрент»'

MTS_ID = 'g69c88bc7'
YURENT_ID = 'g30d7fdce'
SELLER = 'ЗПИФ «Цифровые горизонты» под управлением АО «УК «Молния»'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


CARD_ID = gid('mts-yurent-digital-horizons-fund-exit-10.49-2026-11-05')


def build_card():
    return {
        'id': CARD_ID,
        'date': '2026-11-05',
        'title': 'МТС купил 10,49% «Юрента» у фонда «Цифровые горизонты»',
        'buyer': MTS_ID,
        'target': YURENT_ID,
        'seller': SELLER,
        'seller_src': 'text',
        'ind': 'Транспорт и логистика',
        'type': 'M&A',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'sum': 'Не раскрыта',
        'src': [['Коммерсантъ', KOMM_URL]],
        'from_ingest': True,
        'eco': {
            'sum': 'Не раскрыта',
            'share': '—',
            'val': '—',
            'target_fin': '—',
            'fin': '—',
            'rationale': '—',
            'context': '—',
            'finadv': '—',
        },
        'law': {
            'struct': '—',
            'appr': '—',
            'adv': [],
            'terms': '—',
        },
        'party_evidence': {
            'buyer': [{'value': 'МТС', 'field': 'buyer',
                       'method': 'manual_source_review', 'url': KOMM_URL}],
            'target': [{'value': 'ООО «Юрентбайк.ру»', 'field': 'target',
                        'method': 'manual_source_review', 'url': KOMM_URL}],
            'seller': [{'value': SELLER, 'field': 'seller',
                        'method': 'manual_source_review', 'url': KOMM_URL}],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': DRAFT_ID, 'title': RAW_TITLE},
    }


def fix_state(state):
    """Вернуть список (где, ключ) с неверной отметкой и поправить их на take."""
    import promote
    changed = []
    dr = state.setdefault('decided_raw', {})
    if dr.get(DRAFT_ID) == OLD_MARK:
        dr[DRAFT_ID] = 'take'
        changed.append(('decided_raw', DRAFT_ID))
    else:
        assert dr.get(DRAFT_ID) == 'take', 'неожиданная отметка сырья: %r' % dr.get(DRAFT_ID)
    rt = state.setdefault('raw_titles', {})
    keys = {promote.raw_key(RAW_TITLE)}
    sent = (state.get('raw_sent_titles') or {}).get(DRAFT_ID)
    if sent:
        keys.add(promote.raw_key(sent))
    keys |= {k for k, v in rt.items() if v == OLD_MARK and 'цифровыегоризонты' in k}
    for k in sorted(keys):
        if rt.get(k) == OLD_MARK:
            rt[k] = 'take'
            changed.append(('raw_titles', k[:60]))
    return changed


def main(write):
    import promote
    import tag_themes
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    assert CARD_ID not in {c['id'] for c in pending['cards']}, 'карточка уже в pending.json'
    assert CARD_ID not in {d['id'] for d in data['deals']}, 'карточка уже в базе'
    assert MTS_ID in data['companies'] and data['companies'][MTS_ID]['name'] == 'МТС'
    assert YURENT_ID in data['companies'] and 'Юрент' in data['companies'][YURENT_ID]['name']

    card = build_card()
    themes = tag_themes.add_themes(card)
    state = promote.load_state()
    changed = fix_state(state)
    print('Карточка: %s | %s | темы: %s' % (card['id'], card['title'], themes))
    print('Отметки сырья -> take: %s' % (changed or 'уже исправлены'))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    state = promote.load_state()            # перечитать прямо перед записью
    fix_state(state)
    promote.save_state(state)
    pending = json.load(open(PENDING, encoding='utf-8'))
    assert CARD_ID not in {c['id'] for c in pending['cards']}
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: отметки сырья и 1 карточка в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
