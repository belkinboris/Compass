# -*- coding: utf-8 -*-
"""Качество 24 октября 2026: две записи `pipeline/facts_discrepancies.json`
несли дату карточки с другим ГОДОМ, чем дважды независимо подтверждённая
дата закрытия (`facts.date`, basis=verified, model×2) — `review.py` такую
правку не принимает («год не совпадает: уточнять день можно, переносить
год — нет», `date_is_supported()`), и это намеренно: смена года — отдельное
утверждение, не перенос. Поэтому, как и `fix_placeholder_dates.py`, правка
прямым скриптом с `assert` на старое значение и явной цитатой уже
подтверждённого факта.

    python3 pipeline/fix_facts_discrepancies_date_year_2026_10_24.py          # сухой прогон
    python3 pipeline/fix_facts_discrepancies_date_year_2026_10_24.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
DISCREPANCIES = os.path.join(ROOT, 'facts_discrepancies.json')

FIXES = {
    # id: (старая дата, новая дата, дословная цитата facts.date, источник)
    'g64a94e27': ('2022-11-24', '2023-10-09',
                  '9 октября 2023 года, Москва – Группа российских топ-менеджеров ПАО «ВымпелКом» '
                  'во главе с генеральным директором Александром Торбаховым закрыла сделку по '
                  'выкупу компании у группы VEON.',
                  'https://beelinenow.ru/articles/pao-vympelkom-obyavlyaet-o-zavershenii-sdelki-po-vykupu-kompanii-u-mezhdunarodnogo-kholdinga-veon/'),
    'c2d0c1dcd': ('2024', '2025-10-30',
                  'Дата торгов 30.10.2025',
                  'https://rt-capital.ru/deals/19192/'),
}


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    for did, (old, new, quote, source) in FIXES.items():
        d = by_id[did]
        assert d['date'] == old, (did, d['date'])
        fd = d.get('facts', {}).get('date', {})
        assert fd.get('value') == new and fd.get('basis') == 'verified', (did, fd)
        d['date'] = new
        print('%s: %s -> %s (facts.date подтверждён двумя чтениями: %s | %s)' % (did, old, new, quote, source))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    disc = json.load(open(DISCREPANCIES, encoding='utf-8'))
    today = '2026-10-24'
    for item in disc:
        if item['id'] in FIXES and item['field'] == 'date' and item.get('resolved') is None:
            item['resolved'] = today
    json.dump(disc, open(DISCREPANCIES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
