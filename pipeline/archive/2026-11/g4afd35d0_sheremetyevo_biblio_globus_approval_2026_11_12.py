# -*- coding: utf-8 -*-
"""Карточка `g4afd35d0` («Структуры Wildberries могут купить у Шереметьево
75% «Библио-Глобуса»», 21 октября 2026) несла только начало переговоров —
покупатель и сумма не были названы. Прошлый прогон (17:20) читал статью
Фонтанки про это же дело и не смог решить, одобрение это или пересказ
старой новости (отмечено `unclear`, ушло в консоль). Сегодняшний прогон
(19:21) принес независимое подтверждение: Rusbase (rb.ru) со ссылкой на
РБК — совет директоров Шереметьево одобрил продажу, названы покупатель
(Wildberries & Russ) и сумма (~40 млрд ₽), механизм отложенного платежа
и срок закрытия (до 31 декабря 2026). `enrich.py` сам нашел совпадение
(дописать: 2) — это та же карточка, не дубль.

Почему не через таблицу FIXES (review.py): прежний этап (`prior_stage_
event`) и новое событие — записи в `events[]`, индексированный путь,
который review.py не читает (та же причина, что у events[N] в других
карточках этого дня).

Источник (дочитан по кэшу data/inbox/raw/2026-11-12-articles.jsonl):
  Rusbase (rb.ru)  https://rb.ru/news/wildberries-kupit-75-biblio-globusa-za-40-mlrd-rublej-sovet-direktorov-sheremetevo-odobril-sdelku/
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g4afd35d0'
RUSBASE = ['Rusbase', 'https://rb.ru/news/wildberries-kupit-75-biblio-globusa-za-40-mlrd-rublej-sovet-direktorov-sheremetevo-odobril-sdelku/']

OLD_TITLE = 'Структуры Wildberries могут купить у Шереметьево 75% «Библио-Глобуса»'
NEW_TITLE = 'Wildberries покупает 75% «Библио-Глобуса» за 40 млрд рублей'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Согласование получено'
OLD_DATE = '2026-10-21'
NEW_DATE = '2026-11-12'
NEW_SUM = '40 млрд ₽'

OLD_BUYER_NAME = None
NEW_BUYER_NAME = 'Wildberries & Russ'

OLD_TERMS = '—'
NEW_TERMS = ('Предполагается отложенный платеж: покупатель будет расплачиваться за акции из будущей прибыли '
             'туроператора. Стороны рассчитывают закрыть сделку до 31 декабря 2026 года.')

OLD_CONTEXT = ('В августе аэропорт Шереметьево исключили из перечня стратегических предприятий. По словам РБК, '
               'среди возможных покупателей — структуры, связанные с Wildberries & Russ (RWB), и претендент не один. '
               'Официально покупатель не назван, аэропорт от комментариев отказался. Деньги от продажи, по словам '
               'РБК, могут пойти на выкуп блокирующего пакета акций самого аэропорта в рамках его приватизации. '
               'Вице-президент Альянса туристических агентств России Алексан Мкртчян публично усомнился в самой '
               'сделке: об этом пишет только одно издание, а в туротрасли эту новость не повторяет никто.')
NEW_CONTEXT = (OLD_CONTEXT + ' Переговоры начались летом 2026 года: сначала Wildberries & Russ предлагала '
               'взять туроператора в управление на несколько месяцев, но Шереметьево на такой вариант не '
               'согласился. В RWB от комментариев по сделке отказались.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card.get('title') == OLD_TITLE, card.get('title')
    assert card.get('status') == OLD_STATUS, card.get('status')
    assert card.get('date') == OLD_DATE, card.get('date')
    assert card.get('buyer_name') == OLD_BUYER_NAME, card.get('buyer_name')
    assert card['law']['terms'] == OLD_TERMS
    assert card['eco']['context'] == OLD_CONTEXT
    assert not card.get('events')

    new_event = {
        'kind': 'approval', 'date': NEW_DATE, 'title': 'Согласование получено',
        'note': ('Совет директоров аэропорта Шереметьево одобрил продажу 75% туроператора «Библио-Глобус» '
                  'структурам Wildberries&Russ, сообщает РБК. Стоимость сделки оценивается примерно в 40 млрд '
                  'рублей.'),
        'source': list(RUSBASE),
    }
    prior = enrich.prior_stage_event(card, new_event)

    print('ПРАВКА %s' % CARD_ID)
    print('  title      : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  status     : %r -> %r' % (OLD_STATUS, NEW_STATUS))
    print('  date       : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  sum        : None -> %r' % NEW_SUM)
    print('  buyer_name : None -> %r' % NEW_BUYER_NAME)
    print('  events     : +%s' % (([prior] if prior else []) + ['approval %s' % NEW_DATE]))
    print('  src        : +%s' % [RUSBASE[0]])
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['status'] = NEW_STATUS
    card['date'] = NEW_DATE
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    card['buyer_name'] = NEW_BUYER_NAME
    card['law']['terms'] = NEW_TERMS
    card['eco']['context'] = NEW_CONTEXT

    events = []
    if prior:
        events.append(prior)
    events.append(new_event)
    card['events'] = events

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    if RUSBASE[1] not in existing_urls:
        card.setdefault('src', []).append(list(RUSBASE))

    # Карточку перечитываем прямо перед записью — чужой пуш не затирается.
    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card.get('title') == OLD_TITLE, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
