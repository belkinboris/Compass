# -*- coding: utf-8 -*-
"""Показать в консоли заново то, что ждет решения, — чтобы было куда нажать (17 ноября 2026).

Владелец: «Отправь нам в консоль что что ждет» и «когда в личку приходит пост,
что мы не приняли решение, одновременно должен снова в консоли показываться то,
по чему мы не приняли решение, чтобы мы смогли ткнуть». Старое сообщение с
кнопками к этому времени уехало в ленте на сутки вверх.

ЧТО СЧИТАЕТСЯ ЖДУЩИМ:
  * карточка предпросмотра, показанная и без решения (`remind_undecided.waiting`,
    вид card) — заново тем же путем, что `send_drafts.py --resend`;
  * пост об этапе сделки (вид milestone) — проект поста с его кнопками;
  * карточка, которая уже на сайте, а первый пост ждет «📣 Пост в канал»
    (`send_telegram.py`, строка «Ждут кнопки…») — проект поста с кнопками.
Месячная сводка заново не показывается: у нее свой показ в send_telegram.py.

Вызывают: `remind_undecided.py` — для того, о чем только что напомнил в личку,
и человек руками:

    python3 pipeline/publish/reshow_waiting.py            # сухой прогон: что ждет
    python3 pipeline/publish/reshow_waiting.py --write    # показать все заново
    python3 pipeline/publish/reshow_waiting.py --only card:<id> milestone:<id> post:<id> --write
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
AGAIN = '🔁 Напоминаем: решения еще нет, кнопки под этим сообщением.\n'


def awaiting_post_ids(run=None):
    """[id] карточек базы, чей первый пост ждет кнопки, — как их называет сухой
    send_telegram.py (одно место правды: условий там много, свой разбор разошелся бы)."""
    out = (run or (lambda: subprocess.run(
        [sys.executable, os.path.join(HERE, 'send_telegram.py')],
        capture_output=True, text=True, cwd=ROOT, timeout=600).stdout))()
    m = re.search(r'Ждут кнопки «Пост в канал» в консоли: \d+ — (.+)', out or '')
    return [x.strip() for x in m.group(1).split(',') if x.strip()] if m else []


def all_waiting(data, cards, decisions, now, post_ids=None):
    """[ключ]: card:<id>, milestone:<id события>, post:<id>."""
    import remind_undecided
    keys = [it['key'] for it in remind_undecided.waiting(data, cards, decisions, now)
            if it['kind'] in ('card', 'milestone')]
    return keys + ['post:%s' % i for i in (awaiting_post_ids() if post_ids is None else post_ids)]


def messages(keys, data):
    """[(ключ, текст, кнопки)] для этапов и постов; карточки предпросмотра идут через --resend."""
    import send_drafts
    import send_milestone_drafts
    comps = data.get('companies') or {}
    deals = {d['id']: d for d in data.get('deals') or []}
    out = []
    for key in keys:
        kind, _, ident = key.partition(':')
        if kind == 'post' and ident in deals:
            card = deals[ident]
            out.append((key, AGAIN + send_drafts.post_message_text(card, comps), send_drafts.post_keyboard(card)))
        elif kind == 'milestone':
            for deal in deals.values():
                for event in deal.get('events') or []:
                    if event.get('id') == ident:
                        out.append((key, AGAIN + send_milestone_drafts.milestone_message(deal, event),
                                    send_milestone_drafts.milestone_keyboard(deal['id'], event['kind'])))
    return out


def run(write=False, only=None, now=None, sender=None, resend=None, post_ids=None):
    """Возвращает список ключей, показанных заново (в сухом прогоне — которые показал бы)."""
    import approve
    import send_drafts
    import console_topics
    now = now or datetime.now(timezone.utc)
    data = json.load(open(DATA, encoding='utf-8'))
    cards = json.load(open(PENDING, encoding='utf-8')).get('cards') or []
    if only is None:
        decisions, handle = approve.fetch_decisions()
        if handle is None:
            print('Решения с сайта не прочитаны — заново не показываю, чтобы не спросить о решенном.')
            return []
        keys = all_waiting(data, cards, decisions, now, post_ids)
    else:
        keys = list(only)
    print('Показать в консоли заново: %d%s' % (len(keys), (' — ' + ', '.join(keys)) if keys else ''))
    if not keys or not write:
        if keys:
            print('Сухой прогон. Отправка — с ключом --write.')
        return keys
    shown = []
    for key in [k for k in keys if k.startswith('card:')]:
        rc = (resend or (lambda cid: send_drafts.main(write=True, resend=cid)))(key[5:])
        if not rc:
            shown.append(key)
    rest = messages([k for k in keys if not k.startswith('card:')], data)
    if rest:
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chats = send_drafts.send_targets()
        if sender is None and not (token and chats):
            print('Нет токена или адреса консоли — посты заново не показаны.')
            return shown
        thread = console_topics.thread_id('decision')
        if thread is None and console_topics.unreachable():
            print('Сайт не ответил, в какую тему слать, — посты заново не показаны.')
            return shown
        if sender is None:
            import httpx
            client = httpx.Client(timeout=20)

            def sender(chat, text, keyboard):
                return send_drafts.send_one(client, token, chat, text, keyboard, thread_id=thread, html=True)
        for i, (key, text, keyboard) in enumerate(rest):
            if i:
                time.sleep(send_drafts.PAUSE)
            if all([sender(chat, text, keyboard) for chat in chats] or [False]):
                shown.append(key)
    print('Показано заново: %d из %d.' % (len(shown), len(keys)))
    return shown


if __name__ == '__main__':
    _only = None
    if '--only' in sys.argv:
        _only = [a for a in sys.argv[sys.argv.index('--only') + 1:] if not a.startswith('--')]
    run(write='--write' in sys.argv, only=_only)
