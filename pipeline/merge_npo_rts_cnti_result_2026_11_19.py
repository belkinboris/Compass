# -*- coding: utf-8 -*-
"""Карточка `g85e07f6d» («Дом.РФ» выставил на торги треть здания бывшего
ЦНТИ в Челябинске», собрана 8 октября 2026) описывала только ОБЪЯВЛЕНИЕ
аукциона. Сегодняшний приток принес исход: заявку подала только одна
компания — ООО НПО «РТС» (ИНН 7453099174, ОГРН 1037403874144), аукционная
комиссия признала ее единственным участником и заключила договор по
начальной цене, 59,8 млн ₽ (74.ru, 19.11.2026, итоговый протокол на
«ГИС. Торги»).

Ворота притока завели на эту же новость ОТДЕЛЬНУЮ карточку (`g9937f3c4`,
автоматический парсер перепутал заголовок статьи целиком: `buyer_name`
стояло «Часть известного здания в центре Челябинска», `asset` — «производитель
радионавигационного оборудования. Кто за ним стоит») — это этап уже известной
сделки (тот же лот: 2488 кв. м, улица Труда 157, старт 59,8 млн ₽, продавец
«Дом.РФ»), не новая сделка. `g9937f3c4` снимается из очереди предпросмотра
отдельно, `pipeline/ingest/drop_pending.py` (он же оповестит консоль и
запомнит адрес источника в `discarded_urls`).

Почему не через таблицу FIXES (review.py): проза ниже — пересказ, а не
дословная цитата источника, и записывается событие `events[]`, которое
review.py не читает (та же причина, что в `merge_azimut_yaroslavl_result_
2026_10_13.py` и `merge_mvideo_dopemissiya_closed_2026_11_12.py`). Правка —
прямым скриптом с assert на старое значение каждого поля.

Покупатель — новый профиль компании (в базе еще не было ни одной карточки
с НПО «РТС»). История участников ЕГРЮЛ (datanewton.ru/api/v2/history,
ОГРН 1037403874144) подтверждает, что «кто за ним стоит» из заголовка
источника — Александр Викторович Долматов: его доля стабильна с
2021-07-02 (68%), остальные — Виталий Муниров (11%), Анастасия Мелихова
(10%), Ринат Салихов (снижена с 11% до 5,5% 17.11.2026, в тот же день
вошло ООО «РТС-Технопарк» с 5,5%). Иностранных или подсанкционных лиц в
истории нет — `accepted_notes.checked.registry_owners` карточки.

Продавец у карточки уже стоял верно («Дом.РФ», gb2b066c3) — не трогаем.

Источник: 74.ru, https://74.ru/text/business/2026/11/19/76777277/
(дочитан целиком, текст на диске — data/inbox/raw/2026-11-19-articles.jsonl).

Запуск:
    python3 pipeline/merge_npo_rts_cnti_result_2026_11_19.py            # сухой прогон
    python3 pipeline/merge_npo_rts_cnti_result_2026_11_19.py --write    # применить
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g85e07f6d'
BUYER_COMPANY_ID = 'g2aef124c'  # новый профиль, НПО «РТС»

SRC = ['74.RU', 'https://74.ru/text/business/2026/11/19/76777277/']

OLD_TITLE = '«Дом.РФ» выставил на торги треть здания бывшего ЦНТИ в Челябинске'
NEW_TITLE = 'НПО «РТС» купило на торгах треть здания бывшего ЦНТИ в Челябинске'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_DATE = '2026-10-08'
NEW_DATE = '2026-11-19'
NEW_SUM = '59,8 млн ₽'

OLD_ASSET = 'треть помещений (2488 кв. м) в здании бывшего ЦНТИ в Челябинске'
NEW_ASSET = 'треть здания бывшего ЦНТИ в Челябинске — третий этаж (2488 кв. м)'

OLD_VAL = ('Старт торгов — 59,8 млн ₽; задаток для участников — 10% от этой суммы, шаг аукциона — 599 тыс. ₽.')
NEW_VAL = ('Заявку на аукцион подала только одна компания — ООО НПО «РТС», и комиссия признала ее единственным '
           'участником; по правилам такой процедуры договор заключается по начальной цене предмета аукциона — '
           'этаж здания ушел за 59,8 млн ₽, без снижения или повышения цены торгами.')

OLD_CONTEXT = ('Здесь много лет работал Центр научно-технической информации (ЦНТИ), ликвидированный в прошлом году; '
               'большая часть здания отошла Судебному департаменту Челябинской области, остальное — «Дом.РФ». '
               'Последние три десятилетия помещения занимал рынок мебели, ковров и семян — арендаторы съехали в '
               'конце января, и с начала года там идет ремонт.')
NEW_CONTEXT = ('Дом на Труда, 157 построен в 1972 году (8187 кв. м), и с 1974-го там работал ЦНТИ — в 2025 году '
               'организацию ликвидировали, а здание поделили между судебной системой региона и федеральным '
               'агентом «Дом.РФ». На долю «Дом.РФ» пришелся третий этаж, 2488 кв. м, — его и купило НПО «РТС». '
               'Итоги торгов «Дом.РФ» опубликовал на портале «ГИС. Торги» 19 ноября 2026 года.')

OLD_STRUCT = 'Торги назначены на 20 ноября 2026 года; прием заявок стартовал 8 октября.'
NEW_STRUCT = ('На аукцион заявку подало только ООО НПО «РТС» — конкурентных торгов не проводилось: комиссия '
              'признала компанию единственным участником и заключила с ней договор по начальной цене. Прием '
              'заявок стартовал 8 октября 2026 года, торги были назначены на 20 ноября; итог определился на '
              'стадии рассмотрения заявок, протокол подведения итогов датирован 19 ноября.')

NEW_COMPANY = {
    'name': 'НПО «РТС»',
    'ind': 'Машиностроение',
    'desc': ('Российский разработчик и производитель систем радионавигации, посадки и управления воздушным '
             'движением; решения применяются в аэропортах России, стран СНГ, Азии и Латинской Америки, среди '
             'заказчиков — Росавиация, Минобороны РФ и Роскосмос. Зарегистрировано в Челябинске в 2003 году. '
             'Основной владелец — Александр Долматов.'),
    'kpi': [],
    'legal_short': 'ООО НПО «РТС»',
    'inn': '7453099174',
    'ogrn': '1037403874144',
}


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
    assert card.get('buyer') is None, card.get('buyer')
    assert card.get('asset') == OLD_ASSET, card.get('asset')
    assert card['eco']['val'] == OLD_VAL, card['eco']['val']
    assert card['eco']['context'] == OLD_CONTEXT, card['eco']['context']
    assert card['law']['struct'] == OLD_STRUCT, card['law']['struct']
    assert not card.get('events')
    assert BUYER_COMPANY_ID not in data['companies']

    new_event = {
        'kind': 'closed', 'date': NEW_DATE, 'title': 'Сделка завершена',
        'note': ('Единственную заявку на аукцион подало ООО НПО «РТС» — компания получила этаж бывшего здания '
                  'ЦНТИ по стартовой отметке торгов, 59,8 млн ₽.'),
        'source': list(SRC),
    }
    prior = enrich.prior_stage_event(card, new_event)

    print('ПРАВКА %s' % CARD_ID)
    print('  title  : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  status : %r -> %r' % (OLD_STATUS, NEW_STATUS))
    print('  date   : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  sum    : None -> %r' % NEW_SUM)
    print('  buyer  : None -> %r (НПО «РТС», новый профиль)' % BUYER_COMPANY_ID)
    print('  asset  : %r -> %r' % (OLD_ASSET, NEW_ASSET))
    print('  events : +%s' % (([prior] if prior else []) + ['closed %s' % NEW_DATE]))
    print('  src    : +%s' % [SRC[0]])
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['status'] = NEW_STATUS
    card['date'] = NEW_DATE
    card['sum'] = NEW_SUM
    card['buyer'] = BUYER_COMPANY_ID
    card['asset'] = NEW_ASSET
    card['eco']['sum'] = NEW_SUM
    card['eco']['val'] = NEW_VAL
    card['eco']['context'] = NEW_CONTEXT
    card['law']['struct'] = NEW_STRUCT

    events = []
    if prior:
        events.append(prior)
    events.append(new_event)
    card['events'] = events

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    if SRC[1] not in existing_urls:
        card.setdefault('src', []).append(list(SRC))

    pe = card.setdefault('party_evidence', {})
    pe['buyer'] = [{'value': 'НПО «РТС»', 'field': 'buyer',
                    'method': 'explicit_official_protocol', 'url': SRC[1]}]

    notes = card.setdefault('accepted_notes', {})
    checked = notes.setdefault('checked', {})
    checked['registry_owners'] = ('история участников ЕГРЮЛ (datanewton, ОГРН 1037403874144): основной '
                                   'владелец — Александр Долматов (68% с 2021-07-02), далее Виталий Муниров '
                                   '(11%), Анастасия Мелихова (10%), Ринат Салихов (снижен с 11% до 5,5% '
                                   '17.11.2026, в тот же день вошло ООО «РТС-Технопарк» с 5,5%); иностранных '
                                   'или подсанкционных лиц в истории нет')

    data['companies'][BUYER_COMPANY_ID] = NEW_COMPANY

    # Карточку перечитываем прямо перед записью — чужой пуш не затирается.
    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card.get('title') == OLD_TITLE, 'карточку кто-то уже поправил — перечитайте'
    assert BUYER_COMPANY_ID not in fresh['companies'], 'профиль кто-то уже завел — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card
    fresh['companies'][BUYER_COMPANY_ID] = NEW_COMPANY

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено. Профиль %s (НПО «РТС») добавлен.' % BUYER_COMPANY_ID)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
