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
отправлять незачем); либо бэклог-карточка (`posts[did]` — `null`), у которой
появился новый факт (см. ниже) — для неё это тоже первая настоящая отправка.
Черновики (`data/inbox/drafts/`) сюда не попадают — только то, что уже
прошло `promote.py` и реально в базе.

ЧТО СЧИТАЕТСЯ «ОБНОВЛЕНИЕМ». Сделка, у которой уже есть настоящий
message_id в `telegram_posts` (не `null`) И которая попала в
`data/inbox/updates/<дата>.json` от `enrich.py` с непустым списком
изменений. Правится тот же пост; строка «⟳ Обновлено: …» видна прямо в тексте
(`format_post.render(..., updates=...)`), отдельного уведомления в канал не
шлём — `format_post.should_notify()` решает это для будущего личного
уведомления пользователю, не для канала. Тот же новый факт у бэклог-карточки
(`posts[did]` — `null`) — это не правка, а первая отправка (см. выше).

ГРАНИЦА. Скрипт не решает, ЧТО писать, — это `format_post.py`. Он только
довозит готовый текст до Telegram Bot API и запоминает id сообщения.

ЗАЩИТА ОТ ПЕРВОГО ЗАПУСКА (найдено аудитом 1 августа, не дожидаясь, пока
это случится по-настоящему). `telegram_posts` пока пуст, а `to_send` берёт
ЛЮБУЮ ещё не отправленную сделку — без ограничения это были бы все карточки
базы разом. Решение владельца (2 августа): текущий бэклог НЕ публикуется
разом при включении канала — канал начинает жизнь с сегодняшнего дня, а не
с трёхлетней историей рынка постами один за другим. Механика —
`seed_telegram_posts_backlog.py` заполняет `telegram_posts` значением `null`
для всех сделок, существующих на момент включения канала; такая запись
значит «пока не публиковалась», а не «никогда не будет». Уточнение
владельца (тот же день): если у бэклог-карточки позже появится настоящий
НОВЫЙ факт (`data/inbox/updates/` от `enrich.py`, непустой `changes`) — это
не «трогать старую карточку нельзя», а именно решение не вываливать в канал
то, что на сайте уже лежит СЕЙЧАС; новый факт публикуется как обычный
первый пост (без «⟳ Обновлено» — сравнивать не с чем, читатель видит
карточку впервые), и `posts[did]` перестаёт быть `null`. За один прогон
дополнительно уходит не больше `TELEGRAM_MAX_SENDS_PER_RUN` постов (по
умолчанию 20, с паузой `TELEGRAM_SEND_DELAY_S` между ними, по умолчанию
1,2 с) — двойная защита: бэклог без нового факта не отправится в принципе,
а если счёт «новых» карточек всё равно однажды окажется большим (например,
ретроспективно исправили дату у пачки старых карточек и они перестали быть
бэклогом), скорость всё равно ограничена. Правки уже опубликованных постов
делят тот же общий лимит.

РАВНОМЕРНАЯ ВЫДАЧА (решение владельца 4 августа). Найденное за прогон не
уходит в канал одной пачкой: посты раскладываются на дневное окно
`TELEGRAM_WINDOW` (по умолчанию 10:00–19:00 МСК). Ночью новые посты не
отправляются вовсе — никого не будим; правки уже опубликованных постов идут
всегда, `editMessageText` уведомления не даёт. Подробности расчёта — у
`pace_allowance()`.

Запуск:
    python3 pipeline/publish/send_telegram.py              # сухой прогон
    python3 pipeline/publish/send_telegram.py --write      # отправить свою долю
    python3 pipeline/publish/send_telegram.py --write --now  # отправить всё сразу
