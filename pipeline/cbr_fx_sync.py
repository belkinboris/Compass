# -*- coding: utf-8 -*-
"""Официальные курсы ЦБ (доллар, евро) для пересчёта цен сделок в рубли.

Зачем. Из 1 120 состоявшихся покупок с 2022 года у 77 цена названа в
долларах или евро — и до 26 сентября 2026 такие сделки выпадали из
мультипликаторов целиком: расчёт понимает только рубли. Пересчёт по
официальному курсу ЦБ на дату сделки — не оценка, а арифметика, и её
делает `facts.py` при сборке слоя фактов (`fx.py` читает таблицу, которую
пишет этот скрипт).

Таблица лежит в git (`pipeline/cbr_fx_rates.json`), а не спрашивается у ЦБ на
лету: сборка фактов идёт в каждой рутине, и её итог не должен зависеть от
того, открыт ли сегодня cbr.ru из контейнера. Обновляет таблицу рутина
«банки — синхронизация с ЦБ» (раз в день).

    python3 pipeline/cbr_fx_sync.py            # показать, что изменится
    python3 pipeline/cbr_fx_sync.py --write
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'pipeline', 'cbr_fx_rates.json')
SINCE = date(2021, 1, 1)
CODES = {'USD': 'R01235', 'EUR': 'R01239'}
URL = 'https://www.cbr.ru/scripts/XML_dynamic.asp'


def fetch(code, since, until):
    r = httpx.get(URL, params={'date_req1': since.strftime('%d/%m/%Y'),
                               'date_req2': until.strftime('%d/%m/%Y'),
                               'VAL_NM_RQ': code}, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = {}
    for rec in root.findall('Record'):
        day = datetime.strptime(rec.get('Date'), '%d.%m.%Y').date().isoformat()
        nominal = int(rec.findtext('Nominal'))
        value = float(rec.findtext('Value').replace(',', '.'))
        out[day] = round(value / nominal, 4)
    return out


def main(write):
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    today = date.today()
    table = {'source': 'Банк России, официальные курсы (XML_dynamic.asp)', 'updated': today.isoformat()}
    for cur, code in CODES.items():
        try:
            rates = fetch(code, SINCE, today)
        except (httpx.HTTPError, ET.ParseError) as e:
            print('%s: ЦБ не ответил (%s) — оставляю прежнюю таблицу' % (cur, e))
            return 0
        if not rates:
            print('%s: пустой ответ ЦБ — оставляю прежнюю таблицу' % cur)
            return 0
        table[cur] = dict(sorted(rates.items()))
        added = len(set(rates) - set((old.get(cur) or {})))
        print('%s: %d дат, новых %d, последняя %s = %s ₽'
              % (cur, len(rates), added, max(rates), rates[max(rates)]))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if {k: v for k, v in old.items() if k != 'updated'} == {k: v for k, v in table.items() if k != 'updated'}:
        print('Без изменений.')
        return 0
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(table, f, ensure_ascii=False, indent=0, sort_keys=False)
        f.write('\n')
    print('Записано: %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
