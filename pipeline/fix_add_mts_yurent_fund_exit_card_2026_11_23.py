# -*- coding: utf-8 -*-
"""Новая карточка по решению владельца «это сделка — в работу» (консоль,
23 ноября 2026, draft_id d02193838): ЗПИФ «Цифровые горизонты» под
управлением АО «УК «Молния» 5 ноября 2026 года вышел из состава участников
ООО «Юрентбайк.ру» (кикшеринг «Юрент»), его 10,49% перешли структуре МТС,
доля МТС выросла до 95,1% («Коммерсантъ», 23 ноября 2026, по данным СПАРК).

ПОЧЕМУ РАЗОВЫЙ СКРИПТ. Приток пометил сырье `enrich:ga95746a3` — как новость
о старой карточке «МТС купил 68,8% «Юрента»» (январь 2024), и сырье, которое
владелец признал сделкой, пропало из работы. Это другая сделка: другой
продавец (фонд, а не основатели), другая доля, другой год
(known_issues/intake.md). Карточки связаны `related_deal_ids`, новая несет
`separate_transaction_reviewed`, чтобы поиск дублей по общему предмету не
сводил ее со старой снова.

Стороны. Покупатель — профиль МТС (g69c88bc7): источник пишет «перешла
структуре мажоритарного акционера МТС», юрлицо структуры не названо.
Предмет — ООО «ЮрентБайк.ру» (g30d7fdce). Продавец — текстом «ЗПИФ
«Цифровые горизонты»»: профиля фонда в базе нет (gf3e0918b «Молния» —
челябинская розничная сеть ООО «Молл», не управляющая компания); профиль
фонда заводит приемка (`accept_card.py`, ответ `profiles`), как у других
ЗПИФ базы.

Сумма — «900 млн ₽ (по оценке)»: стороны цену не называли, «Коммерсантъ»
пишет о доле «оценочной стоимостью в 900 млн руб.» (docs/card_money.md,
«Что идет в сумму»); кто и как оценивал — в `eco.val`.

Прозу (`eco.*`, `law.struct`) пишет партия
`pipeline/ingest/fixes/written_2026_11_23_mts_yurent_fund_exit.py` через
`review.py --write`. Приемку и второе чтение делают отдельные агенты.

ИСТОЧНИКИ:
  Коммерсантъ, https://www.kommersant.ru/doc/9127061 (прочитан целиком)
  Русский венчур, https://t.me/rusven/7862 (пересказ, откуда пришло сырье)

Запуск:
    python3 pipeline/fix_add_mts_yurent_fund_exit_card_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_mts_yurent_fund_exit_card_2026_11_23.py --write    # запись
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
TG_URL = 'https://t.me/rusven/7862'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


CARD_ID = gid('mts-yurent-cifrovye-gorizonty-10-49-2026-11-05')
MTS_ID = 'g69c88bc7'
YURENT_ID = 'g30d7fdce'
RELATED = 'ga95746a3'   # «МТС купил 68,8% «Юрента»», январь 2024
SELLER = 'ЗПИФ «Цифровые горизонты»'


def build_card():
    return {
        'id': CARD_ID,
        'date': '2026-11-05',
        'date_basis': 'registry',
        'title': 'МТС купил 10,49% «Юрента» у ЗПИФ «Цифровые горизонты»',
        'ind': 'Транспорт и логистика',
        'type': 'M&A',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'src': [['Коммерсантъ', KOMM_URL]],
        'discovery_src': [['Русский венчур (Telegram)', TG_URL]],
        'from_ingest': True,
        'sum': '900 млн ₽ (по оценке)',
        'eco': {
            'sum': '900 млн ₽ (по оценке)',
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
        'buyer': MTS_ID,
        'target': YURENT_ID,
        'seller': SELLER,
        'seller_src': 'text',
        'related_deal_ids': [RELATED],
        'separate_transaction_reviewed': True,
        'party_evidence': {
            'buyer': [{
                'value': 'МТС', 'field': 'buyer',
                'method': 'manual_source_review', 'url': KOMM_URL,
            }],
            'seller': [{
                'value': SELLER, 'field': 'seller',
                'method': 'manual_source_review', 'url': KOMM_URL,
            }],
            'target': [{
                'value': 'ООО «Юрентбайк.ру»', 'field': 'target',
                'method': 'manual_source_review', 'url': KOMM_URL,
            }],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {
            'draft_id': 'd02193838',
            'title': ('#газеты Закрытый паевой инвестфонд «Цифровые горизонты» под управлением '
                      'АО «УК «Молния» вышел из капитала кикшерингового сервиса «Юрент». 10,49%, '
                      'принадлежавшие ранее фонду, перешли структуре мажорита'),
        },
        'accepted_notes': {
            'searched': ('«Коммерсантъ», 23.11.2026 (первоисточник, прочитан целиком через '
                         'fetch_article_texts.py; данные о переходе доли — из СПАРК, дата 5 ноября '
                         '2026 года); пост «Русского венчура» t.me/rusven/7862 — пересказ той же '
                         'статьи. Юрлицо структуры МТС, получившей долю, источник не называет; '
                         'МТС и УК «Молния» на запросы издания не ответили, цена сторонами не '
                         'названа. Профиля ЗПИФ «Цифровые горизонты» и АО «УК «Молния» в базе нет '
                         '(поиск по именам и описаниям профилей; gf3e0918b «Молния» — челябинская '
                         'розничная сеть, g196b511d «Молния Финанс» — другая компания).'),
        },
    }


def twin(cards):
    """Карточка той же сделки, если ее уже собрал кто-то другой."""
    out = []
    for c in cards:
        blob = json.dumps(c, ensure_ascii=False)
        if c.get('id') == CARD_ID or (
                'Юрент' in str(c.get('title')) and ('10,49' in str(c.get('title'))
                                                   or 'Цифровые горизонты' in str(c.get('title')))) \
                or (c.get('from_raw') or {}).get('draft_id') == 'd02193838' \
                or KOMM_URL in blob and c.get('id') != RELATED and KOMM_URL in json.dumps(c.get('src'), ensure_ascii=False):
            out.append(c['id'])
    return out


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}

    found = twin(pending['cards'] + data['deals'])
    assert not found, 'такая карточка уже есть: %s' % found
    assert MTS_ID in data['companies'] and data['companies'][MTS_ID]['name'] == 'МТС'
    assert YURENT_ID in data['companies'] and 'Юрент' in data['companies'][YURENT_ID]['name']
    assert any(d['id'] == RELATED for d in data['deals']), 'связанной карточки нет в базе'

    card = build_card()
    import tag_themes
    import title_standard
    themes = tag_themes.add_themes(card)
    assert title_standard.verb_ok(card), 'заголовок не по стандарту: %s' % title_standard.hint(card)

    print('Карточка: %s' % card['id'])
    print('  title: %s' % card['title'])
    print('  date: %s (%s), status: %s' % (card['date'], card['date_basis'], card['status']))
    print('  themes: %s' % themes)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    assert not twin(pending['cards']), 'карточка уже в очереди'
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: 1 карточка в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
