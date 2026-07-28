# -*- coding: utf-8 -*-
"""Приток: эта новость — про НОВУЮ сделку или про ту, что уже в базе.

ЗАЧЕМ. Об одной сделке пишут пять изданий за два дня. Если не отличать новую
сделку от новой новости о старой, база превратится в ленту дублей, а телеграм —
в спам из пяти постов об одном и том же. Ответ этого модуля — вход и для
базы («создать карточку» или «дополнить такую-то»), и для публикации
(«написать пост» или «отредактировать существующий»).

КАК УСТРОЕНО. Три сигнала, от сильного к слабому:
  1. Тот же URL источника — очевидный повтор.
  2. Совпадение названий в кавычках плюс близкая сумма (±5%) и дата в пределах
     45 дней. Это самый надёжный сигнал: имя актива и цена совпадают редко.
  3. Три и более общих значимых слов заголовка (основы по 6 знаков, стоп-слова
     выброшены) при дате в пределах 30 дней — либо пять и более при 90 днях.
     Пороги подобраны замером, а не на глаз: при «пять слов / 90 дней» правило
     узнавало только 45% собственных заголовков базы, при «три слова / 30 дней»
     — 78% и всего 1,3% чужих совпадений (их список см. в замере).
Правило 3 — то же, которым `loadBulkDeals()` в интерфейсе прячет компактные
записи, задублированные подробной карточкой; здесь оно переиспользовано, чтобы
приток и показ судили об одинаковости одинаково.

КАК ИЗМЕРЕНО. `--measure` прогоняет ВСЕ 1333 заголовка базы против самой базы:
каждый заголовок обязан найти сам себя (полнота 100% — иначе правило слепое) и
не должен находить ЧУЖУЮ карточку (каждое такое совпадение — либо будущий
ложный склей, либо настоящий дубль в базе, и его надо прочитать глазами).

ЧЕГО ЭТОТ МОДУЛЬ НЕ ДЕЛАЕТ. Он не решает, что именно дописать в карточку:
это работа `promote.py` и человека. Он отвечает только на вопрос «новое или
уже есть».

Запуск:
    python3 pipeline/ingest/match.py --measure
"""
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# Слова, которые есть почти в каждом заголовке о сделке и потому ничего не
# различают. Список взят из `loadBulkDeals()` в index.html — там он собран на
# реальных дублях.
STOP = {
    'ооо', 'пао', 'компания', 'компании', 'группа', 'группой', 'доля', 'долей', 'акций',
    'сделка', 'бизнес', 'приобрел', 'приобрела', 'купил', 'купила', 'может', 'купить',
    'россии', 'покупает', 'инвестирует', 'структурн', 'инвестиционн', 'совместн',
    'предприят', 'создают', 'создала', 'создаёт', 'организац', 'инвесторов', 'залог',
    'закрыт', 'провел', 'получил', 'заключил', 'заключила', 'консолидировал', 'привлек',
    'привлекла', 'выкупил', 'выкупила', 'стороны', 'участием', 'рамках', 'процентов',
}
STOP_STEMS = {w[:6] for w in STOP}


def stems(text):
    words = re.sub(r'«[^»]{2,40}»', ' ', str(text or '')).lower()
    words = re.sub(r'[«»"\'().,:;–—-]', ' ', words).split()
    return {w[:6] for w in words if len(w) > 4 and w[:6] not in STOP_STEMS}


def quoted(text):
    return {m.group(1).lower() for m in re.finditer(r'«([^»]{2,40})»', str(text or ''))}


def amount(text):
    m = re.search(r'(\d[\d\s.,]*)\s*(млрд|млн)', str(text or ''), re.I)
    if not m:
        return None
    num = float(m.group(1).replace(' ', '').replace(',', '.').rstrip('.'))
    return num * (1000 if m.group(2).lower() == 'млрд' else 1)


def days_between(a, b):
    try:
        ya, ma, da = (int(x) for x in str(a)[:10].split('-'))
        yb, mb, db = (int(x) for x in str(b)[:10].split('-'))
        return abs((date(ya, ma, da) - date(yb, mb, db)).days)
    except Exception:
        return 9999


def index_base(deals):
    """Предрасчёт того, по чему сравниваем: делается один раз на прогон."""
    return [{
        'id': d['id'], 'date': d.get('date'), 'title': d.get('title'),
        'stems': stems(d.get('title')), 'quoted': quoted(d.get('title')),
        'amount': amount(d.get('title')) or amount(d.get('sum')),
        'urls': {str(s[1]) for s in (d.get('src') or []) if len(s) > 1},
    } for d in deals]


def match(item, idx):
    """item: {'title','date','url'} -> (deal_id, причина) или (None, None)."""
    url = str(item.get('url') or '')
    t_stems, t_quoted, t_amount = stems(item.get('title')), quoted(item.get('title')), amount(item.get('title'))
    for row in idx:
        if url and url in row['urls']:
            return row['id'], 'тот же адрес источника'
    for row in idx:
        gap = days_between(item.get('date'), row['date'])
        if t_quoted & row['quoted'] and t_amount and row['amount'] and gap <= 45:
            if abs(t_amount - row['amount']) / max(t_amount, row['amount']) < 0.05:
                return row['id'], 'совпали название в кавычках и сумма'
    for row in idx:
        gap = days_between(item.get('date'), row['date'])
        if t_quoted & row['quoted'] and gap <= 45 and len(t_stems & row['stems']) >= 2:
            return row['id'], 'общее название в кавычках и два общих слова'
    for row in idx:
        gap = days_between(item.get('date'), row['date'])
        common = len(t_stems & row['stems'])
        if (gap <= 30 and common >= 3) or (gap <= 90 and common >= 5):
            return row['id'], 'общие слова заголовка: %d' % common
    return None, None


def measure():
    data = json.load(open(DATA, encoding='utf-8'))
    idx = index_base(data['deals'])
    self_found = other = 0
    others = []
    for d in data['deals']:
        item = {'title': d.get('title'), 'date': d.get('date'), 'url': None}
        found, why_ = match(item, [r for r in idx if r['id'] != d['id']])
        if found:
            other += 1
            others.append((d['id'], found, why_, str(d.get('title'))[:70]))
        found_self, _ = match(item, idx)
        if found_self == d['id']:
            self_found += 1
    print('ПОЛНОТА: %d из %d заголовков находят сами себя (%.1f%%)'
          % (self_found, len(data['deals']), 100.0 * self_found / len(data['deals'])))
    print('СКЛЕЙКИ: %d заголовков находят ЧУЖУЮ карточку (%.1f%%) — это либо будущие '
          'ложные склейки, либо настоящие дубли базы' % (other, 100.0 * other / len(data['deals'])))
    for row in others[:15]:
        print('   %s -> %s (%s)\n     %s' % row)


if __name__ == '__main__':
    if '--measure' in sys.argv:
        measure()
    else:
        print(__doc__)
