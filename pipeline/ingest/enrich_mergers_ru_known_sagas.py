#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пять известных сюжетов, которые mergers.ru подтвердил и продвинул дальше.

ПОЧЕМУ ВРУЧНУЮ, А НЕ `enrich.py`. `match.py` не связал эти новости с уже
существующими карточками (слабый сигнал — заголовки описывают разные грани
одной сделки разными словами), поэтому они попали в «новое» вместо «дополнить».
Проверено при сверке бэкфила 31 июля: ЮГК/БТС-Мост, Галс-Девелопмент,
Медскан/Русатом, Домодедово/Перспектива, «Центр ЭКО»/Р-Фарм — уже есть в базе.

ЧТО ДОПИСЫВАЕТСЯ, А ЧТО НЕТ. Только `events` (список этапов с источником) —
это чистое добавление, не трогающее уже заполненные поля. Там, где у
mergers.ru и у карточки разные суммы (ЮГК: 140 млрд ₽ в базе против 93,16 или
81,01 млрд ₽ у источника; Галс-Девелопмент: 112 млрд ₽ против 100 млрд ₽),
поле `sum` НЕ переписывается — расхождение суммы решает человек, а не скрипт
(тот же принцип, что в `enrich.py`: заполненное поле не заменяется догадкой).

Запуск:
    python3 pipeline/ingest/enrich_mergers_ru_known_sagas.py            # сухой прогон
    python3 pipeline/ingest/enrich_mergers_ru_known_sagas.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

# deal_id -> (ожидаемый title дословно, список новых событий)
ENRICH = {
    'gdcc03f9d': (
        'Продажа государственного пакета 67,25% акций ПАО «Южуралзолото Группа Компаний» (ЮГК) — АО «БТС-Мост Холдинг»',
        [
            dict(kind='negotiations', date='2026-06-11', title='Объявлен голландский аукцион',
                 note='Росимущество объявило голландский аукцион по продаже ЮГК со стартовой ценой 81,01 млрд ₽, итоги — 19 июня.',
                 source=['mergers.ru', 'https://mergers.ru/news/Rosimuschestvo-provedet-gollandskij-aukcion-po-prodazhe-YuGK-i-obyavit-itogi-19-iyunya-87063']),
            dict(kind='closed', date='2026-07-06', title='Оплачен контрольный пакет',
                 note='АО «БТС-Мост Холдинг» оплатило Росимуществу стоимость 67,2% акций ЮГК (93,16 млрд ₽ по данным mergers.ru) и долей связанных структур.',
                 source=['mergers.ru', 'https://mergers.ru/news/BTS-Most-Holding-oplatil-kontrolnyj-paket-akcij-YuGK-87151']),
            dict(kind='closed', date='2026-07-17', title='Оформлено владение 67,2489% акций',
                 note='АО «БТС-Мост Холдинг» стало собственником 67,2489% акций ПАО «Южуралзолото Группа Компаний».',
                 source=['mergers.ru', 'https://mergers.ru/news/BTS-Most-Holding-stal-vladelcem-672-YuGK-87227']),
        ]),
    'g92476095': (
        'ВТБ продал «Галс-Девелопмент» группе инвесторов',
        [
            dict(kind='closed', date='2026-07-28', title='Уточнён периметр сделки',
                 note='Гостиница «Holiday Inn Сокольники» вошла в периметр сделки по продаже активов «Галс-Девелопмента» — банк реализовал все свои гостиничные объекты. Стоимость самой гостиницы оценивается отдельно в 8–10 млрд ₽ (по оценке рынка).',
                 source=['mergers.ru', 'https://mergers.ru/news/VTB-prodal-moskovskij-otel-Holiday-Inn-v-Sokolnikah-87279']),
        ]),
    'g68a112bd': (
        'Русатом Хэлскеа увеличил долю в Медскане до 50%',
        [
            dict(kind='negotiations', date='2026-06-03', title='Доля снижена с 50% до 45% перед IPO',
                 note='«Росатом» снизил долю участия в «Медскане» с 50% до 45% в презентации для инвесторов перед плановым IPO в сентябре 2026 года.',
                 source=['mergers.ru', 'https://mergers.ru/news/U-Medskana-poyavilsya-novyj-investor-87023']),
        ]),
    'gf13fba9e': (
        'ООО «Перспектива» (дочка «Шереметьево») подала заявку на участие в аукционе по продаже «Домодедово»',
        [
            dict(kind='closed', date='2026-07-21', title='Перспектива выкупила Домодедово, Внуково покупает долю в ней',
                 note='«Перспектива» выкупила у Росимущества группу «Домодедово» за 66 млрд ₽. Аэропорт Внуково намерен выкупить 25,01% долей «Перспективы» за 16,5 млрд ₽ и стать совладельцем «Домодедово».',
                 source=['mergers.ru', 'https://mergers.ru/news/Ajeroport-Vnukovo-stanet-sovladelcem-Domodedovo-87247']),
        ]),
    'g7f396659': (
        'Структура Р-фарма купила 49,9% сети клиник Центр ЭКО',
        [
            dict(kind='closed', date='2026-06-03', title='Выкуплены оставшиеся 50,1% — доля доведена до 100%',
                 note='АО «Эко Холдинг» (структура «Р-Фарма») выкупила оставшиеся 50,1% акций группы «Центр ЭКО» у Сергея Лебедева; сделка закрыта 29 мая 2026 года.',
                 source=['mergers.ru', 'https://mergers.ru/news/Struktura-R-Farm-vykupila-set-klinik-Centr-JeKO-87027']),
        ]),
}


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for deal_id, (expected_title, events) in ENRICH.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert deal['title'] == expected_title, '%s: заголовок не совпадает дословно: %r' % (deal_id, deal['title'])
        existing_kinds_dates = {(e.get('kind'), e.get('date')) for e in (deal.get('events') or [])}
        new_events = [e for e in events if (e['kind'], e['date']) not in existing_kinds_dates]
        if not new_events:
            continue
        plan.append((deal_id, new_events))

    print('Карточек к дополнению этапами: %d' % len(plan))
    for deal_id, events in plan:
        print('  %s: +%d этап(ов)' % (deal_id, len(events)))
        for e in events:
            print('    %s %s — %s' % (e['date'], e['kind'], e['title']))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, events in plan:
        deal = by_id[deal_id]
        deal.setdefault('events', [])
        deal['events'].extend(events)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
