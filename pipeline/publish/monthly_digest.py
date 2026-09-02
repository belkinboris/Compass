# -*- coding: utf-8 -*-
"""Месячная сводка рынка для канала: что произошло за месяц по данным «Компаса».

ЗАЧЕМ. Просьба владельца 2 сентября 2026: «ежемесячную сводку в тг канале
добавить, интересная аналитика должна выходить, чтобы люди пересылали друг
другу». Канал до этого умел только одно — пост про одну сделку; человеку,
который следит за рынком целиком, он не давал ни одной цифры.

ЧТО СЧИТАЕМ И ЧЕГО НЕ СЧИТАЕМ. Только то, что уже лежит в карточках: число
сделок месяца, сколько из них с названной ценой, сумма этих цен, отрасли,
крупнейшие сделки, самые активные покупатели. Ничего не досчитываем и не
экстраполируем: сводка честно говорит, что это сделки, о которых написали
открытые источники, а не весь рынок.

ЧЕГО ЗДЕСЬ НЕТ И ПОЧЕМУ. Тем сделок («уход иностранного владельца», «IPO») в
сводке нет намеренно: замер 2 сентября показал, что поле `themes` у свежих
месяцев почти пустое (июль — 1 карточка из 41, август — 0 из 44), потому что
`tag_themes.py` по новым карточкам не прогонялся, а прогнать его целиком
нельзя (см. CLAUDE.md, урок про 230 расхождений). Раздел, который был бы пуст
у каждого второго месяца, хуже отсутствующего.

Разбор рублёвой суммы здесь свой, а не импортом из `deal_multiples.py`: тот
модуль тянет sqlalchemy на уровне импорта, а этот код исполняется в контейнере
рутины публикации, где лишняя зависимость — лишняя точка отказа.

Запуск:
    python3 pipeline/publish/monthly_digest.py               # сводка за прошлый месяц
    python3 pipeline/publish/monthly_digest.py --month 2026-08
"""
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import format_post  # noqa: E402  (esc, SITE)


def plural(n, one, few, many):
    """1 сделка / 2 сделки / 5 сделок. Своя копия, а не импорт из
    `ops_status.py`: тот модуль — про отчёт рутины в консоль, а не про
    публикацию, и тянуть его сюда значило бы связать канал с внутренней
    механикой отчётов."""
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


assert (plural(1, 'сделка', 'сделки', 'сделок'), plural(3, 'сделка', 'сделки', 'сделок'),
        plural(11, 'сделка', 'сделки', 'сделок')) == ('сделка', 'сделки', 'сделок')

SITE = format_post.SITE
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# Месяц в предложном падеже — «Рынок M&A в августе».
MONTHS_IN = ('январе', 'феврале', 'марте', 'апреле', 'мае', 'июне',
             'июле', 'августе', 'сентябре', 'октябре', 'ноябре', 'декабре')
MONTHS_NOM = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
              'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')

TOP_DEALS = 5
TOP_INDUSTRIES = 3
# Сводка выходит, только если месяц не пустой: пост «за месяц 2 сделки» не
# аналитика, а признак того, что приток стоял.
MIN_DEALS = 8

_UNIT = {'тыс': 1e-6, 'млн': 1e-3, 'млрд': 1.0, 'трлн': 1e3}   # -> млрд ₽
_RUB = re.compile(r'(?P<n1>\d[\d\s\xa0]*(?:[.,]\d+)?)'
                  r'(?:\s*[–—-]\s*(?P<n2>\d[\d\s\xa0]*(?:[.,]\d+)?))?'
                  r'\s*(?P<unit>тыс|млн|млрд|трлн)\.?\s*₽', re.I)
_ESTIMATE = re.compile(r'оценк|оценив|по\s+оценке|ориентировочн', re.I)


def rub_billions(text):
    """Сумма в млрд ₽ или None. Только рубли и только названная цена —
    оценка эксперта суммой сделки не считается (то же правило, что на
    «Аналитике»: иначе прозрачность рынка и полнота базы завышаются)."""
    if not text or _ESTIMATE.search(str(text)):
        return None
    m = _RUB.search(str(text))
    if not m:
        return None
    num = lambda s: float(s.replace(' ', '').replace('\xa0', '').replace(',', '.'))
    lo = num(m.group('n1'))
    hi = num(m.group('n2')) if m.group('n2') else lo
    return (lo + hi) / 2 * _UNIT[m.group('unit').lower()]


