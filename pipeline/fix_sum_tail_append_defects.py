# -*- coding: utf-8 -*-
"""Две ошибки, допущенные `move_sum_tails_into_valuation.py`, — исправление.

Обе найдены сразу после прогона, чтением результата на затронутых карточках.

1. ДОПИСКА НАЧИНАЛАСЬ СО СТРОЧНОЙ БУКВЫ. Кусок хвоста приклеивался к
   существующему значению через точку, но с маленькой буквы:
   «…при выполнении инвестиционных обязательств. конкурент предложил
   19 млрд рублей.» Шесть полей.

2. У cfdc0e962 ДОПИСКА ОКАЗАЛАСЬ ДУБЛЕМ, И РЕШЕНИЕ БЫЛО НЕВЕРНЫМ. Я отнёс
   «400000000 руб. (размер исковых требований)» в `law.terms`, решив, что
   это факт не из «Оценки». Место выбрано правильно, но факт там УЖЕ был, и
   куда лучшими словами: «Истец намерен взыскать понесенные за два года
   переговоров убытки в размере 400 миллионов рублей… В самом заявлении
   указана сумма в 244 млн руб.» Дописка добавила ту же цифру голыми
   разрядами. Ошибка методическая: решение по хвосту принималось, глядя на
   `eco.val`, а сверять надо было с ПОЛЕМ-ПОЛУЧАТЕЛЕМ. Ровно тот урок,
   который в CLAUDE.md уже записан («Прежде чем наполнять поле, проверьте,
   не показан ли факт под другой подписью»), — и я его повторил.

Сам `move_sum_tails_into_valuation.py` тоже поправлен, чтобы повторный
прогон с нуля давал верный результат: дописка капитализируется, cfdc0e962
переведена в `drop`.

Запуск:
    python3 pipeline/fix_sum_tail_append_defects.py            # сухой прогон
    python3 pipeline/fix_sum_tail_append_defects.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# Поле -> кусок, который был дописан со строчной буквы.
LOWERCASE_APPENDS = [
    ('g9c255b9c', 'eco.val', 'увеличение до 25%'),
    ('g97a4c417', 'eco.val', 'объем инвестиций в проект'),
    ('gd75ae46f', 'eco.val', 'рыночная оценка около 60'),
    ('g8430c9d9', 'eco.val', 'плюс 40-50 млрд руб.'),
    ('g6be1ac50', 'eco.val', 'источник указывает 75-100'),
    ('g2f572b66', 'law.struct', 'конкурент предложил 19'),
]

# Дописка-дубль, которую надо снять целиком.
DUPLICATE_APPEND = ('cfdc0e962', 'law.terms', ' 400000000 руб. (размер исковых требований).')

# Третий случай: в `eco.val` стояла ЗАГОТОВКА без единой цифры («Оценка
# экспертов»), и дописка приклеилась к ней — «Оценка экспертов. эксперты
# называют не менее 3 млрд руб.». Заготовка не значение, а подпись к
# отсутствующему значению: она заменяется целиком, а не дополняется.
STUB_REPLACE = ('g31541607', 'eco.val',
                'Оценка экспертов. эксперты называют не менее 3 млрд руб. до вычета долга '
                '(возможно 1,5 млрд руб.).',
                'Эксперты называют не менее 3 млрд руб. до вычета долга '
                '(возможно 1,5 млрд руб.).')


def get_field(card, path):
    obj = card
    for part in path.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def set_field(card, path, value):
    parts = path.split('.')
    obj = card
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for cid, field, piece in LOWERCASE_APPENDS:
        value = get_field(by_id[cid], field)
        assert isinstance(value, str), '%s.%s: поле не строка' % (cid, field)
        needle = '. ' + piece
        assert needle in value, \
            '%s.%s: не найдена дописка со строчной буквы (%r)' % (cid, field, piece[:30])
        fixed = value.replace(needle, '. ' + piece[0].upper() + piece[1:], 1)
        plan.append((cid, field, value, fixed))

    cid, field, tail = DUPLICATE_APPEND
    value = get_field(by_id[cid], field)
    assert isinstance(value, str) and value.endswith(tail), \
        '%s.%s: дописка-дубль уже снята или изменена' % (cid, field)
    plan.append((cid, field, value, value[:-len(tail)].rstrip()))

    cid, field, old, new = STUB_REPLACE
    value = get_field(by_id[cid], field)
    assert value == old, '%s.%s: значение уже другое: %r' % (cid, field, value)
    plan.append((cid, field, value, new))

    print('Правок: %d (капитализация дописки: %d, снятие дубля: 1, замена заготовки: 1)'
          % (len(plan), len(LOWERCASE_APPENDS)))
    for cid, field, old, new in plan:
        print('  %s %s' % (cid, field))
        print('     было : …%s' % old[-72:])
        print('     стало: …%s' % new[-72:])

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, field, _old, new in plan:
        set_field(by_id[cid], field, new)

    # Проверка на себе: ни одна из дописок больше не начинается со строчной.
    for cid, field, piece in LOWERCASE_APPENDS:
        value = get_field(by_id[cid], field)
        assert ('. ' + piece) not in value, \
            '%s.%s: дописка со строчной буквы осталась' % (cid, field)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
