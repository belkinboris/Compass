# -*- coding: utf-8 -*-
"""Курс ЦБ на дату сделки — для пересчёта цены в долларах или евро в рубли.

Таблицу курсов пишет `pipeline/cbr_fx_sync.py` (рутина «банки», раз в день);
здесь только чтение. Сервер сайта модуль не вызывает: пересчёт делается при
сборке слоя фактов (`facts.py`), и в базу ложится уже рублёвое число вместе
с исходной суммой, курсом и датой курса.

Какой курс берётся:
  • у сделки есть день — официальный курс на этот день, а если в этот день
    курса нет (выходной), то последний установленный до него;
  • у сделки только месяц — средний курс за этот месяц;
  • только год — не пересчитываем: за год доллар ходил от 60 до 120 ₽
    (2022), и любой выбранный день был бы выдумкой.
"""
from __future__ import annotations

import json
import os
from typing import Any

RATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline', 'cbr_fx_rates.json')
# Сделка свежее таблицы: берём последний известный курс, но не старше
# недели — иначе таблица просто не обновлялась, и число было бы случайным.
MAX_GAP_DAYS = 7

_table: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _table
    if _table is None:
        try:
            _table = json.load(open(RATES_PATH, encoding='utf-8'))
        except (OSError, ValueError):
            _table = {}
    return _table


def rate_on(currency: str, day: str | None) -> dict[str, Any] | None:
    """{'rate', 'date', 'method'} или None, если курс честно не выбрать.
    `method`: 'day' — курс на день сделки (или последний до него),
    'month_avg' — средний за месяц, когда у сделки нет дня."""
    from datetime import date as _date
    rates = (_load().get(currency) or {})
    if not rates or not day:
        return None
    day = str(day)
    if len(day) >= 10 and day[4] == '-' and day[7] == '-':
        prior = [d for d in rates if d <= day[:10]]
        if not prior:
            return None
        used = max(prior)
        gap = (_date.fromisoformat(day[:10]) - _date.fromisoformat(used)).days
        if gap > MAX_GAP_DAYS:
            return None
        return {'rate': rates[used], 'date': used, 'method': 'day'}
    if len(day) == 7 and day[4] == '-':
        month = [v for d, v in rates.items() if d.startswith(day)]
        if not month:
            return None
        return {'rate': round(sum(month) / len(month), 4), 'date': day, 'method': 'month_avg'}
    return None
