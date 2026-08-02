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

ЗАЩИТА ОТ ПЕРВОГО ЗАПУСКА (найдено аудитом 1 августа, не дожидаясь, пока
это случится по-настоящему). `telegram_posts` пока пуст, а `to_send` берёт
ЛЮБУЮ ещё не отправленную сделку — без ограничения это были бы все карточки
базы разом. Решение владельца (2 августа): бэклог НЕ публикуется вообще —
канал начинает жизнь с сегодняшнего дня, старые карточки не в счёт.
Механика — `seed_telegram_posts_backlog.py` заполняет `telegram_posts`
значением `null` для всех сделок, существующих на момент включения канала;
такая запись означает «в счёт бэклога, не публиковать и не редактировать
эту карточку» (без `null` защита — только ограничитель СКОРОСТИ, а не
решение, ЧТО публиковать). За один прогон дополнительно уходит не больше
`TELEGRAM_MAX_SENDS_PER_RUN` НОВЫХ постов (по умолчанию 20, с паузой
`TELEGRAM_SEND_DELAY_S` между ними, по умолчанию 1,2 с) — двойная защита:
бэклог не отправится в принципе, а если счёт «новых» карточек всё равно
однажды окажется большим (например, ретроспективно исправили дату у пачки
старых карточек и они перестали быть бэклогом), скорость всё равно
ограничена. Правки уже опубликованных постов делят тот же общий лимит.

Запуск:
    python3 pipeline/publish/send_telegram.py              # сухой прогон
    python3 pipeline/publish/send_telegram.py --write      # отправить и записать id
"""
import json
import os
import sys
import time
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
MAX_SENDS_PER_RUN = int(os.environ.get('TELEGRAM_MAX_SENDS_PER_RUN', '20'))
SEND_DELAY_S = float(os.environ.get('TELEGRAM_SEND_DELAY_S', '1.2'))


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
    doc = json.load(open(os.path.join(UPDATES_DIR, names[-1]), encoding='utf-8'))
    rows = doc.get('updates', [])
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
            # `null` — сделка засеяна как бэклог (см. seed_telegram_posts_backlog.py):
            # решение владельца — не публиковать историю, начинаем с сегодняшнего
            # дня. У таких записей нет настоящего message_id, поэтому и правки
            # для них не готовим — не по забывчивости, а чтобы не пытаться
            # редактировать несуществующее сообщение.
            if not posts[did]:
                continue
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

    # Лимит и пауза — см. docstring («защита от первого запуска»). Правки
    # делят лимит с новыми постами: считаем оба списка одной очередью, а не
    # отдельными лимитами каждый, иначе включённая одновременно куча правок
    # обойдёт защиту с другой стороны.
    queue = [('send', did, text) for did, text in to_send] + \
            [('edit', did, (mid, text)) for did, mid, text in to_edit]
    batch, rest = queue[:MAX_SENDS_PER_RUN], queue[MAX_SENDS_PER_RUN:]
    if rest:
        print('Лимит за прогон: %d. В очереди ещё %d — доберём в следующих прогонах.'
              % (MAX_SENDS_PER_RUN, len(rest)))

    client = _client()
    sent, edited, failed = 0, 0, []
    for i, (kind, did, payload) in enumerate(batch):
        if i:
            time.sleep(SEND_DELAY_S)
        try:
            if kind == 'send':
                posts[did] = post_message(client, token, chat_id, payload)
                sent += 1
            else:
                mid, text = payload
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