# Правила проверены на себе — это те форматы, что реально лежат в базе.
assert rub_billions('40 млрд ₽') == 40.0
assert rub_billions('1,3 трлн ₽') == 1300.0
assert abs(rub_billions('650 млн ₽') - 0.65) < 1e-9
assert rub_billions('50–100 млрд ₽ (по оценке)') is None       # оценка — не цена
assert rub_billions('$2,42 млрд') is None                       # не рубли
assert rub_billions('Не раскрыта') is None


def counts_as_price(deal):
    """Идёт ли цена этой сделки в сумму месяца и в список самых дорогих.

    Два исключения, оба про то, что цифра есть, а сделки за ней нет:
    сорвавшаяся сделка (её цену нельзя складывать с состоявшимися) и
    незакрытые торги — там в `sum` стоит СТАРТОВАЯ цена лота, которую
    назначил продавец, а не цена, о которой договорились стороны (пример:
    лот «Хортицы» на 7,8 млрд ₽ в августе 2026 — торги ещё шли)."""
    status = str(deal.get('status') or '')
    if status == 'Не состоялась':
        return False
    if str(deal.get('type') or '') == 'Продажа с торгов' and status != 'Закрыта':
        return False
    return True


def fmt_b(v):
    """«89,7 млрд ₽» / «1,4 трлн ₽» — так же, как подписаны столбцы на «Аналитике»."""
    if v >= 1000:
        s = ('%.1f' % (v / 1000)).rstrip('0').rstrip('.')
        return '%s трлн ₽' % s.replace('.', ',')
    if v >= 10:
        return '%d млрд ₽' % round(v)
    s = ('%.1f' % v).rstrip('0').rstrip('.')
    return '%s млрд ₽' % s.replace('.', ',')


def month_key(year, month):
    return '%04d-%02d' % (year, month)


def previous_month(today=None):
    today = today or date.today()
    return (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)


def month_deals(deals, year, month):
    key = month_key(year, month)
    return [d for d in deals if str(d.get('date') or '').startswith(key)]


def stats(base, year, month):
    """Всё, что сводка рассказывает, — одной чистой функцией, чтобы цифры
    можно было проверить без Telegram и без сети."""
    deals = base.get('deals', [])
    companies = base.get('companies', {})
    cur = month_deals(deals, year, month)
    priced = [(rub_billions(d.get('sum')), d) for d in cur if counts_as_price(d)]
    priced = [(v, d) for v, d in priced if v]
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    before = month_deals(deals, prev_year, prev_month)

    industries = {}
    for d in cur:
        for ind in (d.get('industries') or [d.get('ind')]):
            if ind and ind != 'Не определена':
                industries[ind] = industries.get(ind, 0) + 1

    buyers = {}
    for d in cur:
        bid = d.get('buyer')
        if bid and companies.get(bid):
            buyers[bid] = buyers.get(bid, 0) + 1

    closed = sum(1 for d in cur if str(d.get('status') or '') == 'Закрыта')
    talks = sum(1 for d in cur if str(d.get('status') or '') in ('Обсуждается', 'Подписана'))
    return {
        'year': year, 'month': month, 'key': month_key(year, month),
        'total': len(cur),
        'prev_total': len(before), 'prev_key': month_key(prev_year, prev_month),
        'priced': len(priced),
        'priced_sum': sum(v for v, _ in priced),
        'top': [d for _, d in sorted(priced, key=lambda t: -t[0])[:TOP_DEALS]],
        'top_sums': [v for v, _ in sorted(priced, key=lambda t: -t[0])[:TOP_DEALS]],
        'industries': sorted(industries.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_INDUSTRIES],
        'serial_buyers': sorted(((companies[b]['name'], n) for b, n in buyers.items() if n >= 2),
                                key=lambda kv: -kv[1])[:3],
        'closed': closed, 'talks': talks,
    }


def enough(st):
    """Стоит ли вообще выпускать сводку за этот месяц."""
    return st['total'] >= MIN_DEALS


