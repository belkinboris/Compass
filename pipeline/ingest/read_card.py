# -*- coding: utf-8 -*-
"""Карточка и тело её статьи одним куском — для шага дочитывания.

ЗАЧЕМ. Замер кампании 9 августа: четыре потока прочитали 175 карточек и
израсходовали 73,4 млн токенов чтения кэша — 615 тыс. токенов НА КАРТОЧКУ при
том, что сама работа (прочитать статью, внести правки) стоит ~4 тыс. Разница
уходила не на работу: поток открывал `data/inbox/raw/<дата>-articles.jsonl`
целиком (файлы по 300 КБ и больше, у изданий 60–80% выгрузки — навигация,
меню, списки «читайте также») и тащил всё это в контекст, где оно потом
перечитывалось на каждом следующем ходу. При стоимости Opus это ~1 доллар за
карточку и ~1100 долларов за оставшуюся очередь — вдвое больше названного
владельцем предела.

ЧТО ДЕЛАЕТ. Печатает ровно то, что нужно для решения: текущее состояние полей
карточки (чтобы видеть, что уже заполнено и что заполнено НЕВЕРНО) и тело
статьи без навигации, обрезанное по мере. Ничего не пишет.

ПОЧЕМУ ОБРЕЗКА НЕ ЛОМАЕТ ДОСЛОВНОСТЬ. `review.py` требует, чтобы цитата
дословно лежала в сыром тексте на диске. Мы не переписываем текст, а берём
его ПОДСТРОКУ: пробелы в кэше уже нормализованы `article_text()` при записи,
поэтому любой кусок напечатанного здесь остаётся дословным куском сырья.

Запуск:
    python3 pipeline/ingest/read_card.py <id> [<id> ...]   # карточки и статьи
    python3 pipeline/ingest/read_card.py --queue 2024 20   # очередь года
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
RAW = os.path.join(ROOT, 'data', 'inbox', 'raw')

# Мера тела статьи. Первая версия стояла на 14 тыс. знаков — и замер по кэшу
# показал, что под обрез попадает каждая пятнадцатая статья (6,7%), а хвост
# срезался в отдельных случаях на 10 тыс. знаков. Это неверный размен: экономия
# бралась не здесь. Дорого стоило то, что поток открывал ФАЙЛ СЫРЬЯ целиком —
# сотни записей по 300 КБ, — а одна статья это медиана 6,4 тыс. знаков, то есть
# около 2 тыс. токенов. Даже самая длинная статья дешевле любого пропущенного
# факта: ради экономии в тысячу токенов можно потерять сумму сделки.
LIMIT = 40000

# Хвост статьи: с этих слов начинается то, что к сделке отношения не имеет.
TAIL = re.compile(
    r'(Читайте также|Читайте нас в|Подписывайтесь|Подписаться на|'
    r'Все права защищены|Материалы по теме|Самое читаемое|Новости партнеров|'
    r'Мы в соцсетях|Поделиться в|Оставить комментарий|Сообщить об опечатке)',
    re.I)

# Голова статьи: последний маркер конца навигации. Берём ПОСЛЕДНИЙ, потому что
# «Главная /» встречается и в подвале — а нам нужен тот, за которым начался текст.
HEAD = re.compile(r'(Главная\s*/|Главная\s*»|Хлебные крошки|Новости\s*/)', re.I)

FIELDS = ('date', 'type', 'ind', 'status', 'asset', 'buyer', 'buyer_name',
          'seller', 'seller_name', 'target', 'sum')
LENS = ('eco.share', 'eco.sum', 'eco.val', 'eco.context', 'eco.rationale',
        'eco.target_fin', 'eco.finadv', 'law.struct', 'law.appr', 'law.terms',
        'law.adv')


def cards():
    """Все карточки, где может лежать id: база и очередь предпросмотра.

    Очередь — тоже уже описанные сделки, и дочитывание касается их наравне с
    базой (тот же урок, что у ворот притока: множеств больше одного)."""
    out = {}
    for path, where in ((BASE, 'база'), (PENDING, 'предпросмотр')):
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding='utf-8'))
        for card in (data.get('deals') if isinstance(data, dict) else data) or []:
            if isinstance(card, dict) and card.get('id'):
                out[card['id']] = (card, where)
    return out


def texts():
    """Адрес -> полный текст статьи из кэша притока."""
    out = {}
    if not os.path.isdir(RAW):
        return out
    for name in sorted(os.listdir(RAW)):
        if not name.endswith('-articles.jsonl'):
            continue
        for line in open(os.path.join(RAW, name), encoding='utf-8'):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            body = str(rec.get('summary') or '')
            # Один адрес мог быть забран дважды; берём тот текст, что длиннее —
            # короткий обычно обрывок страницы, отданный с ошибкой.
            if len(body) > len(out.get(str(rec.get('url')), '')):
                out[str(rec.get('url'))] = body
    return out


def body(text):
    """Тело статьи: без навигации в начале и без обвязки в конце."""
    head = None
    for m in HEAD.finditer(text[:len(text) // 2]):
        head = m
    if head:
        text = text[head.end():]
    # Хвост режем ТОЛЬКО в последней трети. «Читайте также» встречается и
    # посреди статьи — врезкой между абзацами, — и правило без этой оговорки
    # срезало до 10 тыс. знаков тела вместе с обвязкой. Пусть лучше в вывод
    # попадёт лишний подвал, чем пропадёт абзац с суммой.
    tail = TAIL.search(text, max(400, (2 * len(text)) // 3))
    if tail:
        text = text[:tail.start()]
    text = text.strip()
    if len(text) > LIMIT:
        text = text[:LIMIT] + '\n… [обрезано по мере; полный текст — в кэше]'
    return text


def dig(card, path):
    node = card
    for part in path.split('.'):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def show(cid, card, where, cache):
    print('=' * 72)
    print('%s   [%s]%s' % (cid, where, '   ПРОЧИТАНА ' + str(card['reviewed'])
                           if card.get('reviewed') else ''))
    print(card.get('title') or '—')
    print('-' * 72)
    for key in FIELDS:
        val = card.get(key)
        if val not in (None, '', []):
            print('  %-12s %s' % (key, val))
    for key in LENS:
        val = dig(card, key)
        if val in (None, '', '—'):
            continue
        val = str(val)
        print('  %-12s %s' % (key, val if len(val) < 300 else val[:300] + '…'))
    extra = str(card.get('extra') or '')
    if extra:
        print('  %-12s %s' % ('extra', extra if len(extra) < 600
                              else extra[:600] + '…'))
    print('-' * 72)
    found = False
    for _label, url in (card.get('src') or []):
        url = str(url)
        if not url.startswith('http'):
            continue
        text = cache.get(url)
        if not text:
            print('  ИСТОЧНИК БЕЗ ТЕКСТА: %s' % url)
            print('  (сначала: python3 pipeline/ingest/fetch_article_texts.py '
                  '%s --write)' % cid)
            continue
        found = True
        print('  ИСТОЧНИК: %s' % url)
        print()
        print(body(text))
        print()
    if not found:
        print('  Текста статьи нет ни по одному адресу.')


def queue(year, limit):
    """Очередь дочитывания своего года: непрочитанные, свежие первыми."""
    data = json.load(open(BASE, encoding='utf-8'))
    rows = []
    for card in data['deals']:
        m = re.match(r'^(\d{4})', str(card.get('date') or ''))
        if not m or int(m.group(1)) != year or card.get('reviewed'):
            continue
        if not any(str(u).startswith('http') for _l, u in (card.get('src') or [])):
            continue
        rows.append(card)
    rows.sort(key=lambda c: str(c.get('date')), reverse=True)
    print('Непрочитанных за %d: %d' % (year, len(rows)))
    for card in rows[:limit]:
        print('%s  %s  %s' % (card['id'], card.get('date'),
                              (card.get('title') or '')[:90]))


def main(argv):
    if argv[:1] == ['--queue']:
        queue(int(argv[1]), int(argv[2]) if len(argv) > 2 else 25)
        return 0
    if not argv:
        print(__doc__)
        return 1
    known, cache = cards(), texts()
    for cid in argv:
        if cid not in known:
            print('%s — такой карточки нет ни в базе, ни в предпросмотре' % cid)
            continue
        card, where = known[cid]
        show(cid, card, where, cache)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
