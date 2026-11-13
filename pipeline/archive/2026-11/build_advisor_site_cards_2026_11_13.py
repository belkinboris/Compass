# -*- coding: utf-8 -*-
"""Карточки сделок, найденных сверкой с сайтами Advance Capital и Aspring Capital
(бэклог E17, 13 ноября 2026; владелец: «Все сделки которых у нас нет надо
проработать»).

Сверка показала сделки, которых не было ни в базе, ни в очереди. Лента их не
приносила (сделки 2022–2024 годов), поэтому карточки заводятся тем же путем, что
у прежних «вне очереди» (`build_salmon_group_round_2026_10_20.py`): этот скрипт
кладет в очередь (`static/data/pending.json`) оболочку со структурными полями,
текст пишется по фактам (`write_card.py`), дальше приемка и второе чтение.

Структурные поля — по прочитанным источникам (тексты забраны на диск
`fetch_article_texts.py --write` / `save_source.py`); у каждого значения ниже
в комментарии — цитата. Финансовый консультант — со страницы сделок самой
фирмы (advancecapital.ru/sdelki/, aspring.capital/services) и из ее
пресс-релиза.

id — от ключа карточки (sha1), чтобы повторный запуск не плодил дублей.

    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py            # сухой прогон
    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py --write
    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py --write --only nms-medsi
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ASPRING = 'https://aspring.capital/services'
ADV_PR = 'https://advancecapital.ru/news/news/press-releases/%d/'
ADV_DEALS = 'https://advancecapital.ru/sdelki/'


def fin_adv(side, firm, url):
    return ['Финансовый консультант ' + side, firm,
            'Финансовый консультант в сделке, по сообщению самой фирмы. Источник: ' + url]


CARDS = [
    # 12. «Медси» / «Национальная медицинская сеть».
    #   Пресс-релиз «Медси», 11.01.2022: «сообщает о приобретении 100% долей в уставном
    #   капитале сети «Промедицина» в Уфе и сети «Диалайн» в Волгограде у текущих
    #   владельцев Национальной медицинской сети».
    #   Коммерсантъ, 12.01.2022: «Группа компаний «Медси» и «Национальная медицинская
    #   сеть» (НМС) закрыли сделку купли-продажи… Продавцами выступили фонд прямых
    #   инвестиций «Эльбрус капитал» и миноритарии «Промедицины». Сумму сделки «Медси»
    #   не раскрывает»; «в конце декабря 2021 года за «Медси» были зарегистрированы
    #   права на доли» — дня регистрации нет, дата карточки — день объявления.
    #   aspring.capital/services: «Aspring Capital выступил в сделке эксклюзивным
    #   инвестиционным консультантом владельцев НМС».
    {'key': 'nms-medsi',
     'match': ('Промедицин', 'Диалайн'),
     'draft': {
         'date': '2022-01-11',
         'title': '«Медси» купила сети клиник «Промедицина» и «Диалайн» у «Национальной медицинской сети»',
         'ind': 'Здравоохранение', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['«Медси»', 'https://medsi.ru/press-centr/news/medsi-priobrela-kliniki-natsionalnoy-meditsinskoy-seti-v-ufe-i-volgograde/'],
                 ['Коммерсантъ', 'https://www.kommersant.ru/doc/5158318'],
                 ['РБК', 'https://ufa.rbc.ru/ufa/12/01/2022/61deb1979a79471e7dc5f5d7'],
                 ['Vademecum', 'https://vademec.ru/news/2022/01/11/medsi-zakryla-sdelku-po-pokupke-aktivov-natsionalnoy-meditsinskoy-seti/'],
                 ['Aspring Capital', ASPRING]],
         'buyer_name': '«Медси»',
         'asset': 'Сети клиник «Промедицина» и «Диалайн»',
         'seller': '«Национальная медицинская сеть»',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'announcement'},
     'finadv': 'Aspring Capital — эксклюзивный инвестиционный консультант владельцев «Национальной медицинской сети»',
     'adv': [fin_adv('продавца (владельцы «Национальной медицинской сети»)', 'Aspring Capital', ASPRING)]},
]


# Поправки к уже заведенным оболочкам: (ключ, поле, было, стало) — с assert на старое.
FIXUPS = [
    # Продавец в схеме — фонд (профиль Elbrus Capital привязан приемкой): текст роли
    # должен называть того же, кого профиль (docs/card_parties.md, «ссылку и текст правят вместе»).
    ('nms-medsi', 'seller', '«Национальная медицинская сеть»', 'Elbrus Capital'),
]


def card_id(key):
    return 'g' + hashlib.sha1(('advisor-site:' + key).encode('utf-8')).hexdigest()[:8]


def build(row):
    card = promote.to_card(row['draft'], card_id(row['key']))
    card['src'] = [list(s) for s in row['draft']['src']]      # подписи изданий — как записаны здесь
    for k, v in (row.get('set') or {}).items():
        card[k] = v
    if row['draft'].get('sum'):
        card['eco']['sum'] = row['draft']['sum']
    if row.get('finadv'):
        card['eco']['finadv'] = row['finadv']
    card['law']['adv'] = [list(r) for r in row.get('adv') or []]
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    return card


def main(write=False, only=None):
    pending = json.load(open(PENDING, encoding='utf-8'))      # читается прямо перед записью
    base = json.load(open(DATA, encoding='utf-8'))
    everything = pending['cards'] + base['deals']
    ids = {c['id'] for c in everything}
    added = 0
    for row in CARDS:
        if only and row['key'] not in only:
            continue
        cid = card_id(row['key'])
        if cid in ids:
            print('УЖЕ ЕСТЬ   %s %s' % (cid, row['key']))
            continue
        twins = [c['id'] for c in everything
                 if all(m.lower() in json.dumps(c, ensure_ascii=False).lower() for m in row['match'])]
        if twins:
            print('ОТКАЗ      %s: похожая карточка уже есть — %s' % (row['key'], ', '.join(twins)))
            continue
        card = build(row)
        print('НОВАЯ      %s %s: %s' % (cid, row['key'], card['title']))
        pending['cards'].append(card)
        added += 1
    fixed = 0
    by_id = {c['id']: c for c in pending['cards']}
    for key, field, old, new in FIXUPS:
        card = by_id.get(card_id(key))
        if only and key not in only or card is None or card.get(field) == new:
            continue
        assert card.get(field) == old, (key, field, card.get(field))
        card[field] = new
        for ev in (card.get('party_evidence') or {}).get(field, []):
            if ev.get('value') == old:
                ev['value'] = new
        print('ПОПРАВКА   %s %s: %r -> %r' % (card['id'], field, old, new))
        fixed += 1
    added += fixed
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    if added:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗаписано карточек и поправок: %d.' % added)
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    only = None
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    sys.exit(main(write='--write' in args, only=only))