"""
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import format_post  # noqa: E402
import telegram_endpoint  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
UPDATES_DIR = os.path.join(ROOT, 'data', 'inbox', 'updates')
MAX_SENDS_PER_RUN = int(os.environ.get('TELEGRAM_MAX_SENDS_PER_RUN', '20'))
SEND_DELAY_S = float(os.environ.get('TELEGRAM_SEND_DELAY_S', '1.2'))
# Пауза между НОВЫМИ постами внутри одного прогона. Она нужна отдельно от
# `SEND_DELAY_S` (та защищает от лимитов Bot API и меряется секундами): в
# последнем слоте окна уходит весь остаток очереди, и без разведения читатель
# получил бы три уведомления подряд в одну минуту — ровно то, чего мы избегаем
# равномерной выдачей. Правок это не касается: `editMessageText` не уведомляет.
SPREAD_S = float(os.environ.get('TELEGRAM_SPREAD_S', '90'))

# ---------- РАВНОМЕРНАЯ ВЫДАЧА ----------
# Пять постов подряд в одну минуту — это не лента, а спам: читатель получает
# пять уведомлений за десять секунд и отключает канал. Раскладываем найденное
# за прогон на окно дневных часов.
#
# ПОЧЕМУ БЕЗ СОБСТВЕННОГО РАСПИСАНИЯ И БЕЗ ОЖИДАНИЯ ВНУТРИ ПРОЦЕССА. Растянуть
# отправку на девять часов внутри одного запуска нельзя: публикация — последний
# шаг притока, а приток живёт короткой сессией и завершается. Хранить «когда
# опубликовать» отдельным полем тоже не хочется: это второе состояние рядом с
# `telegram_posts`, которое обязано с ним не разъезжаться.
#
# Поэтому расчёт БЕЗ СОСТОЯНИЯ: на каждом прогоне смотрим, сколько прогонов
# ещё осталось до конца окна, и берём ровно свою долю очереди. Пять постов в
# 10:00 при часовом прогоне и окне до 19:00 — это 10 оставшихся прогонов и по
# одному посту за раз; если часть постов не ушла, следующий прогон честно
# пересчитает долю от того, что осталось. Самовосстанавливается: пропущенный
# прогон не копит долг, он просто делится на меньшее число слотов.
MSK = timezone(timedelta(hours=3))          # Москва, перевода часов нет
PUBLISH_WINDOW = os.environ.get('TELEGRAM_WINDOW', '10-19')   # часы по Москве
RUN_EVERY_H = float(os.environ.get('TELEGRAM_RUN_EVERY_H', '1'))


def window_bounds():
    start, end = (int(x) for x in PUBLISH_WINDOW.split('-'))
    assert 0 <= start < end <= 24, 'окно публикации задано неверно: %r' % PUBLISH_WINDOW
    return start, end


def pace_allowance(pending, now=None):
    """Сколько новых постов можно отправить прямо сейчас.

    Возвращает (сколько, пояснение). Ноль — значит «не сейчас»: либо ночь,
    либо очередь пуста. Правок это не касается — `editMessageText` не будит
    читателя, и придерживать исправление факта до утра незачем.
    """
    start, end = window_bounds()
    now = now or datetime.now(MSK)
    hour = now.hour + now.minute / 60.0
    if hour < start or hour >= end:
        return 0, 'вне окна публикации %02d:00–%02d:00 МСК (сейчас %02d:%02d) — держим до утра' % (
            start, end, now.hour, now.minute)
    if not pending:
        return 0, 'очередь пуста'
    slots = int((end - hour) / RUN_EVERY_H) + 1
    per = max(1, int(math.ceil(pending / float(slots))))
    return per, 'окно %02d:00–%02d:00 МСК, впереди прогонов: %d, берём %d из %d' % (
        start, end, slots, min(per, pending), pending)


class TelegramError(Exception):
    pass


def _client():
    import httpx
    return httpx.Client(timeout=20.0)


def post_message(client, token, chat_id, text):
    r = client.post(telegram_endpoint.method_url(token, 'sendMessage'), json={
        'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True,
    })
    body = r.json()
    if not body.get('ok'):
        raise TelegramError('sendMessage: %s' % (body.get('description') or r.text[:200]))
    return body['result']['message_id']


def edit_message(client, token, chat_id, message_id, text):
    r = client.post(telegram_endpoint.method_url(token, 'editMessageText'), json={
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


def main(write, ignore_pace=False):
    """`ignore_pace` — то же, что ключ `--now`, но параметром.

    Нужен тестам: они проверяют лимит сообщений за прогон и правило бэклога, а
    не дневное окно, и без явного обхода темпа проходили бы только с 10 до 19
    по Москве — то есть падали бы по вечерам, ничего при этом не сломавшись."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID', '')
    data = json.load(open(DATA, encoding='utf-8'))
    posts = data.setdefault('telegram_posts', {})
    comps = data['companies']
    updates_by_id = load_today_updates()

    to_send, to_edit, to_seed = [], [], []
    for deal in data['deals']:
        did = deal['id']
        if did in posts:
            if not posts[did]:
                # `null` — сделка засеяна как бэклог (см. seed_telegram_posts_backlog.py):
                # владелец решил не публиковать историю разом, начали с
                # сегодняшнего дня. Это НЕ значит «никогда»: если у бэклог-карточки
                # позже появится настоящий новый факт (enrich.py напишет его в
                # data/inbox/updates/), для читателя это первый пост про эту
                # сделку — отправляем его как новый (без «⟳ Обновлено», сравнивать
                # не с чем), а не молчим вечно и не правим несуществующее сообщение.
                changes = updates_by_id.get(did)
                if changes and sendable(deal):
                    text = format_post.render(deal, comps)
                    to_send.append((did, text))
                continue
            changes = updates_by_id.get(did)
            if changes:
                text = format_post.render(deal, comps, updates=changes)
                to_edit.append((did, posts[did], text))
        elif deal.get('no_post'):
            # Решение модерации «карточка без поста»: сайт получает карточку,
            # канал молчит. Засеваем состояние как бэклог (None) — если позже
            # у сделки появится настоящий новый факт, канал узнает о нём как
            # о новости, а не получит запоздалый первый пост.
            to_seed.append(did)
        elif sendable(deal):
            # Текст, который владелец продиктовал в Telegram при модерации
            # черновика, важнее автоформата — но только для ПЕРВОГО поста:
            # дальнейшие обновления снова собирает format_post.
            text = deal.get('post_override') or format_post.render(deal, comps)
            to_send.append((did, text))

    print('Новых постов: %d, правок существующих: %d, без поста по решению: %d'
          % (len(to_send), len(to_edit), len(to_seed)))
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
    # Равномерная выдача. Ключ `--now` её отключает: он для ручного запуска,
    # когда владелец сам решил опубликовать всё немедленно.
    if ignore_pace or '--now' in sys.argv:
        allow, why = len(to_send), 'ключ --now: равномерная выдача отключена'
    else:
        allow, why = pace_allowance(len(to_send))
    print('Темп: %s' % why)
    held = to_send[allow:]
    to_send = to_send[:allow]
    if held:
        print('Придержано новых постов: %d — уйдут следующими прогонами.' % len(held))
    if not to_send and not to_edit:
        # Засев «без поста» — тоже изменение состояния: не записать его —
        # значит показывать эти карточки в плане каждый прогон заново.
        if to_seed:
            for did in to_seed:
                posts[did] = None
            with open(DATA, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print('Постов нет; засеяно без поста: %d.' % len(to_seed))
        else:
            print('Отправлять сейчас нечего.')
        return

    queue = [('send', did, text) for did, text in to_send] + \
            [('edit', did, (mid, text)) for did, mid, text in to_edit]
    batch, rest = queue[:MAX_SENDS_PER_RUN], queue[MAX_SENDS_PER_RUN:]
    if rest:
        print('Лимит за прогон: %d. В очереди ещё %d — доберём в следующих прогонах.'
              % (MAX_SENDS_PER_RUN, len(rest)))

    client = _client()
    sent, edited, failed = 0, 0, []
    prev_kind = None
    for i, (kind, did, payload) in enumerate(batch):
        if i:
            # Два новых поста подряд разводим по времени, всё остальное —
            # обычной технической паузой.
            time.sleep(SPREAD_S if (kind == 'send' and prev_kind == 'send') else SEND_DELAY_S)
        prev_kind = kind
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

    for did in to_seed:
        posts[did] = None
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Отправлено новых: %d, отредактировано: %d, засеяно без поста: %d, ошибок: %d'
          % (sent, edited, len(to_seed), len(failed)))
    for did, err in failed:
        print('  %s: %s' % (did, err))


if __name__ == '__main__':
    main('--write' in sys.argv)
