# -*- coding: utf-8 -*-
"""Дозабор ПОЛНЫХ текстов статей-источников для проверки чтением.

ЗАЧЕМ. Лента отдаёт заголовок и короткую аннотацию, а факты живут в теле
статьи: «Прежний собственник — Патвакан Мкртчян» и «стоимость актива могла
составить от 370 млн до 430 млн руб.» в аннотациях не было вовсе — владелец
нашёл оба факта глазами в самих статьях. review.py принимает правку только
с цитатой, дословно лежащей в сыром тексте на диске (data/inbox/raw), —
значит, тело статьи надо забрать и положить туда же, как обычную запись
притока: {'url', 'title', 'summary': <текст статьи без разметки>}.

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
    import urllib.request
    out = os.path.join(RAW, '%s-articles.jsonl' % date.today().isoformat())
    records = []
    for cid, url, title in card_urls(ids):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            body = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
        except Exception as e:
            print('  НЕ ЗАБРАН %s %s (%s)' % (cid, url, e))
            continue
        text = article_text(body)
        assert len(text) > 200, 'подозрительно короткий текст: %s' % url
        records.append({'url': url, 'title': title, 'summary': text})
        print('  ЗАБРАН    %s %s (%d знаков)' % (cid, url, len(text)))
    if not write:
        print('Сухой прогон: %d статей. Запись — с ключом --write.' % len(records))
        return 0
    os.makedirs(RAW, exist_ok=True)
    with open(out, 'a', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print('Дописано в %s: %d записей.' % (out, len(records)))
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--write']
    sys.exit(main(args, write='--write' in sys.argv))
