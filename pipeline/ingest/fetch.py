# -*- coding: utf-8 -*-
"""Приток, шаг 1: забрать новые записи из источников.

ЗАЧЕМ ОТДЕЛЬНЫМ ШАГОМ. Сеть — самая ненадёжная часть притока: источник может
лечь, поменять адрес ленты, отдать мусор. Поэтому забор ничего не разбирает и
ничего не решает: он складывает сырые записи в `data/inbox/raw/<дата>.jsonl` и
пишет отчёт, кто ответил, а кто нет. Разбором занимаются `classify.py` и
`match.py` — их можно гонять на сохранённом сырье сколько угодно раз, без сети.

ГДЕ ЭТО РАБОТАЕТ. В среде разработки исходящий доступ к новостным сайтам закрыт
политикой прокси (403 на CONNECT к rbc.ru, kommersant.ru, interfax.ru,
vedomosti.ru — проверено). Поэтому:
  * `--verify` честно проверяет каждую ленту и записывает результат в
    `sources.json` (поле `feed_checked`), чтобы в реестре не осталось
    непроверенных предположений;
  * `--offline` берёт записи из `data/inbox/fixtures/*.xml` — так тесты и
    разбор работают там, где сети нет.
Ни один шаг не притворяется успешным: недоступный источник помечается
недоступным и попадает в отчёт.

ЧТО СЧИТАЕТСЯ ЗАПИСЬЮ. `{source_id, url, title, summary, published, fetched}`.
Ключ дедупликации — `url`: одну и ту же ссылку второй раз не сохраняем.

Запуск:
    python3 pipeline/ingest/fetch.py --offline        # из фикстур, без сети
    python3 pipeline/ingest/fetch.py --verify         # проверить адреса лент
    python3 pipeline/ingest/fetch.py                  # обычный забор (нужна сеть)
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from xml.etree import ElementTree

_unescape = html.unescape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCES = os.path.join(HERE, 'sources.json')
INBOX = os.path.join(ROOT, 'data', 'inbox')
RAW = os.path.join(INBOX, 'raw')
FIXTURES = os.path.join(INBOX, 'fixtures')
UA = 'Mozilla/5.0 (compatible; KompasBot/0.1; +https://kompas.deals)'
TIMEOUT = 20


def load_sources():
    return json.load(open(SOURCES, encoding='utf-8'))['sources']


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def parse_rss(body, source_id):
    """RSS и Atom одним разбором: нам нужны только ссылка, заголовок и дата."""
    out = []
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return out
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    for item in root.iter():
        tag = item.tag.split('}')[-1]
        if tag not in ('item', 'entry'):
            continue
        get = lambda name: (item.findtext(name) or item.findtext('atom:' + name, namespaces=ns) or '')
        link = get('link')
        if not link:
            el = item.find('atom:link', namespaces=ns)
            link = el.get('href') if el is not None else ''
        title = re.sub(r'\s+', ' ', get('title')).strip()
        if not link or not title:
            continue
        out.append({
            'source_id': source_id,
            'url': link.strip(),
            'title': title,
            'summary': re.sub(r'<[^>]+>', ' ', get('description') or get('summary'))[:600].strip(),
            'published': (get('pubDate') or get('published') or get('updated')).strip(),
        })
    return out


MERGERS_RU_BASE = 'https://mergers.ru'
MERGERS_RU_BLOCK = re.compile(
    r'<div class="news_box">\s*<p class="marb_10"><a class="underline" href="([^"]+)">([^<]+)</a></p>\s*'
    r'<p>(.*?)</p>\s*<p class="small cb-mt-5 grey">(\d{2})\.(\d{2})\.(\d{4})<', re.S)


def parse_mergers_ru_news(body, source_id):
    """`/news/` — готовая лента, уже отфильтрованная площадкой под M&A: заметно
    выше сигнал, чем у общих новостных RSS (Коммерсантъ и т. п. отдают всё
    подряд, включая спорт и котировки — см. E9). Разбор регуляркой, а не HTML-
    парсером: структура блока `news_box` простая и стабильная, тянуть парсер
    ради одной страницы незачем."""
    text = body.decode('utf-8', 'ignore') if isinstance(body, bytes) else body
    out = []
    for url, title, summary, dd, mm, yyyy in MERGERS_RU_BLOCK.findall(text):
        clean_summary = re.sub(r'<[^>]+>', ' ', summary)
        clean_summary = _unescape(re.sub(r'\s+', ' ', clean_summary)).strip()[:600]
        out.append({
            'source_id': source_id,
            'url': url if url.startswith('http') else MERGERS_RU_BASE + url,
            'title': _unescape(title).strip(),
            'summary': clean_summary,
            'published': '%s-%s-%s' % (yyyy, mm, dd),
        })
    return out


def parse_telegram(body, source_id):
    """Веб-зеркало канала t.me/s/<канал>: посты лежат в div-ах с классом
    tgme_widget_message_text. Разбираем регулярками, а не HTML-парсером, чтобы
    не тянуть зависимость: структура зеркала простая и меняется редко."""
    text = body.decode('utf-8', 'ignore') if isinstance(body, bytes) else body
    out = []
    for m in re.finditer(
            r'<a class="tgme_widget_message_date" href="([^"]+)"[^>]*>.*?'
            r'<time datetime="([^"]+)"', text, re.S):
        out.append({'source_id': source_id, 'url': m.group(1), 'published': m.group(2),
                    'title': '', 'summary': ''})
    bodies = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', text, re.S)
    for i, raw in enumerate(bodies):
        plain = re.sub(r'<[^>]+>', ' ', raw)
        plain = re.sub(r'\s+', ' ', plain).strip()
        if i < len(out):
            out[i]['title'] = plain[:200]
            out[i]['summary'] = plain[:600]
    return [x for x in out if x['title']]


def fetch_source(src, offline=False):
    """(записи, ошибка). Ошибка — строка; успех — None."""
    feed = src.get('feed')
    if not feed:
        return [], 'ленты нет — нужен разбор страницы'
    if offline:
        path = os.path.join(FIXTURES, src['id'].replace(':', '_') + '.xml')
        if not os.path.exists(path):
            return [], 'нет фикстуры %s' % os.path.basename(path)
        body = open(path, 'rb').read()
    else:
        try:
            body = http_get(feed)
        except urllib.error.HTTPError as e:
            return [], 'HTTP %s' % e.code
        except Exception as e:                                  # noqa: BLE001
            return [], '%s: %s' % (type(e).__name__, str(e)[:80])
    if src['kind'] == 'telegram':
        items = parse_telegram(body, src['id'])
    elif src['kind'] == 'html_mergers':
        items = parse_mergers_ru_news(body, src['id'])
    else:
        items = parse_rss(body, src['id'])
    return items, None


def seen_urls():
    urls = set()
    if not os.path.isdir(RAW):
        return urls
    for name in os.listdir(RAW):
        if not name.endswith('.jsonl'):
            continue
        for line in open(os.path.join(RAW, name), encoding='utf-8'):
            try:
                urls.add(json.loads(line)['url'])
            except Exception:                                    # noqa: BLE001
                pass
    return urls


def main(argv):
    offline, verify = '--offline' in argv, '--verify' in argv
    sources = load_sources()
    if verify:
        # `--only <id>` — проверить один источник, не трогая last_check у
        # остальных 160: добавляя ленту, незачем перезаписывать дату проверки
        # всему реестру и раздувать diff.
        only = None
        if '--only' in argv:
            i = argv.index('--only')
            only = argv[i + 1] if i + 1 < len(argv) else None
        ok = 0
        for src in sources:
            if not src.get('feed'):
                continue
            if only and src.get('id') != only:
                continue
            items, err = fetch_source(src, offline=False)
            src['feed_checked'] = err is None
            src['last_check'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            src['last_error'] = err
            print('%-28s %s' % (src['id'], 'ок, записей %d' % len(items) if not err else 'НЕТ: ' + err))
            ok += (err is None)
        json.dump({'sources': sources}, open(SOURCES, 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False)
        print('\nЛент отвечает: %d из %d' % (ok, sum(1 for s in sources if s.get('feed'))))
        return

    os.makedirs(RAW, exist_ok=True)
    known = seen_urls()
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(RAW, day + '.jsonl')
    added, errors = 0, []
    with open(path, 'a', encoding='utf-8') as f:
        for src in sources:
            if not src.get('enabled'):
                continue
            items, err = fetch_source(src, offline=offline)
            if err:
                errors.append((src['id'], err))
                continue
            for item in items:
                if item['url'] in known:
                    continue
                known.add(item['url'])
                item['fetched'] = day
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                added += 1
    print('Новых записей: %d -> %s' % (added, os.path.relpath(path, ROOT)))
    print('Источников с ошибкой: %d' % len(errors))
    for sid, err in errors[:15]:
        print('   %-28s %s' % (sid, err))


if __name__ == '__main__':
    main(sys.argv[1:])
