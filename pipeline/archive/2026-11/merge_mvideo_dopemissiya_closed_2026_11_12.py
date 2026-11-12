# -*- coding: utf-8 -*-
"""Карточка `gb5d8a18a` («ЦБ зарегистрировал допэмиссию акций «М.видео» по
закрытой подписке», собрана 19 августа 2026) описывала только РЕГИСТРАЦИЮ
допвыпуска Банком России. Сегодняшний приток принес исход: размещение
завершено, все 500 млн акций выкуплены по 49,9 ₽ — ПРАЙМ (1prime.ru,
12.11.2026), подтверждено Коммерсантом и smart-lab.ru (перепечатка
релиза компании). Ворота притока завели на ту же новость два отдельных
черновика (d51262230 и часть c той же темы в hold) — не опознали слабое
текстовое совпадение (общее слово «допэмиссия», разная формулировка
действия: «зарегистрировал» vs «завершила»), это новый этап известной
сделки, не новая сделка — та же логика, что `merge_azimut_yaroslavl_
result_2026_10_13.py`.

Почему не через таблицу FIXES (review.py): прежний этап (`prior_stage_
event`) и новое событие — записи в `events[]`, индексированный путь
review.py не читает (та же причина, что у events[N].note в других
карточках этого дня). Правка — прямым скриптом с assert на старое
значение каждого поля.

Источники (дочитаны по кэшу data/inbox/raw/2026-11-12-articles.jsonl):
  ПРАЙМ   https://1prime.ru/20261112/dopemissija-875162299.html
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gb5d8a18a'
PENDING_DUP_ID = 'd51262230'  # черновик в data/inbox/drafts — не в pending.json, трогать не нужно

PRIME = ['ПРАЙМ', 'https://1prime.ru/20261112/dopemissija-875162299.html']

OLD_TITLE = 'ЦБ зарегистрировал допэмиссию акций «М.видео» по закрытой подписке'
NEW_TITLE = '«М.видео» закрыла допэмиссию: акционеры выкупили весь выпуск за 24,95 млрд рублей'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_DATE = '2026-08-13'
NEW_DATE = '2026-11-12'
NEW_SUM = '24,95 млрд ₽'

OLD_VAL = '—'
NEW_VAL = ('Цену размещения совет директоров определил в 49,9 ₽ за акцию; при 500 млн размещенных '
           'бумаг это дает 24,95 млрд рублей.')


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
    assert card.get('sum') is None, card.get('sum')
    assert card['eco']['val'] == OLD_VAL
    assert not card.get('events')

    new_event = {
        'kind': 'closed', 'date': NEW_DATE, 'title': 'Сделка завершена',
        'note': ('Размещение закрыто: все 500 млн акций дополнительного выпуска выкуплены по 49,9 ₽ '
                  'за акцию — компания разместила 100% предусмотренного объема.'),
        'source': list(PRIME),
    }
    prior = enrich.prior_stage_event(card, new_event)

    print('ПРАВКА %s' % CARD_ID)
    print('  title  : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  status : %r -> %r' % (OLD_STATUS, NEW_STATUS))
    print('  date   : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  sum    : None -> %r' % NEW_SUM)
    print('  events : +%s' % (([prior] if prior else []) + ['closed %s' % NEW_DATE]))
    print('  src    : +%s' % [PRIME[0]])
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['status'] = NEW_STATUS
    card['date'] = NEW_DATE
    card['sum'] = NEW_SUM
    card['eco']['val'] = NEW_VAL
    card['eco']['sum'] = NEW_SUM

    events = []
    if prior:
        events.append(prior)
    events.append(new_event)
    card['events'] = events

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    if PRIME[1] not in existing_urls:
        card.setdefault('src', []).append(list(PRIME))

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
