# -*- coding: utf-8 -*-
"""Хвост «Сумма: …» с фактами — разнести по полям, а не стереть.

ОТКУДА ЗАДАЧА. `strip_import_service_tails.py` (15 августа 2026) снял 603
служебных хвоста компактного импорта, но НАМЕРЕННО не тронул те, где в
хвосте стояли числа, которых нет в полях суммы: «Enterprise Value
оценивается в 5,8 млрд руб.», «из которых 7,7 млрд руб. пошли на
обслуживание долга», «рыночная оценка около 60 млрд руб.». Признак дефекта
— повод прочитать, а не основание стереть (CLAUDE.md): это факты, просто не
в своём поле. Осталось 150 карточек, и это их разбор.

КАК КЛАССИФИЦИРОВАНЫ. Не по строкам, а по ВЕЛИЧИНАМ: числа хвоста и полей
карточки переводятся в рубли/штуки с учётом «млн»/«млрд»/«тыс», и
сравниваются множества значений. Иначе «25600000000» и «25,6 млрд ₽» —
одно и то же — считались бы разными (так и было в первом замере), а «33»
из «33,01% доли» считалось бы суммой. Проценты и множители (`5,5x`) из
сравнения исключены, годы тоже.

  A. 103 поля — все величины хвоста уже есть на карточке. Хвост снимается:
     он не добавляет ничего, а на экране висит служебной строкой.
  B.  31 поле — величины новые, а «Оценка и дисконт» (`eco.val`) пуста.
     Хвост переезжает В НЕЁ дословно: это ровно то поле, для которого он
     написан.
  C.  17 полей — величины новые, но `eco.val` уже занята. Каждая прочитана
     глазами, решение записано в таблице `READ` ниже с причиной. Механически
     тут решать нельзя: у g8b02811a хвост («несколько 100 млн руб.») слабее
     того, что уже стоит в `eco.val`, а у cfdc0e962 число вообще не про
     цену сделки — это размер исковых требований, и место ему в «Условиях».

ЧТО ЗАПРЕЩЕНО И ЧЕМ ЭТО ДЕРЖИТСЯ. Ни одного нового слова: всё, что
записывается, обязано быть ДОСЛОВНОЙ подстрокой хвоста этой же карточки.
Проверяется `assert` на каждой правке — тот же приём, что в
`pipeline/extract_approvals.py`, где это главная проверка, а не украшение.

ХВОСТ-ПОМЕТКА СТОРОНЫ НЕ ТРОГАЕТСЯ. У части карточек за суммой идёт ещё
и «(Покупатель: … )» — это отдельный класс дефекта (183 поля), он не
входит в этот прогон и остаётся на месте.

Запуск:
    python3 pipeline/move_sum_tails_into_valuation.py            # сухой прогон
    python3 pipeline/move_sum_tails_into_valuation.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SUM_TAIL = re.compile(r'(?:^|(?<=[.!?])\s+)Сумма:\s*(.*)$', re.S)
PARTY_TAIL = re.compile(r'\s*\((?:[^()]*\([^()]*\)[^()]*|(?:Покупател|Продавец|Продавц|Инвестор)[^()]*)\)\s*$')

# Заготовки: подпись к отсутствующему значению, а не значение. Дописка их
# не дополняет, а ЗАМЕНЯЕТ — иначе выходит «Оценка экспертов. эксперты
# называют не менее 3 млрд руб.».
STUBS = {'Оценка экспертов', 'По оценкам экспертов', 'Оценка аналитиков'}

PLACEHOLDER = {'', '—', 'не раскрыта', 'публично не сообщалось', 'не привлекался',
               'не определена', 'не раскрыты', 'не раскрывалась', 'не раскрывались',
               'не сообщалось', 'нет данных'}

SCALE = {'млрд': 1e9, 'миллиард': 1e9, 'млн': 1e6, 'миллион': 1e6, 'тыс': 1e3, 'тысяч': 1e3}
AMOUNT = re.compile(r'(\d[\d\s]*(?:[.,]\d+)?)\s*'
                    r'(млрд|миллиард\w*|млн|миллион\w*|тыс\w*)?(?!\s*[%xх])', re.I)

# --- группа C: решение по каждой карточке, прочитанной глазами -------------
# ('поле-получатель', 'дословный кусок хвоста')  либо ('drop', причина)
READ = {
 'g22b470f6': ('eco.val', '40–80 млн EUR (экспертная оценка, официально не раскрывается)',
               'вторая, независимая оценка в ЕВРО — в eco.val стоит оценка Шапошникова в '
               'долларах ($30–40 млн); это разные оценки, а не одна'),
 'g072d8c14': ('eco.val', '~3,5 млрд руб. (теоретическая стоимость по 291 руб./акцию)',
               'теоретическая стоимость по цене акции — расчёт, которого в eco.val нет'),
 'g9c255b9c': ('eco.val', 'увеличение до 25% — около 2-3 млрд руб. в совокупности',
               'оценка ВТОРОГО этапа (доведение доли до 25%), в eco.val только первый'),
 'g97a4c417': ('eco.val', 'объем инвестиций в проект — 1,45 млрд руб.',
               'объём инвестиций в проект — не цена сделки, но величина того же ряда; '
               'в eco.val её нет'),
 'g8b02811a': ('drop', '', 'хвост «несколько 100 млн руб.» слабее и расплывчатее оценки, '
                           'которая уже стоит в eco.val — добавить нечего'),
 'ge571a54e': ('eco.val', '209,1 млн USD (19,1 млрд руб. Equity Value, EV 20,2 млрд руб.)',
               'разложение цены на Equity Value и EV — структура, которой в eco.val нет'),
 'gd75ae46f': ('eco.val', 'рыночная оценка около 60 млрд руб.',
               'рыночная оценка актива; в eco.val сказано лишь, что цену не назвали'),
 'g8b512496': ('eco.val', 'Enterprise Value > 3,5 млрд руб.',
               'EV с учётом долга; в eco.val — цена без учёта долга, это разные величины'),
 'g8430c9d9': ('eco.val', 'плюс 40-50 млрд руб. на строительство',
               'разложение общих инвестиций (65 млрд) на участок и стройку'),
 'g6be1ac50': ('eco.val', 'источник указывает 75-100 млрд рублей',
               'оценка источника; в eco.val — оценка аналитика «Синары» (40-50 млрд)'),
 'g2f572b66': ('law.struct', 'конкурент предложил 19 млрд рублей',
               'предложение проигравшего участника — механика конкурса, а не оценка'),
 'g52a97d10': ('eco.val', '10-11 млрд рублей (рыночная стоимость)',
               'рыночная стоимость диапазоном; в eco.val — «более 10 млрд» без верхней границы'),
 'gf1608a6f': ('eco.val', '90-100 млрд руб. (оценка МТС, официально не раскрывается)',
               'оценка самой МТС; в eco.val — комментарий стороннего аналитика'),
 'g31541607': ('eco.val', 'эксперты называют не менее 3 млрд руб. до вычета долга '
                          '(возможно 1,5 млрд руб.)',
               'в eco.val стоит заготовка «Оценка экспертов» без единой цифры — '
               'хвост её и наполняет'),
 'cfdc0e962': ('drop', '', 'величина не про цену сделки (размер исковых требований) — '
                           'и она УЖЕ стоит в law.terms словами: «взыскать… убытки в размере '
                           '400 миллионов рублей… В самом заявлении указана сумма в 244 млн '
                           'руб.». Дописка была бы тем же числом голыми разрядами'),
 'c06799f22': ('eco.val', '77 млрд руб. (предложение на продажу доли 51%) или 74 млрд руб. '
                          '(предложение на выкуп доли 49%)',
               'две встречные оферты сторон; в eco.val — оценка Бурмистрова'),
 'c9bad29b7': ('eco.val', '$2,5–3 млрд (по оценке при дисконтах) или минимум $5 млрд '
                          '(справедливая стоимость портфеля по Forbes), возможно $10 млрд и более',
               'оценки НА МОМЕНТ ПЕРЕГОВОРОВ (февраль 2023); в eco.val — оценка по факту '
               'закрытия сделки ($2 млрд), это разные моменты истории'),
}


# --- обрезанная сумма: импорт оборвал число на десятичной запятой ---------
# Найдено при разборе хвостов: у четырёх карточек базы поле `sum` не несёт ни
# единицы измерения, ни значка валюты. У трёх причина одна и та же и видна
# насквозь — число оборвано ровно на запятой, а целое значение лежит в
# хвосте «Сумма: …» ЭТОЙ ЖЕ карточки: «960,2 млн руб.» -> «960».
# Четвёртая (g048c2ca3, «1 фунт стерлингов (номинальная цена)») не дефект:
# это честная запись символической цены, просто у фунта нет значка в нашем
# списке валют — не трогаем.
BROKEN_SUM = {
    'g202f49be': ('3', '3,6 млрд ₽', 'Объем размещения составил 3,6 млрд рублей'),
    'caac79625': ('960', '960,2 млн ₽', 'Сумма: 960,2 млн руб.'),
    'c15d1a169': ('до 11', 'до 11,8 млрд ₽', 'до 11,8 млрд ₽'),
}


def is_placeholder(v):
    return not isinstance(v, str) or v.strip().lower() in PLACEHOLDER


def values(text):
    out = set()
    for m in AMOUNT.finditer(str(text or '')):
        raw = m.group(1).replace(' ', '').replace(',', '.')
        try:
            n = float(raw)
        except ValueError:
            continue
        unit = (m.group(2) or '').lower()
        mult = 1
        for key, factor in SCALE.items():
            if unit.startswith(key):
                mult = factor
                break
        if mult == 1 and (1900 < n < 2100 or n < 1000):
            continue
        out.add(round(n * mult))
    return out


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


def _self_check():
    assert values('25600000000 руб.') == values('25,6 млрд ₽'), \
        'одна величина, записанная цифрами и словами, обязана совпасть'
    assert values('33,01% доли') == set(), 'процент — не сумма'
    assert values('EV/EBITDA 5,5x') == set(), 'мультипликатор — не сумма'
    assert values('в 2021 году') == set(), 'год — не сумма'
    assert 5800000000 in values('Enterprise Value оценивается в 5,8 млрд руб.')


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))

    plan = {'A': [], 'B': [], 'C': [], '?': []}
    for deal in data['deals']:
        for field in ('extra', 'eco.rationale'):
            text = get_field(deal, field)
            if not isinstance(text, str):
                continue
            m = SUM_TAIL.search(text)
            if not m:
                continue
            tail = m.group(1).strip()
            party = PARTY_TAIL.search(tail)
            sum_part = tail[:party.start()].strip() if party else tail
            kept_party = tail[party.start():].strip() if party else ''
            eco = deal.get('eco') or {}
            known = (values(deal.get('sum')) | values(eco.get('sum'))
                     | values(eco.get('val')) | values(eco.get('context')))
            fresh = values(sum_part) - known

            head = text[:m.start()].rstrip()
            rebuilt = (head + (' ' + kept_party if kept_party else '')).strip()

            if not fresh:
                plan['A'].append((deal, field, rebuilt, sum_part))
            elif is_placeholder(eco.get('val')):
                plan['B'].append((deal, field, rebuilt, sum_part))
            elif deal['id'] in READ:
                plan['C'].append((deal, field, rebuilt, sum_part, READ[deal['id']]))
            else:
                plan['?'].append((deal['id'], field, sorted(fresh), sum_part[:90]))

    print('A. хвост снимается (все величины уже на карточке): %d' % len(plan['A']))
    print('B. хвост переезжает в «Оценку и дисконт» (была пуста): %d' % len(plan['B']))
    print('C. прочитано глазами, решение по таблице READ: %d' % len(plan['C']))
    if plan['?']:
        print('НЕ РАЗОБРАНО (нет записи в READ): %d' % len(plan['?']))
        for row in plan['?']:
            print('   ', row)
        return 1

    # --- дословность: всё, что пишем, обязано лежать в хвосте -------------
    for deal, field, _rebuilt, sum_part in plan['B']:
        assert sum_part and sum_part in (get_field(deal, field) or ''), \
            '%s: значение для eco.val не лежит в тексте дословно' % deal['id']
    for deal, field, _rebuilt, sum_part, (target, piece, _why) in plan['C']:
        if target == 'drop':
            continue
        assert piece in sum_part, \
            '%s: кусок %r не лежит в хвосте дословно' % (deal['id'], piece[:40])

    for deal, _f, _r, sum_part, (target, piece, why) in plan['C']:
        print('  %s -> %-11s %s' % (deal['id'], target, why[:78]))

    # --- обрезанная сумма ---------------------------------------------------
    by_id = {d['id']: d for d in data['deals']}
    print('\nОбрезанных сумм к починке: %d' % len(BROKEN_SUM))
    for cid, (old, new, evidence) in BROKEN_SUM.items():
        card = by_id[cid]
        assert card.get('sum') == old, \
            '%s: sum уже другое: %r, ожидали %r' % (cid, card.get('sum'), old)
        haystack = ' '.join(str(card.get(k) or '') for k in ('extra', 'sum')) + \
                   ' ' + str((card.get('eco') or {}).get('sum') or '')
        assert evidence in haystack, \
            '%s: подтверждения %r нет в самой карточке' % (cid, evidence[:40])
        print('  %s: sum %r -> %r  (в карточке: %r)' % (cid, old, new, evidence[:46]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, field, rebuilt, _sum_part in plan['A']:
        set_field(deal, field, rebuilt)

    for deal, field, rebuilt, sum_part in plan['B']:
        set_field(deal, field, rebuilt)
        deal.setdefault('eco', {})['val'] = sum_part.rstrip('.') + '.'

    for deal, field, rebuilt, _sum_part, (target, piece, _why) in plan['C']:
        set_field(deal, field, rebuilt)
        if target == 'drop':
            continue
        current = get_field(deal, target)
        # Дописка всегда с заглавной: она встаёт ПОСЛЕ точки, и строчная там
        # читается как обрыв («…обязательств. конкурент предложил 19 млрд»).
        addition = piece.rstrip('.') + '.'
        addition = addition[0].upper() + addition[1:]
        if is_placeholder(current) or current.strip().rstrip('.') in STUBS:
            set_field(deal, target, addition)
        else:
            set_field(deal, target, current.rstrip().rstrip('.') + '. ' + addition)

    for cid, (_old, new, _evidence) in BROKEN_SUM.items():
        by_id[cid]['sum'] = new
        if (by_id[cid].get('eco') or {}).get('sum') in (_old, None):
            by_id[cid].setdefault('eco', {})['sum'] = new

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
