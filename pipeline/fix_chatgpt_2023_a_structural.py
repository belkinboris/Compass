# -*- coding: utf-8 -*-
"""Три структурные правки к карточкам той же партии, что и
`pipeline/ingest/fixes/batch_chatgpt_2023_a.py` — `review.py` их не берёт,
потому что это не перенос новой цитаты, а исправление уже имеющегося текста.

1. `g369b9b26` (ФСК/Sibelco): `eco.rationale` и `extra` несли ДОСЛОВНО
   одинаковый текст (класс дефекта из CLAUDE.md — «Один и тот же текст
   лежит в двух полях»), и оба заканчивались протёкшей служебной пометкой
   разбора «(ФСК (покупатель))» — это подпись роли стороны для внутреннего
   сопоставления, а не часть факта, и она была видна читателю. Пометка
   снята из обоих полей, `extra` (полный дубль без уникального текста)
   очищен — уникальной информации сверх `eco.rationale` в нём не было.

2. `c171fe137` (Магнит/KazanExpress): `sum`/`eco.sum` стояли пустыми, хотя
   источник прямо говорит «Ее сумма не раскрывается» — `review.py` не
   принимает для `sum` голый текст-заглушку (`sum_is_supported()` ждёт
   числовой формат), поэтому это правится напрямую, тем же приёмом, что
   `fill_frame_vpp_softline.py`.

3. `cb1991390` (национализация под управление «Росхима»): источник (AK&M)
   был в `src` под меткой «@dealsma (Telegram)» — тот же исторический
   дефект, что уже чинился для 836 ссылок (`relabel_dealsma_sources.py`),
   просто эта карточка прошла мимо того прогона. Подпись меняется на имя
   издания по домену (`pipeline/source_names.py`), сам адрес не трогается.

Запуск: python3 pipeline/fix_chatgpt_2023_a_structural.py
        python3 pipeline/fix_chatgpt_2023_a_structural.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_RATIONALE = (
    'Девелопер ФСК приобрел российские активы бельгийской компании '
    'Sibelco, включая Раменский горно-обогатительный комбинат, '
    'Неболчинское карьероуправление, завод по добыче глины в Воронежской '
    'области и торговый дом в Санкт-Петербурге. Сумма сделки официально '
    'не раскрыта. (ФСК (покупатель))')
NEW_RATIONALE = (
    'Девелопер ФСК приобрел российские активы бельгийской компании '
    'Sibelco, включая Раменский горно-обогатительный комбинат, '
    'Неболчинское карьероуправление, завод по добыче глины в Воронежской '
    'области и торговый дом в Санкт-Петербурге. Сумма сделки официально '
    'не раскрыта.')


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    changed = 0

    d1 = by_id['g369b9b26']
    assert d1['eco']['rationale'] == OLD_RATIONALE, 'g369b9b26: eco.rationale уже другое'
    assert d1.get('extra') == OLD_RATIONALE, 'g369b9b26: extra уже другое'
    print('ПРАВИМ  g369b9b26: eco.rationale (снимаю пометку роли), extra (снимаю дубль)')
    if write:
        d1['eco']['rationale'] = NEW_RATIONALE
        d1.pop('extra', None)
        changed += 1

    d2 = by_id['c171fe137']
    assert d2.get('sum') is None, 'c171fe137: sum уже задан'
    assert d2['eco'].get('sum') is None, 'c171fe137: eco.sum уже задан'
    print('ПРАВИМ  c171fe137: sum, eco.sum = «Не раскрыта» (источник: «Ее сумма не раскрывается»)')
    if write:
        d2['sum'] = 'Не раскрыта'
        d2['eco']['sum'] = 'Не раскрыта'
        changed += 1

    d3 = by_id['cb1991390']
    assert d3['src'] == [['@dealsma (Telegram)',
                           'https://www.akm.ru/news/pod_upravlenie_roskhima_'
                           'otoshli_chetyre_natsionalizirovannye_kompanii/']], \
        'cb1991390: src уже другое'
    print('ПРАВИМ  cb1991390: src — подпись «@dealsma (Telegram)» -> «АК&М»')
    if write:
        d3['src'] = [['АК&М',
                       'https://www.akm.ru/news/pod_upravlenie_roskhima_'
                       'otoshli_chetyre_natsionalizirovannye_kompanii/']]
        changed += 1

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: %d карточек.' % changed)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
