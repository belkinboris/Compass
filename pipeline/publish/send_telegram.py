#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приток, шаг 4: действительно отправить пост в Telegram.

ЧТО БЫЛО. `format_post.py` уже год собирает текст поста, решает, обновление
это или новая сделка, и решает, будить ли читателя, — но сам НИЧЕГО не
отправляет (это написано прямо в его docstring). Отправлять было нечем: сеть к
источникам была закрыта политикой прокси, а токена бота не было. 31 июля
проверено, что исходящая сеть в этой среде работает (api.telegram.org отвечает
302 на корень — обычное поведение); этот файл — недостающий последний шаг.

ОДНА СДЕЛКА — ОДИН ПОСТ. Карточка получает пост один раз (`sendMessage`), и
дальше он РЕДАКТИРУЕТСЯ (`editMessageText`), а не дублируется: правило из
`enrich.py`/`format_post.py`, здесь оно наконец реализовано по сети. Связь
«сделка -> id сообщения в канале» хранится в `deals_promoted.json` в поле
верхнего уровня `telegram_posts` (тот же приём, что `merged`/`merged_deal_stages`
— словарь рядом с данными, а не отдельный файл, который может разъехаться).

ЧТО НУЖНО ДЛЯ ЗАПУСКА. Переменные окружения:
    TELEGRAM_BOT_TOKEN     — токен бота от @BotFather
    TELEGRAM_CHANNEL_ID    — куда постить: @username канала или числовой id
Без них скрипт не падает и не притворяется, что отправил, — печатает, что
отправил бы, и останавливается (тот же принцип, что у auth.py с SMTP: без
настройки — честный лог, а не тихая имитация успеха).

ЧТО СЧИТАЕТСЯ «НОВЫМ ДЛЯ ОТПРАВКИ». Сделка, отсутствующая в `telegram_posts`,
у которой есть хотя бы предмет ИЛИ сумма (пустой заголовок без единого факта
отправлять незачем). Черновики (`data/inbox/drafts/`) сюда не попадают —
только то, что уже прошло `promote.py` и реально в базе.

ЧТО СЧИТАЕТСЯ «ОБНОВЛЕНИЕМ». Сделка, которая уже есть в `telegram_posts` И
попала в `data/inbox/updates/<дата>.json` от `enrich.py` с непустым списком
изменений. Правится тот же пост; строка «⟳ Обновлено: …» видна прямо в тексте
(`format_post.render(..., updates=...)`), отдельного уведомления в канал не
шлём — `format_post.should_notify()` решает это для будущего личного
уведомления пользователю, не для канала.

ГРАНИЦА. Скрипт не решает, ЧТО писать, — это `format_post.py`. Он только
довозит готовый текст до Telegram Bot API и запоминает id сообщения.

Запуск:
    python3 pipeline/publish/send_telegram.py              # сухой прогон
    python3 pipeline/publish/send_telegram.py --write      # отправить и записать id
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import format_post  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
UPDATES_DIR = os.path.join(ROOT, 'data', 'inbox', 'updates')
API_BASE = 'https://api.telegram.org/bot%s/%s'


class TelegramError(Exception):
    pass


def _client():
    import httpx
    return httpx.Client(timeout=20.0)


def post_message(client, token, chat_id, text):
    r = client.post(API_BASE % (token, 'sendMessage'), json={
        'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True,
    })
    body = r.json()
    if not body.get('ok'):
        raise TelegramError('sendMessage: %s' % (body.get('description') or r.text[:200]))
    return body['result']['message_id']


def edit_message(client, token, chat_id, message_id, text):
    r = client.post(API_BASE % (token, 'editMessageText'), json={
        'chat_id': chat_id, 'message_id': message_id, 'text': text,
        'parse_mode': 'HTML', 'disable_web_page_preview': True,
    })
    body = r.json()
    if not body.get('ok'):
        # "message is not modified" — Telegram считает правкой даже пробел;
        # повторная отправка того же текста не должна валить весь прогон.
        if 'not modified' in str(body.get('description', '')).lower():
            return
        raise TelegramError('editMessageText: %s' % (body.get('description') or r.text[:200]))


def load_today_updates():
    """{deal_id: [изменения]} из самого свежего файла data/inbox/updates/."""
    if not os.path.isdir(UPDATES_DIR):
        return {}
    names = sorted(os.listdir(UPDATES_DIR))
    if not names:
        return {}
    rows = json.load(open(os.path.join(UPDATES_DIR, names[-1]), encoding='utf-8'))
    return {row['deal_id']: row.get('changes', []) for row in rows if row.get('changes')}


def sendable(deal):
    return format_post.has(deal.get('sum')) or (deal.get('seller') or deal.get('seller_id')) \
        or (deal.get('target') or deal.get('asset') or deal.get('asset_id'))


def main(write):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID', '')
    data = json.load(open(DATA, encoding='utf-8'))
    posts = data.setdefault('telegram_posts', {})
    comps = data['companies']
    updates_by_id = load_today_updates()

    to_send, to_edit = [], []
    for deal in data['deals']:
        did = deal['id']
        if did in posts:
            changes = updates_by_id.get(did)
            if changes:
                text = format_post.render(deal, comps, updates=changes)
                to_edit.append((did, posts[did], text))
        elif sendable(deal):
            text = format_post.render(deal, comps)
            to_send.append((did, text))

    print('Новых постов: %d, правок существующих: %d' % (len(to_send), len(to_edit)))
    if not token or not chat_id:
        print('TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID не заданы — не отправляю, только показываю план.')
        for did, text in to_send[:3]:
            print('\n--- новый пост: %s ---\n%s' % (did, text[:400]))
        for did, _mid, text in to_edit[:3]:
            print('\n--- правка поста: %s ---\n%s' % (did, text[:400]))
        return

    if not write:
        print('Сухой прогон с настоящим токеном: не отправляю. Запись — с ключом --write.')
        return

    client = _client()
    sent, edited, failed = 0, 0, []
    for did, text in to_send:
        try:
            mid = post_message(client, token, chat_id, text)
            posts[did] = mid
            sent += 1
        except TelegramError as e:
            failed.append((did, str(e)))
    for did, mid, text in to_edit:
        try:
            edit_message(client, token, chat_id, mid, text)
            edited += 1
        except TelegramError as e:
            failed.append((did, str(e)))

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Отправлено новых: %d, отредактировано: %d, ошибок: %d' % (sent, edited, len(failed)))
    for did, err in failed:
        print('  %s: %s' % (did, err))


if __name__ == '__main__':
    main('--write' in sys.argv)
