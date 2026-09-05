# -*- coding: utf-8 -*-
"""Аудит перед публичной бетой (5 сентября 2026), продолжение: две правки
сумм и подписей, найденные при проверке блока «Крупнейшие сделки по
раскрытой сумме» после fix_audit_2026_09_05_data.py.

1. `g4e3b91d7` (IPO Совкомбанка): в `sum` стояло «200–219 млрд ₽» — это
   оценка ВСЕЙ компании по ценовому диапазону размещения, а не объём
   сделки; сама карточка в `eco.share` говорит: «Общий размер IPO составил
   11,5 млрд ₽ с учётом стабилизационного пакета». Сумма — 11,5 млрд ₽,
   оценка по диапазону — в `eco.val` первой фразой. Из-за этой подмены
   IPO стояло седьмым в «крупнейших сделках» рядом с покупками за сотни
   миллиардов.

2. `gc3d735fc` («Открытие»/ВТБ): у PwC в `eco.finadv` стояла подпись
   «оценка при подготовке к IPO (ранее)» — на карточке в скобках
   показывалось одинокое «ранее». Теперь: «оценка «Открытия» при подготовке
   к IPO, до сделки» — и сторона читается как сама компания.

Запуск: python3 pipeline/fix_audit_2026_09_05_sums.py
        python3 pipeline/fix_audit_2026_09_05_sums.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SOVCOM = 'g4e3b91d7'
SOVCOM_SUM_OLD, SOVCOM_SUM_NEW = '200–219 млрд ₽', '11,5 млрд ₽'
SOVCOM_VAL_PREFIX = 'Оценка всей компании по ценовому диапазону размещения — 200–219 млрд ₽. '

OTKRYTIE = 'gc3d735fc'
FINADV_OLD = ('АО «Деловые решения и технологии» (бывшая Deloitte) — независимый оценщик на стороне '
              'ЦБ (продавца); PwC — оценка при подготовке к IPO (ранее)')
FINADV_NEW = ('АО «Деловые решения и технологии» (бывшая Deloitte) — независимый оценщик на стороне '
              'ЦБ (продавца); PwC — оценка «Открытия» при подготовке к IPO, до сделки')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    sv = by_id[SOVCOM]
    assert sv['sum'] == SOVCOM_SUM_OLD and sv['eco']['sum'] == SOVCOM_SUM_OLD, (sv['sum'], sv['eco']['sum'])
    assert '11,5 млрд ₽' in sv['eco']['share'] and not sv['eco']['val'].startswith('Оценка всей компании')
    ot = by_id[OTKRYTIE]
    assert ot['eco']['finadv'] == FINADV_OLD, ot['eco']['finadv']
    print('1. %s sum: %s -> %s; eco.val += оценка по диапазону' % (SOVCOM, SOVCOM_SUM_OLD, SOVCOM_SUM_NEW))
    print('2. %s finadv -> %s' % (OTKRYTIE, FINADV_NEW))
    if not write:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')
        return
    sv['sum'] = SOVCOM_SUM_NEW
    sv['eco']['sum'] = SOVCOM_SUM_NEW
    sv['eco']['val'] = SOVCOM_VAL_PREFIX + sv['eco']['val']
    ot['eco']['finadv'] = FINADV_NEW
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('\nЗаписано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