def render(base, year, month):
    """Текст поста. Пусто, если месяц слишком пустой для сводки."""
    st = stats(base, year, month)
    if not enough(st):
        return ''
    esc = format_post.esc
    mon_in, mon_nom = MONTHS_IN[month - 1], MONTHS_NOM[month - 1]
    n = st['total']
    lines = ['📊 <b>Рынок слияний и поглощений в %s %d</b>' % (mon_in, year), '']

    head = ('За %s мы записали %d %s.'
            % (mon_nom, n, plural(n, 'сделку', 'сделки', 'сделок')))
    if st['prev_total']:
        head += (' Месяцем раньше — %d.' % st['prev_total'])
    lines.append(head)

    if st['priced']:
        lines.append('Цену назвали в %d из них — вместе %s.'
                     % (st['priced'], fmt_b(st['priced_sum'])))
    else:
        lines.append('Ни в одной из них стороны не назвали цену публично.')
    lines.append('')

    if st['top']:
        lines.append('<b>Самые дорогие сделки месяца</b>')
        for i, d in enumerate(st['top'], 1):
            lines.append('%d. <a href="%s/#/deal/%s">%s</a> — %s'
                         % (i, SITE, d['id'], esc(d.get('title') or ''), esc(d.get('sum') or '')))
        lines.append('')

    if st['industries']:
        parts = ['%s — %d' % (name, cnt) for name, cnt in st['industries']]
        lines.append('<b>Где сделок больше всего:</b> %s.' % esc(', '.join(parts)))

    if st['serial_buyers']:
        parts = ['%s (%d)' % (name, cnt) for name, cnt in st['serial_buyers']]
        lines.append('<b>Покупали не по одному разу:</b> %s.' % esc(', '.join(parts)))

    if st['closed'] or st['talks']:
        state = []
        if st['closed']:
            state.append('%d уже закрыты' % st['closed'])
        if st['talks']:
            state.append('%d пока в работе' % st['talks'])
        lines.append('Из %d %s %s.' % (n, plural(n, 'сделки', 'сделок', 'сделок'),
                                       ' и '.join(state)))
    lines.append('')

    # ЧЕСТНАЯ ОГОВОРКА — не украшение. Число «столько-то сделок за месяц»
    # обязано называть своё множество (CLAUDE.md: «у числа на экране два
    # свойства: величина и множество»), иначе его перескажут как статистику
    # всего рынка. Плюс прямо сказано, что свежий месяц ещё подрастёт: часть
    # сделок становится известна позже, и через месяц цифра будет другой.
    lines.append('Считаем по сделкам, о которых написали открытые источники, — '
                 'это не весь рынок. Цифры за свежий месяц ещё подрастут: '
                 'о части сделок становится известно позже.')
    lines.append('')
    lines.append('#итогимесяца #MA')
    return '\n'.join(lines)


def render_buttons(year, month):
    return {'inline_keyboard': [
        [{'text': 'Все сделки на «Компасе»', 'url': '%s/#/deals?year=%d' % (SITE, year)}],
        [{'text': 'Аналитика рынка', 'url': '%s/#/analytics' % SITE}],
    ]}


def load_base():
    with open(DATA, encoding='utf-8') as f:
        return json.load(f)


def main(argv):
    month_arg = None
    for i, a in enumerate(argv):
        if a == '--month' and i + 1 < len(argv):
            month_arg = argv[i + 1]
    if month_arg:
        year, month = int(month_arg[:4]), int(month_arg[5:7])
    else:
        year, month = previous_month()
    base = load_base()
    st = stats(base, year, month)
    text = render(base, year, month)
    print('Месяц: %s | сделок: %d | с ценой: %d | сумма: %s'
          % (st['key'], st['total'], st['priced'], fmt_b(st['priced_sum']) if st['priced'] else '—'))
    if not text:
        print('Сводка не выпускается: сделок меньше %d.' % MIN_DEALS)
        return
    print('-' * 60)
    print(text)
    print('-' * 60)
    print(format_post.buttons_preview(render_buttons(year, month)))


if __name__ == '__main__':
    main(sys.argv[1:])
