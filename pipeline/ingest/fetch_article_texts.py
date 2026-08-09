# -*- coding: utf-8 -*-
"""Дозабор ПОЛНЫХ текстов статей-источников для сборки карточки чтением.

ЗАЧЕМ. Лента отдаёт заголовок и короткую аннотацию — замер по сырью за август:
медиана 130 знаков, 87% записей короче 300, у четверти аннотации нет вовсе.
А факты живут в теле статьи: «Прежний собственник — Патвакан Мкртчян»,
«стоимость актива могла составить от 370 млн до 430 млн руб.», оценка завода
«Квант» в 1–1,5 млрд ₽ — ничего из этого в аннотациях не было. Полный текст —
медиана 6383 знака, в ~49 раз больше того, что видит разбор. review.py
принимает правку только с цитатой, дословно лежащей в сыром тексте на диске
(data/inbox/raw), — значит, тело статьи надо забрать и положить туда же, как
обычную запись притока: {'url', 'title', 'summary': <текст без разметки>}.

КТО ЗОВЁТ. С 8 августа — САМ promote.py, сразу после того как карточка прошла
ворота: до этого дозабор был отдельной командой, которую надо было не забыть
запустить, и из 84 карточек притока полный текст был скачан для 13 — карточка
NexTouch/«Квант» два дня простояла с пустыми линзами при 326 КБ текста в
кэше. Ручной запуск по id карточки остался для дочитывания старых карточек
(приоритет G7).

Забираются ТОЛЬКО адреса, уже стоящие в карточках базы или предпросмотра, —
скрипт не источник новых ссылок, а дозагрузка уже известных.

Запуск:
    python3 pipeline/ingest/fetch_article_texts.py <id карточки> [...]  # сухой
    python3 pipeline/ingest/fetch_article_texts.py <id> [...] --write   # записать
"""
import html as html_lib
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
RAW = os.path.join(ROOT, 'data', 'inbox', 'raw')


def article_text(raw_html):
    """Текст без разметки. Скрипты и стили выкидываются целиком: внутри них
    цитат не бывает, а мусора — мегабайты."""
    raw_html = re.sub(r'<script\b.*?</script>|<style\b.*?</style>', ' ',
                      raw_html, flags=re.S | re.I)
    text = html_lib.unescape(re.sub(r'<[^>]+>', ' ', raw_html))
    return re.sub(r'\s+', ' ', text).strip()


def already_fetched():
    """Адреса, чей полный текст уже лежит на диске: второй раз не качаем.

    Без этого повторный прогон promote (перезапуск рутины, ручная проверка)
    скачивал бы те же статьи заново — а поверх лимитов чужих сайтов лучше
    не ходить дважды за тем же."""
    urls = set()
    if not os.path.isdir(RAW):
        return urls
    for name in os.listdir(RAW):
        if not name.endswith('-articles.jsonl'):
            continue
        for line in open(os.path.join(RAW, name), encoding='utf-8'):
            try:
                urls.add(str(json.loads(line).get('url')))
            except ValueError:
                continue
    return urls


def fetch_and_store(targets, write=True):
    """Скачать полные тексты и дописать в data/inbox/raw/<дата>-articles.jsonl.

    `targets` — список (метка, url, заголовок); метка нужна только для отчёта.
    Сетевые ошибки НЕ валят вызывающего: недоступная статья — обычное дело
    (пейволл, защита от роботов), и провал одного адреса не должен останавливать
    ворота. Возвращает (сколько скачано, сколько не вышло)."""
    import urllib.request
    skip = already_fetched()
    out = os.path.join(RAW, '%s-articles.jsonl' % date.today().isoformat())
    records, failed = [], 0
    for label, url, title in targets:
        if url in skip:
            print('  УЖЕ ЕСТЬ  %s %s' % (label, url))
            continue
        skip.add(url)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            body = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
            text = article_text(body)
            if len(text) <= 200:
                raise ValueError('подозрительно короткий текст (%d знаков)' % len(text))
        except Exception as e:
            print('  НЕ ЗАБРАН %s %s (%s)' % (label, url, e))
            failed += 1
            continue
        records.append({'url': url, 'title': title, 'summary': text})
        print('  ЗАБРАН    %s %s (%d знаков)' % (label, url, len(text)))
    if write and records:
        os.makedirs(RAW, exist_ok=True)
        with open(out, 'a', encoding='utf-8') as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return len(records), failed


def card_urls(ids):
    cards = {d['id']: d for d in json.load(open(BASE, encoding='utf-8'))['deals']}
    if os.path.exists(PENDING):
        cards.update({c['id']: c for c in
                      json.load(open(PENDING, encoding='utf-8'))['cards']})
    urls = []
    for cid in ids:
        card = cards.get(cid)
        assert card, 'карточки %s нет ни в базе, ни в предпросмотре' % cid
        for s in card.get('src') or []:
            if len(s) > 1 and str(s[1]).startswith('http'):
                urls.append((cid, str(s[1]), str(card.get('title') or '')))
    return urls


def main(ids, write=False):
    fetched, failed = fetch_and_store(card_urls(ids), write=write)
    if not write:
        print('Сухой прогон: %d статей скачано, %d недоступно. Запись — с ключом --write.'
              % (fetched, failed))
    else:
        print('Дописано: %d записей, недоступно: %d.' % (fetched, failed))
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--write']
    sys.exit(main(args, write='--write' in sys.argv))
