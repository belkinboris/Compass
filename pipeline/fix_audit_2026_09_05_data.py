# -*- coding: utf-8 -*-
"""Данные по аудиту перед публичной бетой (5 сентября 2026), раздел 4.1 —
шесть правок одним скриптом, каждая с assert на исходное состояние.

1. ДУБЛЬ «ОТКРЫТИЯ». `gc3d735fc` («Продажа Банком России 100% акций ПАО Банк
   «ФК Открытие» группе ВТБ», 27.12.2022) и `gc2a1693a` («ВТБ приобрел банк
   «Открытие»», 22.12.2022) — одна покупка за 340 млрд ₽, и обе стояли в
   «Крупнейших сделках» аналитики. Остаётся `gc3d735fc`: у неё заполнены
   eco.share/val/target_fin/rationale/context, law.struct/appr и пять
   источников. Из дубля переносится то, чего у оставшейся нет: покупатель
   (профиль ВТБ — в оставшейся стояло «Не раскрыт» при ВТБ в заголовке),
   сопоставление цены с капиталом группы (550 млрд ₽), уход прежнего
   правления и ребрендинг (extra), четыре источника и подтверждение сторон
   (party_evidence). Дата закрытия — 27 декабря 2022 года (Коммерсантъ,
   doc/5748673, прочитан 5 сентября 2026: «ЦБ официально объявил 27 декабря,
   что больше не является акционером банка «Открытие», продав его ВТБ»);
   22 декабря у дубля — дата сообщения РБК об условиях сделки, отдельным
   событием не записывается: подписание договора датой ни один из
   источников карточки не называет. Событие «Сделка завершена» 27.12.2022 —
   в `events`. Адрес `#/deal/gc2a1693a` живёт через `merged`. Записи
   таблицы FIXES для дубля (batch_monthly_2026_08_23_r51.py) снимаются
   вместе с ним — правило из CLAUDE.md о слиянии дублей.

2. «ОЦЕНКА» В КОНСУЛЬТАНТАХ. `eco.finadv` оставшейся карточки нёс через «;»
   строку «оценка рыночной стоимости: 328–374 млрд руб.» — интерфейс делит
   поле по «;» и показывал её консультантом. Диапазоны оценок уходят в
   `eco.val`, в `finadv` остаются только фирмы и их роли.

3. `gd73fd825` (продажа бизнеса Яндекса консорциуму): продавец «Не раскрыт»
   при Yandex N.V. в заголовке — `seller` текстом.

4. `g46c6e23f` (Яндекс/Boxberry): дата стояла годом «2024», а сделка —
   апреля 2025 года. Интерфакс (business/1022482, прочитан 5 сентября 2026):
   публикация 24 апреля 2025 года, «"Яндекс" закрыл сделку по приобретению
   двух юрлиц службы доставки Boxberry», ранее — «16 апреля 2025 года …
   "Яндекс" покупает службу доставки Boxberry» (business/1021099). Дата
   сделки — 24 апреля 2025 года (день сообщения о закрытии; точная дата
   перехода долей не раскрыта — так и сказано в событии), события: объявление
   16.04.2025 и закрытие 24.04.2025.

5. `c51d0bb64` (партнёрство Wildberries и ВТБ): в `sum` стояло «около 500
   млрд ₽ (допэмиссия ВТБ)» — объём допэмиссии одного участника, а не цена
   партнёрства; карточка стояла второй в «Крупнейших сделках». Сумма — «Не
   раскрыта», факт о допэмиссии — в `eco.context`.

6. ПРОФИЛИ-ОПИСАНИЯ БЕЗ СДЕЛОК. «контрольный пакет Яндекса», «пул
   потенциальных инвесторов», «структура Газпромбанка», «торговые центры
   «Мега»» и ещё восемь — описательные обрывки, заведённые профилями компаний,
   ни одна карточка не ссылается на них ни одной ролью (проверено по
   buyer/seller_id/target/asset_id). Удаляются вместе с match_keys; два таких
   же обрывка с записями в реестре ФНС (g585a1aa5, gc19b6767) не тронуты —
   реестр ссылается на них, это отдельная чистка.

Запуск: python3 pipeline/fix_audit_2026_09_05_data.py
        python3 pipeline/fix_audit_2026_09_05_data.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KEEP, DROP = 'gc3d735fc', 'gc2a1693a'
VTB = 'gcafc31dc'
FINADV_OLD = ('АО «Деловые решения и технологии» (бывшая Deloitte) — независимый оценщик на стороне '
              'ЦБ (продавца); оценка рыночной стоимости: 328–374 млрд руб.; PwC — ранее проводила '
              'оценку в рамках подготовки к IPO (449–535 млрд руб., включая активы, впоследствии '
              'переданные банку «Траст»)')
FINADV_NEW = ('АО «Деловые решения и технологии» (бывшая Deloitte) — независимый оценщик на стороне '
              'ЦБ (продавца); PwC — оценка при подготовке к IPO (ранее)')
VAL_ADD = (' Независимая оценка «Деловых решений и технологий»: 328–374 млрд ₽; более ранняя оценка '
           'PwC при подготовке к IPO — 449–535 млрд ₽, включая активы, позже переданные банку «Траст».')
CONTEXT_ADD_550 = ' Капитал группы «Открытие» оценивался в 550 млрд ₽, цена покупки — 340 млрд ₽.'
CLOSED_EVENT = {
    'kind': 'closed', 'date': '2022-12-27', 'title': 'Сделка завершена',
    'note': 'ЦБ объявил 27 декабря 2022 года, что больше не является акционером «Открытия»; '
            'ВТБ полностью оплатил акции.',
}

ORPHANS = {
    'g87e3ff99': 'контрольный пакет Яндекса',
    'gc3d94eb3': 'пул потенциальных инвесторов (не названы конкретно)',
    'ged687237': 'менеджмент во главе с Максимом Орловским, Владимиром Куровым и Игорем Даниленко',
    'gc634d92f': 'российские партнеры во главе с Захаром Смушкиным',
    'gc14f4478': 'группа российских топ-менеджеров во главе с Александром Торбаховым',
    'g93353b9c': 'структура Газпромбанка',
    'gc0956e6b': 'российский бизнес «Ренессанс капитала»',
    'gfcd0ed71': 'торговые центры «Мега»',
    'gac3876af': "гипермаркеты «О'кей»",
    'gab2b5053': 'три российских завода по производству упаковки Mondi',
    'g05d8286a': 'отель Swissotel Resort Сочи Камелия',
    'ge036c235': 'ПАО ЮГК + доля в «МелТЭК» и сельхозпредприятия',
}

BOXBERRY = 'g46c6e23f'
BOXBERRY_EVENTS = [
    {'kind': 'signed', 'date': '2025-04-16', 'title': 'Объявлено о сделке',
     'note': '«Яндекс» сообщил о покупке службы доставки Boxberry (Интерфакс, 16 апреля 2025 года).'},
    {'kind': 'closed', 'date': '2025-04-24', 'title': 'Сделка завершена',
     'note': 'Интерфакс 24 апреля 2025 года сообщил, что «Яндекс» закрыл сделку по приобретению двух '
             'юрлиц Boxberry; точная дата перехода долей не раскрыта.'},
]
BOXBERRY_SRC = ['Интерфакс (16.04.2025)', 'https://www.interfax.ru/business/1021099']

WB = 'c51d0bb64'
WB_SUM_OLD = 'около 500 млрд ₽ (допэмиссия ВТБ)'
WB_VAL_OLD = 'Около 500 млрд ₽ (допэмиссия ВТБ)'
WB_CONTEXT_ADD = (' Под вход в WB Банк ВТБ проводит допэмиссию около 500 млрд ₽ — это объём размещения '
                  'акций самого банка, а не цена партнёрства; стоимость доли не раскрыта.')

YANDEX_SALE = 'gd73fd825'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deals = data['deals']
    by_id = {d['id']: d for d in deals}
    co, keys = data['companies'], data['match_keys']

    # 1. дубль «Открытия»
    keep, drop = by_id[KEEP], by_id[DROP]
    assert keep.get('buyer') is None and not keep.get('buyer_name'), keep.get('buyer')
    assert drop.get('buyer') == VTB and co[VTB]['name'] == 'ВТБ'
    assert keep['date'] == '2022-12-27' and drop['date'] == '2022-12-22'
    assert not keep.get('events'), keep.get('events')
    assert '550' not in (keep['eco'].get('context') or '') and '550' in drop['eco']['context']
    assert 'Задорнов' not in (keep.get('extra') or '') and 'Задорнов' in drop['extra']
    keep_urls = {s[1] for s in keep.get('src') or []}
    src_add = [s for s in drop.get('src') or [] if s[1] not in keep_urls]
    print('1. %s <- %s: buyer -> ВТБ; +context(550); +extra; +%d src; +event closed 27.12.2022'
          % (KEEP, DROP, len(src_add)))

    # 2. оценка в консультантах
    assert keep['eco']['finadv'] == FINADV_OLD, keep['eco']['finadv']
    assert '328' not in keep['eco']['val']
    print('2. finadv ->', FINADV_NEW)

    # 3. продавец Яндекса
    ys = by_id[YANDEX_SALE]
    assert ys.get('seller') is None and ys.get('seller_id') is None
    print('3. gd73fd825 seller -> Yandex N.V.')

    # 4. Boxberry
    bx = by_id[BOXBERRY]
    assert bx['date'] == '2024' and not bx.get('events'), (bx['date'], bx.get('events'))
    assert BOXBERRY_SRC[1] not in {s[1] for s in bx['src']}
    print('4. g46c6e23f date 2024 -> 2025-04-24; events: 16.04 объявлено, 24.04 закрыта; +src 1021099')

    # 5. WB/ВТБ
    wb = by_id[WB]
    assert wb['sum'] == WB_SUM_OLD and wb['eco']['sum'] == 'около 500 млрд ₽' and wb['eco']['val'] == WB_VAL_OLD, (wb['sum'], wb['eco']['sum'], wb['eco']['val'])
    assert 'допэмиссию около 500' not in wb['eco']['context']
    print('5. c51d0bb64 sum/eco.sum -> Не раскрыта; eco.val -> —; context += допэмиссия')

    # 6. профили-обрывки
    party = set()
    for d in deals:
        for k in ('buyer', 'seller_id', 'target', 'asset_id'):
            if d.get(k):
                party.add(d[k])
    for cid, name in ORPHANS.items():
        assert co[cid]['name'] == name, (cid, co[cid]['name'])
        assert cid not in party, cid
        assert not any((c.get('holding') or {}).get('id') == cid for c in co.values()), cid
    print('6. удаляются %d профилей-обрывков' % len(ORPHANS))

    if not write:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')
        return
    keep['buyer'] = VTB
    keep['eco']['context'] = (keep['eco'].get('context') or '').rstrip() + CONTEXT_ADD_550
    keep['extra'] = (keep.get('extra') or '').rstrip() + ' ' + drop['extra'].strip()
    keep['src'] = (keep.get('src') or []) + src_add
    keep['events'] = [CLOSED_EVENT]
    if drop.get('party_evidence'):
        keep['party_evidence'] = drop['party_evidence']
    keep['eco']['finadv'] = FINADV_NEW
    keep['eco']['val'] = keep['eco']['val'].rstrip() + VAL_ADD
    deals[:] = [d for d in deals if d['id'] != DROP]
    data.setdefault('merged', {})[DROP] = KEEP
    ys['seller'] = 'Yandex N.V.'
    bx['date'] = '2025-04-24'
    bx['events'] = BOXBERRY_EVENTS
    bx['src'].append(BOXBERRY_SRC)
    wb['sum'] = 'Не раскрыта'
    wb['eco']['sum'] = 'Не раскрыта'
    wb['eco']['val'] = '—'
    wb['eco']['context'] = wb['eco']['context'].rstrip() + WB_CONTEXT_ADD
    for cid in ORPHANS:
        del co[cid]
        keys.pop(cid, None)
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('\nЗаписано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
