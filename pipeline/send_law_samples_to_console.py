# -*- coding: utf-8 -*-
"""Выборка карточек с юридическими условиями сделки — в тему «Админ» консоли.

Просьба владельца 23 сентября 2026: «скинь примерно 30 рандомных примеров
наших карточек, где есть юридические условия сделки, чтобы мы смогли их
проверить лично». Это не отчёт и не очередь — материал для ручной вычитки
вдвоём, поэтому сообщение простое: ссылка, заголовок и само условие.

Выборка СЛУЧАЙНАЯ с фиксированным зерном (--seed), чтобы её можно было
повторить или, наоборот, взять другую: смысл проверки в том, чтобы никто —
ни я, ни владелец — не выбирал удобные примеры.

    python3 pipeline/send_law_samples_to_console.py            # сухой прогон
    python3 pipeline/send_law_samples_to_console.py --write
    python3 pipeline/send_law_samples_to_console.py --write --seed 42 -n 30
"""
from __future__ import annotations

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(HERE, 'ingest'), os.path.join(HERE, 'publish')):
    if p not in sys.path:
        sys.path.insert(0, p)

import console_topics                                    # noqa: E402
from send_drafts import send_one, PAUSE                  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SITE = 'https://projectcompass.ru/#/deal/%s'
MIN_YEAR = 2022


def cut(text, limit=600):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def render(i, total, card):
    law = card.get('law') or {}
    lines = ['%d/%d · %s' % (i, total, SITE % card['id']),
             (card.get('title') or '').strip(),
             '']
    for field, label in (('terms', 'Условия'), ('struct', 'Как устроена сделка'),
                         ('appr', 'Согласования')):
        val = cut(law.get(field))
        if val and val != '—':
            lines.append('%s: %s' % (label, val))
    return '\n'.join(lines)


def main(argv):
    write = '--write' in argv
    seed = 20260923
    count = 30
    for i, a in enumerate(argv):
        if a == '--seed' and i + 1 < len(argv):
            seed = int(argv[i + 1])
        if a in ('-n', '--count') and i + 1 < len(argv):
            count = int(argv[i + 1])

    base = json.load(open(DATA, encoding='utf-8'))
    pool = [d for d in base['deals']
            if int(str(d.get('date') or '0')[:4] or 0) >= MIN_YEAR
            and str((d.get('law') or {}).get('terms') or '').strip() not in ('', '—')]
    print('карточек с условиями сделки (с %d года): %d' % (MIN_YEAR, len(pool)))
    if not pool:
        return 0

    random.Random(seed).shuffle(pool)
    picked = pool[:count]
    print('в выборке: %d (зерно %d)' % (len(picked), seed))
    print()
    for i, card in enumerate(picked, 1):
        print(render(i, len(picked), card))
        print('-' * 60)

    if not write:
        print('\nСухой прогон. Отправить: --write')
        return 0

    bot = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = console_topics.console_chats()
    thread = console_topics.thread_id('admin')
    if not bot or not chats:
        print('Отправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.')
        return 1
    if thread is None:
        print('Тема «Админ» не отвечает номером — сообщения уйдут в общую ленту группы.')

    import time
    import httpx
    head = ('Выборка для ручной проверки: %d случайных карточек, где записаны '
            'юридические условия сделки. Всего таких карточек в базе %d. '
            'Выборка случайная (зерно %d) — чтобы никто не выбирал удобные примеры.'
            % (len(picked), len(pool), seed))
    sent = 0
    with httpx.Client(timeout=30) as client:
        ok = all(send_one(client, bot, chat, head, None, thread) for chat in chats)
        print('шапка: %s' % ('отправлена' if ok else 'НЕ ДОШЛА'))
        for i, card in enumerate(picked, 1):
            text = render(i, len(picked), card)
            ok = all(send_one(client, bot, chat, text, None, thread) for chat in chats)
            print('  %s %s' % ('отправлено' if ok else 'НЕ ДОШЛО', card['id']))
            sent += 1 if ok else 0
            if i < len(picked):
                time.sleep(PAUSE)
    print('\nИТОГ ПРОГОНА: отправлено %d из %d.' % (sent, len(picked)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
