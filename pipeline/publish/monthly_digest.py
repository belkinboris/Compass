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

ЧЕГО В ТЕКСТЕ НЕТ И ПОЧЕМУ. Сравнения с прошлым месяцем и числа сделок с
названной ценой — владелец 2 сентября 2026 попросил убрать: «зачем это
читателю?». Оговорка о неполноте — одной фразой, без объяснений про «свежий
месяц еще подрастет». Темы месяца («Особенности месяца») показываются,
только когда хотя бы у двух тем набралось по две сделки (см. `stats()`):
раздел, пустой у каждого второго месяца, хуже отсутствующего.

Цены и допуск — из слоя фактов карточки (`facts.admitted`, `facts.price`),
то есть ровно те, что на «Аналитике»; своего разбора строки `sum` здесь нет
(1 ноября 2026, см. `admitted_price`).

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
    `ops_status.py`: тот модуль — про отчет рутины в консоль, а не про
    публикацию, и тянуть его сюда значило бы связать канал с внутренней
    механикой отчетов."""
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
TOP_THEMES = 3
# Тема попадает в сводку, только если ею помечено больше одной сделки: строка
# «продажа с торгов — 1» не наблюдение, а случайность. И весь раздел
# показывается, только когда таких тем хотя бы две, — одна тема с двумя
# сделками не «особенности месяца», а одна сделка с ярлыком.
MIN_THEME_DEALS = 2
MIN_THEMES_TO_SHOW = 2
# Сводка выходит, только если месяц не пустой: пост «за месяц 2 сделки» не
# аналитика, а признак того, что приток стоял.
MIN_DEALS = 8

def admitted_price(deal, metric='purchase_sums'):
    """Цена сделки в млрд ₽ — если сделка допущена к показателю «Аналитики»,
    иначе None. Одно правило с сайтом (аудит одинаковых понятий, 1 ноября
    2026): допуск `facts.admitted` и рублевая цена `facts.price.value_rub`
    уже посчитаны `facts_derive.py` и лежат в карточке. До этого сводка
    разбирала строку `sum` сама и складывала то, чего на сайте нет: раунды и
    допэмиссии, непрочитанные цены, середину диапазона без слова «оценка»,
    обсуждаемые оферты в «крупнейших» — и теряла валютные сделки.

    `metric`: 'purchase_sums' — сумма месяца, 'top_purchases' — крупнейшие
    (там еще нет «Обсуждается»)."""
    f = deal.get('facts') or {}
    if not (f.get('admitted') or {}).get(metric):
        return None
    rub = (f.get('price') or {}).get('value_rub')
    return rub / 1e9 if rub else None


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
    """Все, что сводка рассказывает, — одной чистой функцией, чтобы цифры
    можно было проверить без Telegram и без сети."""
    deals = base.get('deals', [])
    companies = base.get('companies', {})
    cur = month_deals(deals, year, month)
    priced = [(admitted_price(d), d) for d in cur]
    priced = [(v, d) for v, d in priced if v]
    tops = [(admitted_price(d, 'top_purchases'), d) for d in cur]
    tops = sorted(((v, d) for v, d in tops if v), key=lambda t: -t[0])[:TOP_DEALS]
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

    themes = {}
    for d in cur:
        for t in (d.get('themes') or []):
            themes[t] = themes.get(t, 0) + 1
    # Тема с названием отрасли («Недвижимость») в «Особенностях месяца» не
    # показывается: у отрасли свой счет («Где сделок больше всего: Недвижимость —
    # 44»), а тег-тема стоит лишь у части этих сделок (13 из 44), и читатель видел
    # одно слово с двумя числами (владелец, 2 ноября 2026, сводка за октябрь).
    industry_names = {i for d in deals for i in (d.get('industries') or [d.get('ind')]) if i}
    themes = [(t, n) for t, n in sorted(themes.items(), key=lambda kv: (-kv[1], kv[0]))
              if n >= MIN_THEME_DEALS and t not in industry_names][:TOP_THEMES]

    closed = sum(1 for d in cur if str(d.get('status') or '') == 'Закрыта')
    talks = sum(1 for d in cur if str(d.get('status') or '') in ('Обсуждается', 'Подписана'))
    return {
        'year': year, 'month': month, 'key': month_key(year, month),
        'total': len(cur),
        'prev_total': len(before), 'prev_key': month_key(prev_year, prev_month),
        'priced': len(priced),
        'priced_sum': sum(v for v, _ in priced),
        'top': [d for _, d in tops],
        'top_sums': [v for v, _ in tops],
        'industries': sorted(industries.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_INDUSTRIES],
        'serial_buyers': sorted(((companies[b]['name'], n) for b, n in buyers.items() if n >= 2),
                                key=lambda kv: -kv[1])[:3],
        'themes': themes if len(themes) >= MIN_THEMES_TO_SHOW else [],
        'closed': closed, 'talks': talks,
    }


def enough(st):
    """Стоит ли вообще выпускать сводку за этот месяц.

    Мало сделок — не единственная причина промолчать: `render()` пишет
    «Самые дорогие сделки месяца» и ссылки на них ТОЛЬКО когда `top` не
    пуст, а без единой ссылки на сделку `check_post.check_digest()` верно
    бракует пост («в сводке нет ни одной сделки»). У свежего месяца, где
    сумму еще не назвали ни у одной сделки (все «Обсуждается»/сумма не
    раскрыта), `total` может перевалить порог раньше, чем появится первая
    закрытая сделка с ценой, — сводка ждет, пока будет что показать.
    """
    return st['total'] >= MIN_DEALS and bool(st['top'])


def render(base, year, month):
    """Текст поста. Пусто, если месяц слишком пустой для сводки."""
    st = stats(base, year, month)
    if not enough(st):
        return ''
    esc = format_post.esc
    mon_in, mon_nom = MONTHS_IN[month - 1], MONTHS_NOM[month - 1]
    n = st['total']
    lines = ['📊 <b>Рынок слияний и поглощений в %s %d</b>' % (mon_in, year), '']

    # Владелец о первой живой сводке (2 сентября 2026): сравнение с прошлым
    # месяцем и «цену назвали в 9 из них — вместе 80 млрд» читателю не нужны
    # («зачем это читателю?»). Первая строка называет только то, о чем пост.
    # Сумма месяца не пропала: она стоит у каждой сделки в разделе «Самые
    # дорогие», где у цифры есть адрес. prev_total/priced в stats() остаются
    # для аналитики и тестов, в текст не идут.
    lines.append('За %s мы рассказали о %d %s.'
                 % (mon_nom, n, plural(n, 'сделке', 'сделках', 'сделках')))
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

    if st['themes']:
        parts = ['%s — %d' % (name, cnt) for name, cnt in st['themes']]
        lines.append('<b>Особенности месяца:</b> %s.' % esc(', '.join(parts)))

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
    # обязано называть свое множество (CLAUDE.md: «у числа на экране два
    # свойства: величина и множество»), иначе его перескажут как статистику
    # всего рынка. Первая редакция («это не весь рынок. Цифры за свежий месяц
    # еще подрастут…») владельцу показалась оправданием («что за свежий
    # месяц, как вообще такое писать?») — оставлена одна спокойная фраза о
    # том, откуда берутся сделки.
    lines.append('Мы собираем только сделки, информация о которых публично доступна.')
    lines.append('')
    # «#итогимесяца» партнер (7 сентября 2026) предложила заменить на
    # «#статистика»: по этому слову сводку ищут, а «итоги месяца» — наш
    # внутренний ярлык рубрики.
    lines.append('#статистика #MA')
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
