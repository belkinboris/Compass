#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Разовый скан архива канала «РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ» (@LawFirms) с 2022 года.

ЗАЧЕМ. Канал никогда не был в реестре источников: на 3 августа 2026 в базе
ровно одна ссылка на него (добавлена вручную в тот же день), тогда как у
@dealsma их 66. Между тем владелец начинал «Компас» именно с этого канала:
консультанты нередко платят за объявление о своём участии в сделке, и часть
сделок публикуется ТОЛЬКО здесь. Значит, за 2022–2026 годы мы гарантированно
пропустили и сделки, и — особенно — имена консультантов.

ГРАНИЦА ПО ДАТЕ. Сайт показывает сделки с 2022 года (тест
`test_pre_2022_deals_hidden_from_site`), поэтому раньше 2022 не идём. Замер
соответствия «номер поста -> дата» (3 августа 2026):
    пост  3980 = 2022-01-07      пост  7999 = 2024-10-11
    пост  4999 = 2022-10-27      пост  8999 = 2025-05-22
    пост  5999 = 2023-07-25      пост  9999 = 2025-12-18
    пост  6999 = 2024-03-15      пост 11223 = 2026-08-02
Отсюда STOP_ID: ниже него посты заведомо старше 2022 года. Точную границу
всё равно ставит дата самого поста, номер — только чтобы знать, где
остановиться.

ПОЧЕМУ НЕ ЧЕРЕЗ fetch.py. Обычный забор берёт последние ~20 постов ленты —
этого хватает для ежедневного притока, но не для разбора архива в 7 тысяч
постов. Это разовая работа: сложить сырьё на диск, дальше его разбирают
обычные шаги притока (triage/match/enrich), а не этот скрипт. Скрипт ничего
не решает и ничего не пишет в базу — ровно как `fetch.py`.

ДЁШЕВО. Ни одного обращения к платной модели: только HTML-страницы
`t.me/s/<канал>?before=<id>`, по ~20 постов на страницу. Прогон резюмируемый —
уже скачанные посты не качаются повторно, поэтому обрыв сети не начинает всё
сначала.

Запуск:
    python3 pipeline/ingest/scan_lawfirms_archive.py            # весь архив с 2022
    python3 pipeline/ingest/scan_lawfirms_archive.py --limit 20 # только 20 страниц
"""
import html
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'data', 'inbox', 'raw', 'lawfirms_archive.jsonl')

CHANNEL = 'LawFirms'
START_ID = 11300      # заведомо выше самого свежего поста
STOP_ID = 3900        # ниже этого номера посты старше 2022 года
DELAY_S = 0.6

POST_RE = re.compile(
    r'data-post="%s/(\d+)".*?'
    r'(?:<time[^>]*datetime="([^"]+)")?'
    r'.*?class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>' % CHANNEL, re.S)
TIME_RE = re.compile(r'datetime="([0-9T:+\-]+)"')


def clean(fragment):
    text = re.sub(r'<br\s*/?>', '\n', fragment)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'[ \t]+', ' ', html.unescape(text)).strip()


def parse_page(page_html):
    """Каждый пост — свой блок; дату берём из <time> внутри того же блока."""
    out = []
    blocks = re.split(r'(?=<div class="tgme_widget_message[ "])', page_html)
    for block in blocks:
        m = re.search(r'data-post="%s/(\d+)"' % CHANNEL, block)
        if not m:
            continue
        body = re.search(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>\s*(?:<div class="tgme_widget_message_(?:footer|reply_markup)|</div>)', block, re.S)
        t = TIME_RE.search(block)
        text = clean(body.group(1)) if body else ''
        out.append({
            'post_id': int(m.group(1)),
            'date': (t.group(1)[:10] if t else None),
            'url': 'https://t.me/%s/%s' % (CHANNEL, m.group(1)),
            'text': text,
        })
    return out


def load_seen():
    seen = {}
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            for line in f:
                try:
                    row = json.loads(line)
                    seen[row['post_id']] = row
                except ValueError:
                    continue
    return seen


def main(limit=None):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    seen = load_seen()
    print('уже скачано постов: %d' % len(seen))

    before = START_ID
    if seen:
        before = min(seen)  # продолжаем с самого старого скачанного
        print('продолжаем с before=%d' % before)

    pages = 0
    added = 0
    with open(OUT, 'a', encoding='utf-8') as f:
        while before > STOP_ID:
            if limit and pages >= limit:
                print('достигнут предел страниц (--limit)')
                break
            url = 'https://t.me/s/%s?before=%d' % (CHANNEL, before)
            try:
                page = subprocess.run(['curl', '-s', '--max-time', '30', url],
                                      capture_output=True, text=True).stdout
            except Exception as e:
                print('сеть: %s — останавливаюсь, прогон резюмируемый' % e)
                break
            rows = parse_page(page)
            pages += 1
            if not rows:
                print('страница before=%d пуста — конец архива или обрыв' % before)
                break
            for row in rows:
                if row['post_id'] not in seen:
                    seen[row['post_id']] = row
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
                    added += 1
            f.flush()
            lo = min(r['post_id'] for r in rows)
            dates = [r['date'] for r in rows if r['date']]
            if pages % 10 == 0 or lo <= STOP_ID:
                print('  страниц %4d | посты до %5d | дата %s | всего %d'
                      % (pages, lo, min(dates) if dates else '?', len(seen)))
            if lo >= before:      # курсор не двигается — защита от вечного цикла
                print('курсор застрял на %d, останавливаюсь' % lo)
                break
            before = lo
            time.sleep(DELAY_S)

    with_text = sum(1 for r in seen.values() if r.get('text'))
    print('\nГОТОВО. Страниц: %d, новых постов: %d, всего в файле: %d (с текстом: %d)'
          % (pages, added, len(seen), with_text))
    print('Сырьё: %s' % OUT)
    return 0


if __name__ == '__main__':
    lim = None
    if '--limit' in sys.argv:
        lim = int(sys.argv[sys.argv.index('--limit') + 1])
    sys.exit(main(limit=lim))
