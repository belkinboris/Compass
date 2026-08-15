# -*- coding: utf-8 -*-
"""Каталог вычитки, класс C1: « - » (дефис в позиции тире) — 217 полей.

НАЙДЕНО прошлым кругом вычитки, здесь — сплошной прогон по всей базе.
«Пробел-дефис-пробел» в русском тексте — либо диапазон чисел (короткое
тире «–»), либо пунктуационное тире: пропущенная связка («мультипликатор
- 0,6» = «мультипликатор — 0,6»), обособление («Новый владелец - АО
«Каппа РУС»»), список долей («8,7% - у Goldman Sachs»). Оба тире — не
дефис.

ДВЕ КАТЕГОРИИ, РАЗНЫЙ ЗНАК:
  * ДИАПАЗОН (цифра перед дефисом, опционально с единицей млн/млрд/тыс/%,
    и цифра сразу после) — короткое тире «–»: «900 млн - 2 млрд ₽»,
    «в 2022 - 1,7 млрд руб.». 6 полей.
  * ВСЁ ОСТАЛЬНОЕ — длинное тире «—»: связка, обособление, список. 279 полей.

ИСКЛЮЧЕНИЕ — ДЕФИС ВНУТРИ НАЗВАНИЯ В КАВЫЧКАХ. «Инвестиционные решения -
4», «Ренессанс Капитал - ФК», «М.Видео - Эльдорадо», «Кассир.ру -
Национальный билетный оператор» и другие — это ЗАРЕГИСТРИРОВАННЫЕ имена
юрлиц с дефисом внутри, а не пунктуация; замена испортила бы название.
Признак — дефис лежит ВНУТРИ пары «…», от неё не трогается ничего (8 полей).

ОТДЕЛЬНЫЙ ДЕФЕКТ ПОД ТЕМ ЖЕ ПРИЗНАКОМ — g71aec6a5. eco.rationale несёт
«что «Роснефть» - Артаг" работает…» — сломанное ВЛОЖЕННОЕ название: сама
карточка называется «...АО «НК «Роснефть» — Артаг» (Северная Осетия)...»
(двойные ёлочки, тире внутри имени), а в rationale вложенная кавычка не
открылась (одна «, не две) и не закрылась (голая ASCII-кавычка вместо »).
Это не дефис-вместо-тире, а разбор, потерявший структуру имени — чинится
отдельно, приведением к формату заголовка этой же карточки.

Запуск:
    python3 pipeline/fix_hyphen_as_dash.py            # сухой прогон
    python3 pipeline/fix_hyphen_as_dash.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ECO_FIELDS = ('rationale', 'context', 'share', 'val', 'target_fin', 'fin', 'sum', 'finadv')
LAW_FIELDS = ('struct', 'appr', 'terms')

HYPHEN = re.compile(r'([а-яёА-ЯЁ0-9%»)]) - ([а-яёА-ЯЁ0-9«(])')
RANGE_BEFORE = re.compile(r'\d\s*(?:млн|млрд|тыс|%)?\s*$')
RANGE_AFTER = re.compile(r'^\s*\d')

BROKEN_NAME_ID = 'g71aec6a5'
BROKEN_NAME_OLD = '«Роснефть» - Артаг"'
BROKEN_NAME_NEW = '«Роснефть» — Артаг»'


def inside_guillemets(text, pos):
    """Позиция `pos` лежит внутри ближайшей пары «...» — дефис в имени."""
    left = text.rfind('«', 0, pos)
    if left == -1:
        return False
    right = text.find('»', left)
    if right == -1:
        return False
    return left < pos < right


def fix_field(text):
    """Заменить каждый « - » на «–» (диапазон) или «—» (остальное)."""
    out = []
    last = 0
    for m in HYPHEN.finditer(text):
        dash_pos = m.start() + 1  # позиция самого дефиса (после первой группы)
        if inside_guillemets(text, dash_pos):
            continue
        before, after = text[:m.start() + 1], text[m.end() - 1:]
        replacement = '–' if RANGE_BEFORE.search(before) and RANGE_AFTER.match(after) else '—'
        out.append(text[last:m.start()])
        out.append(m.group(1) + ' ' + replacement + ' ' + m.group(2))
        last = m.end()
    out.append(text[last:])
    return ''.join(out)


def _self_check():
    assert fix_field('900 млн - 2 млрд ₽') == '900 млн – 2 млрд ₽'
    assert fix_field('в 2022 - 1,7 млрд руб.') == 'в 2022 – 1,7 млрд руб.'
    assert fix_field('Новый владелец - АО «Каппа РУС»') == \
        'Новый владелец — АО «Каппа РУС»'
    assert fix_field('еще 8,7% - у Goldman Sachs') == 'еще 8,7% — у Goldman Sachs'
    # дефис внутри названия в кавычках не трогается
    assert fix_field('ООО «Инвестиционные решения - 4», из них 71%') == \
        'ООО «Инвестиционные решения - 4», из них 71%'
    assert fix_field('группы «М.Видео - Эльдорадо». Он владеет') == \
        'группы «М.Видео - Эльдорадо». Он владеет'


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
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for deal in data['deals']:
        pairs = [('extra', deal.get('extra'))]
        pairs += [('eco.' + k, (deal.get('eco') or {}).get(k)) for k in ECO_FIELDS]
        pairs += [('law.' + k, (deal.get('law') or {}).get(k)) for k in LAW_FIELDS]
        for field, value in pairs:
            if not isinstance(value, str) or not value:
                continue
            if deal['id'] == BROKEN_NAME_ID and BROKEN_NAME_OLD in value:
                continue  # чинится отдельно ниже
            new = fix_field(value)
            if new != value:
                plan.append((deal, field, value, new))

    broken = by_id.get(BROKEN_NAME_ID)
    assert broken is not None, 'нет карточки %s' % BROKEN_NAME_ID
    assert BROKEN_NAME_OLD in (broken.get('eco') or {}).get('rationale', ''), \
        'g71aec6a5: сломанное имя уже другое'

    n_range = sum(1 for _d, _f, old, new in plan if '–' in new and '–' not in old)
    n_em = len(plan) - n_range
    print('Правок «пробел-дефис-пробел»: %d (диапазонов «–»: %d, тире «—»: %d)'
          % (len(plan), n_range, n_em))
    print('Плюс восстановление вложенного имени в %s' % BROKEN_NAME_ID)
    for deal, field, old, new in plan[:10]:
        print('  %s %-13s %r -> %r' % (deal['id'], field, old[:40], new[:40]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, field, _old, new in plan:
        set_field(deal, field, new)

    broken['eco']['rationale'] = broken['eco']['rationale'].replace(
        BROKEN_NAME_OLD, BROKEN_NAME_NEW)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
