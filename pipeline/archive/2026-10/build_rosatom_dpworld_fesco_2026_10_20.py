# -*- coding: utf-8 -*-
"""Новая карточка: «Росатом» и DP World создают совместное предприятие на
базе FESCO (по просьбе партнера, источник — Интерфакс 16 октября 2026).

ПОЧЕМУ РУКАМИ. Партнер прислал заметку Интерфакса «„Росатом“ готовит сделку
с арабским DP World» (16.10.2026) — отдельной карточки о СП 2025–2026 годов
в базе нет. Рядом лежат две карточки о том же активе, но о других сделках:
`gf1f8c278` (2019, DP World и РФПИ — 49% Fesco, «Не состоялась») и
`c6b59f911` (передача акций ДВМП от государства «Росатому»). Их не трогаем.
Карточка собирается так же, как кнопкой «в работу»: черновик →
`promote.to_card` → `pending.json` с `pending_since`; дальше обычный путь
(write_card.py, review.py --mark-read, accept_card.py, второе чтение,
send_drafts.py).

ЧТО ИЗВЕСТНО И ЧЕГО НЕТ (по статьям):
  * тип — «Создание СП» (docs/card_status_dates.md): участники — сами
    учредители, «Росатом» (`rosatom`) и DP World (`gd45e6602`); FESCO
    (`g2d0dac7a`) — то, что вносится в СП, поэтому профилем предмета
    (`asset_id`), а не стороной.
  * доли: «Росатом» — 51%, DP World — 49% за денежный вклад; в СП (ООО
    «Глобальная логистика», зарегистрировано 24 декабря 2025) вносится пакет
    ДВМП — 92,5% по Известиям и Ъ, 92,4% по словам представителя «Росатома»
    (Reuters).
  * статус — «Согласование получено»: ФАС согласовала в апреле 2026,
    правкомиссия — о решении стало известно 18 августа 2026 (Росатом
    подтвердил Reuters). Сделка не закрыта: 7–8 октября «Росатом» сказал Ъ,
    что юридическая документация еще согласуется и сделку состоявшейся он
    не объявляет; 16 октября Лихачев: «Готовим сейчас вместе с ними сделку».
  * дата — год: день заседания правкомиссии не назван, 18 августа — день,
    когда о решении сообщили (docs/card_status_dates.md, «Нет дня — только
    год»).
  * сумма не раскрыта: вклад DP World — по рыночной стоимости FESCO от
    независимого оценщика; 145–150 млрд ₽ (СберCIB) и ~160 млрд ₽ (Bonus
    Fabula) — оценки аналитиков, в eco.val, не в sum.
  * консультанты в источниках не названы.

id — константой (docs/intake_run.md, «id ручной сборки — константой»):
повторный запуск не заводит второй карточки.

Запуск:
    python3 pipeline/build_rosatom_dpworld_fesco_2026_10_20.py            # сухой прогон
    python3 pipeline/build_rosatom_dpworld_fesco_2026_10_20.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g7d3f5a20'
ROSATOM, DP_WORLD, FESCO = 'rosatom', 'gd45e6602', 'g2d0dac7a'
RELATED = ('gf1f8c278', 'c6b59f911')   # другие сделки о том же активе — не трогать

INTERFAX = ['Интерфакс', 'https://www.interfax.ru/business/1123174']
IZ_NEWS = ['Известия', 'https://iz.ru/2073991/2026-04-07/fas-razreshila-dp-world-kupit-doliu-v-fesco']
IZ_LONG = ['Известия', 'https://iz.ru/2073773/denis-kuznetcov/sozdaniyu-mirovogo-logisticheskogo-operatora-s-uchastiem-rf-dan-zelenyj-svet']
TMT_MAR = ['The Moscow Times', 'https://ru.themoscowtimes.com/2026/03/27/rosatom-i-dp-world-sozdayut-sovmestnogo-logisticheskogo-operatora-a191029']
TMT_AUG = ['The Moscow Times', 'https://ru.themoscowtimes.com/2026/08/18/pravitelstvo-rf-odobrilo-sozdanie-logisticheskogo-sp-rosatoma-i-dp-world-a203731']
KOMMERSANT = ['Коммерсантъ', 'https://kommersant.ru/doc/9008037']
ATOMIC = ['atomic-energy.ru', 'https://www.atomic-energy.ru/news/2026/08/20/167918']

DRAFT = {
    'date': '2026',
    'title': '«Росатом» и DP World создают совместное предприятие на базе FESCO',
    'ind': 'Транспорт и логистика',
    'type': 'Создание СП',
    'status': 'Согласование получено',
    'sum': 'Не раскрыта',
    'src': [INTERFAX, TMT_MAR, IZ_NEWS, IZ_LONG, TMT_AUG, ATOMIC, KOMMERSANT],
    'asset': 'ООО «Глобальная логистика» — совместное предприятие, в которое «Росатом» вносит пакет ДВМП (FESCO)',
    'events': [
        {
            'kind': 'announced',
            'date': '2026-03-27',
            'title': '«Росатом» и DP World договорились о создании СП',
            'note': '«Росатом» сообщил, что получит 51% совместного оператора, а DP World — 49%: '
                    'госкорпорация вносит свой пакет ДВМП, DP World — деньги по рыночной '
                    'стоимости FESCO, определенной независимым оценщиком.',
            'source': TMT_MAR,
        },
        {
            'kind': 'approval',
            'date': '2026',
            'title': 'ФАС одобрила сделку',
            'note': 'О согласовании ФАС стало известно в апреле 2026 года; день решения не назван.',
            'source': IZ_NEWS,
        },
        {
            'kind': 'approval',
            'date': '2026',
            'title': 'Правкомиссия одобрила сделку',
            'note': 'О решении правительственной комиссии по иностранным инвестициям стало известно '
                    '18 августа 2026 года, «Росатом» его подтвердил; день заседания не назван.',
            'source': TMT_AUG,
        },
    ],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in pending['cards']) or any(d['id'] == CARD_ID for d in promoted['deals']):
        print('УЖЕ ЕСТЬ: %s — повторно не собираю' % CARD_ID)
        return 0
    comps = promoted['companies']
    assert comps[ROSATOM]['name'] == 'Росатом', comps[ROSATOM]['name']
    assert comps[DP_WORLD]['name'] == 'DP World', comps[DP_WORLD]['name']
    assert comps[FESCO]['name'] == 'Fesco', comps[FESCO]['name']
    related = {d['id']: d for d in promoted['deals'] if d['id'] in RELATED}
    assert set(related) == set(RELATED), 'соседние карточки FESCO пропали: %s' % set(related)
    for c in pending['cards']:
        if 'DP World' in (c.get('title') or '') or 'FESCO' in (c.get('title') or ''):
            print('ОТКАЗ: похожая карточка уже в очереди: %s %s' % (c['id'], c['title']))
            return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['eco']['sum'] = 'Не раскрыта'
    card['buyer'] = ROSATOM
    card['target'] = DP_WORLD
    card['asset_id'] = FESCO
    card['kind'] = 'jv'
    card.pop('party_evidence', None)   # стороны — профили, не текст из заголовка
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('УЖЕ ЕСТЬ в pending.json — не пишу')
        return 0
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
