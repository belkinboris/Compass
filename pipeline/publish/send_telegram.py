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
верхнего уровня `telegram_posts` (тот же прием, что `merged`/`merged_deal_stages`
— словарь рядом с данными, а не отдельный файл, который может разъехаться).

ЧТО НУЖНО ДЛЯ ЗАПУСКА. Одна переменная окружения:
    TELEGRAM_BOT_TOKEN     — токен бота от @BotFather
Куда постить, спрашивать не нужно: адрес канала — не секрет и лежит в
`DEFAULT_CHANNEL` (переопределяется `TELEGRAM_CHANNEL_ID`, если понадобится
тестовый канал). Без токена скрипт не падает и не притворяется, что отправил,
— печатает, что отправил бы, и останавливается (тот же принцип, что у auth.py
с SMTP: без настройки — честный лог, а не тихая имитация успеха).

ЧТО СЧИТАЕТСЯ «НОВЫМ ДЛЯ ОТПРАВКИ». Сделка, отсутствующая в `telegram_posts`,
у которой есть хотя бы предмет ИЛИ сумма (пустой заголовок без единого факта
отправлять незачем); либо бэклог-карточка (`posts[did]` — `null`), у которой
появился новый факт (см. ниже) — для нее это тоже первая настоящая отправка.
Черновики (`data/inbox/drafts/`) сюда не попадают — только то, что уже
прошло `promote.py` и реально в базе.

ЧТО СЧИТАЕТСЯ «ОБНОВЛЕНИЕМ». Сделка, у которой уже есть настоящий
message_id в `telegram_posts` (не `null`) И которая попала в
`data/inbox/updates/<дата>.json` от `enrich.py` с непустым списком
изменений. Правится тот же пост; строка «⟳ Обновлено: …» видна прямо в тексте
(`format_post.render(..., updates=...)`), отдельного уведомления в канал не
шлем — `format_post.should_notify()` решает это для будущего личного
уведомления пользователю, не для канала. Тот же новый факт у бэклог-карточки
(`posts[did]` — `null`) — это не правка, а первая отправка (см. выше).

ГРАНИЦА. Скрипт не решает, ЧТО писать, — это `format_post.py`. Он только
довозит готовый текст до Telegram Bot API и запоминает id сообщения.

ЗАЩИТА ОТ ПЕРВОГО ЗАПУСКА (найдено аудитом 1 августа, не дожидаясь, пока
это случится по-настоящему). `telegram_posts` пока пуст, а `to_send` берет
ЛЮБУЮ еще не отправленную сделку — без ограничения это были бы все карточки
базы разом. Решение владельца (2 августа): текущий бэклог НЕ публикуется
разом при включении канала — канал начинает жизнь с сегодняшнего дня, а не
с трехлетней историей рынка постами один за другим. Механика —
`seed_telegram_posts_backlog.py` заполняет `telegram_posts` значением `null`
для всех сделок, существующих на момент включения канала; такая запись
значит «пока не публиковалась», а не «никогда не будет». Уточнение
владельца (тот же день): если у бэклог-карточки позже появится настоящий
НОВЫЙ факт (`data/inbox/updates/` от `enrich.py`, непустой `changes`) — это
не «трогать старую карточку нельзя», а именно решение не вываливать в канал
то, что на сайте уже лежит СЕЙЧАС; новый факт публикуется как обычный
первый пост (без «⟳ Обновлено» — сравнивать не с чем, читатель видит
карточку впервые), и `posts[did]` перестает быть `null`. За один прогон
дополнительно уходит не больше `TELEGRAM_MAX_SENDS_PER_RUN` постов (по
умолчанию 20, с паузой `TELEGRAM_SEND_DELAY_S` между ними, по умолчанию
1,2 с) — двойная защита: бэклог без нового факта не отправится в принципе,
а если счет «новых» карточек все равно однажды окажется большим (например,
ретроспективно исправили дату у пачки старых карточек и они перестали быть
бэклогом), скорость все равно ограничена. Правки уже опубликованных постов
делят тот же общий лимит.

РАВНОМЕРНАЯ ВЫДАЧА (решение владельца 4 августа). Найденное за прогон не
уходит в канал одной пачкой: посты раскладываются на дневное окно
`TELEGRAM_WINDOW` (по умолчанию 10:00–21:00 МСК). Ночью новые посты не
отправляются вовсе — никого не будим; правки уже опубликованных постов идут
всегда, `editMessageText` уведомления не дает. Подробности расчета — у
`pace_allowance()`.

Запуск:
    python3 pipeline/publish/send_telegram.py              # сухой прогон
    python3 pipeline/publish/send_telegram.py --write      # отправить свою долю
    python3 pipeline/publish/send_telegram.py --write --now  # отправить все сразу
    python3 pipeline/publish/send_telegram.py --write --finish  # всю очередь в этом прогоне, с паузой 20 мин
    python3 pipeline/publish/send_telegram.py --write --skip gX1 gX2
        # П3-10: отправить все, КРОМЕ перечисленных сделок — решение читающего
        # ПОСЛЕ того, как он прочел полные тексты в сухом прогоне (см. ниже),
        # не механическая находка check_post.py. Пропущенные не помечаются
        # отправленными: следующий прогон покажет их снова.
"""
import json
import re
import os
import sys
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))        # console_topics

import approve  # noqa: E402  (fetch_decisions/consume — тот же мост, что у карточек)
import channels  # noqa: E402  (куда идет пост: основной канал, недвижимость или оба)
import console_topics  # noqa: E402
import check_post  # noqa: E402
import format_post
import monthly_digest  # noqa: E402
import review  # noqa: E402  (POSTWORTHY_MILESTONE_KINDS — один список на пайплайн и сайт)
import telegram_endpoint  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
UPDATES_DIR = os.path.join(ROOT, 'data', 'inbox', 'updates')
# АДРЕС КАНАЛА ВЕРНУЛСЯ В ОКРУЖЕНИЕ — ПОТОМУ ЧТО ПОМЕНЯЛСЯ САМ ФАКТ.
# Здесь стоял @username, и стоял сознательно: публикация молчала трое суток
# (4–7 августа), когда `TELEGRAM_CHANNEL_ID` пропала из окружения рутин, а
# @имя публичного канала видит любой подписчик — не секрет, значит, надежнее
# держать его в коде, где оно не потеряется.
#
# 4 сентября 2026 канал сделали ПРИВАТНЫМ (чтобы закрытый тест не привел
# посторонних). У приватного канала @имени нет вовсе: и `sendMessage`, и
# `getChat` по старому имени отвечают «chat not found», публикация встала.
# Постить в него можно — бот там администратор, — но только по ЧИСЛОВОМУ id.
# А этот id, в отличие от @имени, публиковать в открытом репозитории не надо:
# репозиторий публичный, а канал теперь закрытый. Поэтому адрес снова живет
# только в окружении рутин, а здесь пусто — и если его не положили, скрипт
# говорит об этом прямым текстом, а не бьется в мертвое имя.
DEFAULT_CHANNEL = ''
MAX_SENDS_PER_RUN = int(os.environ.get('TELEGRAM_MAX_SENDS_PER_RUN', '20'))
SEND_DELAY_S = float(os.environ.get('TELEGRAM_SEND_DELAY_S', '1.2'))
SITE_POLL_S = 60          # как часто спрашивать сайт при --wait-for-site
# Пауза между НОВЫМИ постами внутри одного прогона. Она нужна отдельно от
# `SEND_DELAY_S` (та защищает от лимитов Bot API и меряется секундами): в
# последнем слоте окна уходит весь остаток очереди, и без разведения читатель
# получил бы три уведомления подряд в одну минуту — ровно то, чего мы избегаем
# равномерной выдачей. Правок это не касается: `editMessageText` не уведомляет.
SPREAD_S = float(os.environ.get('TELEGRAM_SPREAD_S', '90'))
# ПАУЗА 20 МИНУТ МЕЖДУ НОВЫМИ ПОСТАМИ (владелец, 14 октября 2026): «если
# я одобряю одновременно несколько — по 20 минут; но остальные посты должны
# выкладываться как можно быстрее». Поэтому дневной размазки больше нет:
# одобренный пост уходит первым же прогоном, а если их несколько, скрипт
# сам ждет GAP_S между ними (и от последнего поста прошлого прогона —
# `telegram_last_post_at` в базе). Ждать в одном прогоне — не дольше
# RUN_WAIT_S, чтобы прогон кончился до следующего (рутина — раз в час);
# что не успело, уходит следующим прогоном с той же паузой. Каждый новый
# пост записывается на диск сразу после отправки: оборвись прогон посреди
# ожидания, повтора не будет. Правки вышедших постов паузы не ждут.
GAP_S = float(os.environ.get('TELEGRAM_GAP_S', str(20 * 60)))
RUN_WAIT_S = float(os.environ.get('TELEGRAM_RUN_WAIT_S', str(45 * 60)))

# ---------- РАВНОМЕРНАЯ ВЫДАЧА ----------
# Пять постов подряд в одну минуту — это не лента, а спам: читатель получает
# пять уведомлений за десять секунд и отключает канал. Раскладываем найденное
# за прогон на окно дневных часов.
#
# ПОЧЕМУ БЕЗ СОБСТВЕННОГО РАСПИСАНИЯ И БЕЗ ОЖИДАНИЯ ВНУТРИ ПРОЦЕССА. Растянуть
# отправку на девять часов внутри одного запуска нельзя: публикация — последний
# шаг притока, а приток живет короткой сессией и завершается. Хранить «когда
# опубликовать» отдельным полем тоже не хочется: это второе состояние рядом с
# `telegram_posts`, которое обязано с ним не разъезжаться.
#
# Поэтому расчет БЕЗ СОСТОЯНИЯ: на каждом прогоне смотрим, сколько прогонов
# еще осталось до конца окна, и берем ровно свою долю очереди. Пять постов в
# 10:00 при часовом прогоне и окне до 19:00 — это 10 оставшихся прогонов и по
# одному посту за раз; если часть постов не ушла, следующий прогон честно
# пересчитает долю от того, что осталось. Самовосстанавливается: пропущенный
# прогон не копит долг, он просто делится на меньшее число слотов.
MSK = timezone(timedelta(hours=3))          # Москва, перевода часов нет
# Расписание рутины публикации расширено до 10:00–21:00 МСК 21 августа
# 2026 (см. окно в самом триггере) — умолчание здесь отставало от него и
# держало готовые посты до утра два лишних часа. Как и с DEFAULT_CHANNEL
# выше: значение не секретно, поэтому умолчание можно поднять прямо в
# коде, а не заводить обязательную переменную окружения.
PUBLISH_WINDOW = os.environ.get('TELEGRAM_WINDOW', '10-21')   # часы по Москве
RUN_EVERY_H = float(os.environ.get('TELEGRAM_RUN_EVERY_H', '1'))


def window_bounds():
    start, end = (int(x) for x in PUBLISH_WINDOW.split('-'))
    assert 0 <= start < end <= 24, 'окно публикации задано неверно: %r' % PUBLISH_WINDOW
    return start, end


# ОДИН ОТПРАВЛЯЮЩИЙ ЗА РАЗ (29 октября 2026). Два прогона публикации шли
# одновременно (второй — из другой папки ship_decisions), каждый со своей
# очередью и своей паузой 20 минут: посты «Полюса», «Сибпромстроя» и
# «Уралсиба» вышли в канал недвижимости по два раза с разницей 13 минут.
# Замок общий для машины (не для папки), снимается сам при выходе процесса.
SEND_LOCK = os.environ.get('COMPASS_SEND_LOCK', '/tmp/compass-send-telegram.lock')
_send_lock_fd = None


def take_send_lock(path=None):
    global _send_lock_fd
    import fcntl
    if _send_lock_fd is not None and path is None:
        return True  # замок уже у этого процесса (тесты зовут main несколько раз)
    fd = open(path or SEND_LOCK, 'a')
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fd.close()
        return False
    _send_lock_fd = fd
    return True


def already_posted_on_disk(did, path=None):
    """Пост по сделке уже записан в файле на диске — другим процессом,
    пока этот спал в паузе между постами."""
    try:
        disk = json.load(open(path or DATA, encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return (disk.get('telegram_posts') or {}).get(did) is not None \
        or did in (disk.get('telegram_posts_realty') or {})


def gap_wait_s(last_post_at, now=None):
    """Сколько секунд ждать до следующего нового поста (0 — можно сейчас)."""
    if not last_post_at:
        return 0.0
    try:
        last = datetime.fromisoformat(str(last_post_at))
    except ValueError:
        return 0.0
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max(0.0, GAP_S - (now - last).total_seconds())


def in_window_after(wait_s, now=None):
    """Пост, отложенный на wait_s, все еще попадает в дневное окно."""
    start, end = window_bounds()
    at = (now or datetime.now(MSK)) + timedelta(seconds=wait_s)
    return start <= at.hour + at.minute / 60.0 < end


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
    # С 14 октября 2026 очередь не размазывается по дню: одобренное уходит
    # сразу, несколько — с паузой GAP_S (см. выше), ее держит цикл отправки.
    return pending, 'окно %02d:00–%02d:00 МСК: отправляем сразу, между новыми постами — %d мин' % (
        start, end, int(GAP_S // 60))


class TelegramError(Exception):
    pass


def _client():
    import httpx
    return httpx.Client(timeout=20.0)


def post_message(client, token, chat_id, text, buttons=None):
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML',
               'disable_web_page_preview': True}
    if buttons:
        payload['reply_markup'] = buttons
    r = client.post(telegram_endpoint.method_url(token, 'sendMessage'), json=payload)
    body = r.json()
    if not body.get('ok'):
        raise TelegramError('sendMessage: %s' % (body.get('description') or r.text[:200]))
    return body['result']['message_id']


def is_message_gone(error_text):
    """Telegram отвечает так, когда сообщение удалено из канала (человеком —
    ни один наш скрипт message_id не трогает) или сам канал/чат недоступен
    боту, — а не когда есть проблема с СЕТЬЮ или ТОКЕНОМ. Отличать нужно:
    остальные ошибки правки — повод остановиться и разобраться, эта —
    повод спросить человека, что делать с конкретной карточкой, и продолжить
    прогон дальше (П4-10)."""
    t = str(error_text or '').lower()
    return 'message to edit not found' in t or 'chat not found' in t


def edit_message(client, token, chat_id, message_id, text, buttons=None):
    # Клавиатуру передаем и при правке: `editMessageText` без `reply_markup`
    # снимает кнопки с уже опубликованного поста, а не оставляет их как были.
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text,
               'parse_mode': 'HTML', 'disable_web_page_preview': True}
    if buttons:
        payload['reply_markup'] = buttons
    r = client.post(telegram_endpoint.method_url(token, 'editMessageText'), json=payload)
    body = r.json()
    if not body.get('ok'):
        # "message is not modified" — Telegram считает правкой даже пробел;
        # повторная отправка того же текста не должна валить весь прогон.
        if 'not modified' in str(body.get('description', '')).lower():
            return
        raise TelegramError('editMessageText: %s' % (body.get('description') or r.text[:200]))


def post_to_channels(client, token, addr, route, text, buttons):
    """Первый пост в каналы `route` по порядку. Возвращает ({канал: номер
    поста}, ошибка или None) — не бросает: пост, уже вышедший в первом
    канале, обязан быть записан, даже если второй канал отказал.

    Клавиатура в обоих каналах одна и та же: кнопки-ссылки на пару во
    втором канале сняты владельцем 29 октября 2026 («выглядит плохо»)."""
    mids = {}
    for ch in route:
        try:
            mids[ch] = post_message(client, token, addr[ch], text, buttons)
        except TelegramError as e:
            return mids, '%s: %s' % ('канал недвижимости' if ch == channels.REALTY
                                     else 'основной канал', e)
    return mids, None


def site_channel_edits():
    """{"<канал>:<номер поста>": …} — посты, поправленные людьми прямо в канале
    (сайт слышит это от Telegram, `main._remember_manual_channel_edit`). Сайт
    не ответил — None: тогда автоправки этого прогона не делаются вовсе,
    затереть ручную правку хуже, чем отложить уточнение поста на час."""
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if not token:
        return {}
    try:
        import httpx
        r = httpx.get('%s/api/ops/channel-edits' % site, params={'token': token}, timeout=20)
        if r.status_code == 200:
            return (r.json() or {}).get('edits') or {}
    except Exception as e:                                    # noqa: BLE001
        print('Список ручных правок в канале не получен (%s).' % e)
    return None


def site_channels():
    """Адреса каналов, которые сайт услышал от самого Telegram:
    {'chat_id': основной, 'realty_chat_id': недвижимость} — или {}, если
    спросить нечем или сайт не ответил."""
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if not token:
        return {}
    try:
        import httpx
        r = httpx.get('%s/api/moderation/channel' % site, params={'token': token}, timeout=20)
        if r.status_code == 200:
            return r.json() or {}
    except Exception as e:                                    # noqa: BLE001
        print('Адрес канала у сайта не спросить (%s).' % e)
    return {}


def realty_channel_address(site, main_chat):
    """Канал «Компас - Недвижимость»: переменная `TELEGRAM_REALTY_CHANNEL_ID`
    -> память сайта -> пусто (тогда посты о недвижимости идут в основной
    канал, как до 2 октября 2026). Совпал с основным — значит, адреса
    перепутаны, и такой адрес не годится: два поста подряд в одном канале
    хуже, чем один."""
    chat = (os.environ.get('TELEGRAM_REALTY_CHANNEL_ID', '').strip()
            or str((site or {}).get('realty_chat_id') or '').strip())
    return '' if chat and chat == str(main_chat or '').strip() else chat


def channel_address(site=None):
    """Куда постить. Порядок: переменная окружения -> адрес, который сайт
    услышал от самого Telegram -> пусто.

    Почему второй шаг вообще есть. 4 сентября 2026 канал сделали приватным, и
    старое @имя перестало существовать: `sendMessage` и `getChat` по нему
    отвечают «chat not found». Постить в закрытый канал можно только по
    внутреннему числовому адресу, а называет его сам Telegram — в посте
    канала, то есть САЙТУ (у него вебхук). Сайт его запоминает, рутина
    забирает по токену тем же мостом, что и решения модерации. Так адрес не
    надо ни вписывать руками в окружение (оно не доезжает до уже работающих
    сессий рутин), ни держать в публичном репозитории.

    Адрес канала недвижимости основным не считается никогда: 2 октября 2026
    сайт, услышав новый канал, записал его в ячейку основного — и рутина без
    переменной окружения отправила бы туда весь поток.
    """
    from_env = os.environ.get('TELEGRAM_CHANNEL_ID', '').strip()
    if from_env and not from_env.startswith('@'):
        return from_env
    site = site_channels() if site is None else site
    chat = str(site.get('chat_id') or '').strip()
    if chat and chat != str(site.get('realty_chat_id') or '').strip():
        return chat
    if from_env:
        print('ВНИМАНИЕ: адрес канала задан именем (%s), а канал закрытый — '
              'по имени он боту не виден. Сайт адреса пока не знает: напишите '
              'любое сообщение в канале, Telegram назовет адрес сам.' % from_env)
        return from_env
    print('ВНИМАНИЕ: адреса канала нет ни в окружении, ни у сайта. Напишите '
          'любое сообщение в канале — Telegram назовет адрес, сайт его '
          'запомнит, и следующий прогон отправит посты.')
    return ''



def post_snapshot(deal):
    """Поля карточки, из которых собран пост (SIGNIFICANT + консультанты,
    этапы и финансы предмета) — то, что `telegram_post_state` запоминает за
    каждым вышедшим постом."""
    eco, law = (deal.get('eco') or {}), (deal.get('law') or {})
    snap = {k: deal.get(k) for k in format_post.SIGNIFICANT
            if k not in ('advisers', 'events') and deal.get(k) is not None}
    # Заголовок — тоже часть поста: переписали его (29 октября 2026, Baggins
    # Coffee: «так не говорят») — пост правится молча, без «Что стало известно».
    snap['title'] = deal.get('title')
    snap['law'] = {'adv': law.get('adv') or []}
    snap['eco'] = {'target_fin': eco.get('target_fin'), 'finadv': eco.get('finadv')}
    snap['events'] = [{'kind': e.get('kind')} for e in (deal.get('events') or []) if isinstance(e, dict)]
    return snap


def card_changes_since_post(deals, posts, realty_posts, post_state):
    """{deal_id: [что изменилось]} для уже вышедших постов, чья карточка
    разошлась с запомненным состоянием. Пост без состояния только
    запоминается (seed) — иначе первый прогон переправил бы весь канал.

    ЗАЧЕМ (4 октября 2026). Задание на правку поста приходило только из
    `data/inbox/updates/`, которые пишет `enrich.py` в контейнере притока и
    которые в git не живут. Факт, дописанный таблицей правок, приемкой или
    руками, до канала не доходил: пост о «дочке» Western Union вышел
    29 сентября без финансов, 3 октября карточка получила баланс НКО, а
    пост так и стоял пустым, пока владелец не увидел у конкурента богатый
    текст о той же сделке. Теперь источник факта неважен: разошлось с
    состоянием — пост правится, и читателю называется, что именно нового."""
    out = {}
    for deal in deals:
        did = deal['id']
        if not (posts.get(did) or realty_posts.get(did)):
            continue
        before = post_state.get(did)
        if before is None:
            post_state[did] = post_snapshot(deal)
            continue
        found = format_post.changes(before, deal)
        # Финансы в пост больше не идут (29 октября 2026) — их изменение
        # пост не правит; снимок обновится молча веткой ниже.
        if found:
            out[did] = found
        elif before.get('title') is not None and before.get('title') != deal.get('title') \
                and not deal.get('post_override') and not format_post.is_joint_post(deal):
            out[did] = []   # молчаливая правка: заголовок переписан, фактов новых нет
        elif before != post_snapshot(deal):
            # Текст переписан теми же фактами (пересказ карточки, 16 октября
            # 2026): новостью это не считается — пост не трогаем, иначе у
            # старой сделки появляется шапка «Новое о сделке · уточнены
            # финансы», хотя нового ничего. Запоминаем новое состояние.
            post_state[did] = post_snapshot(deal)
    return out


def _same_numbers(was, now):
    """Те же числа (порядок не важен — пересказ меняет порядок мысли) —
    значит, изменилась только формулировка, а не факты."""
    nums = lambda t: sorted(re.findall(r'\d+(?:[.,]\d+)?', str(t or '')))
    return bool(nums(now)) and nums(was) == nums(now)

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


BANK_FINANCE_PATH = os.path.join(ROOT, 'static', 'data', 'bank_finance.json')


def load_bank_finance():
    """{company_id: запись формы 806/102} из static/data/bank_finance.json —
    пусто, если файла нет (тесты на временной базе)."""
    try:
        with open(BANK_FINANCE_PATH, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def fns_client_or_none():
    """Живой клиент ФНС — или `None`, если `API_FNS_KEY` не задан в этом
    окружении. Тихо, не падая: финстрока (П7-9) — украшение поста, а не его
    обязательная часть, и ее отсутствие не должно ронять весь прогон."""
    try:
        from fns_client import ApiFnsClient
        return ApiFnsClient()
    except Exception:                                                     # noqa: BLE001
        return None


def build_fin(deal, confirmed_inns, client, bank_finance=None):
    """{'target': fin_summary()|None, 'buyer': ...} — по confirmed ИНН сторон
    сделки, живым `bo()` (Этап 9, П7-9). `confirmed_inns` — только
    `decision == "confirmed"` (см. `fns_registry.confirmed_inns()`), поэтому
    банки сюда не попадают сами по себе: ФНС для них не дает коммерческую
    отчетность (форма для банков другая — блок «По данным Банка России» на
    сайте берет ее из ЦБ, не отсюда). Каждая роль — отдельный, независимый
    запрос: сбой по одной стороне не должен стоить финстроки другой стороне
    того же поста. Повторный запрос уже известной организации бесплатен
    (`bo` — лимит «по организациям», см. CLAUDE.md) — считать сторон сделок,
    которые мы и так синхронизируем, можно на каждый прогон."""
    fin = {}
    bank_finance = load_bank_finance() if bank_finance is None else bank_finance
    for role in ('target', 'buyer'):
        company_id = deal.get(role)
        if not company_id:
            continue
        # Банк или НКО: ФНС отчетности не даст, зато форма 806/102 Банка
        # России уже лежит в bank_finance.json (ежедневная рутина «банки») —
        # без сети и без ключа ФНС. До 4 октября 2026 такие посты выходили
        # без финансов (пост о «дочке» Western Union 29 сентября).
        if company_id in bank_finance:
            summary = format_post.bank_fin_summary(bank_finance[company_id])
            if summary:
                fin[role] = summary
            continue
        inn = confirmed_inns.get(company_id)
        if not inn or client is None:
            continue
        from fns_client import normalize_bo
        try:
            rows = normalize_bo(client.bo(inn), inn)
        except Exception:                                                 # noqa: BLE001
            continue
        summary = format_post.fin_summary(rows)
        if summary:
            fin[role] = summary
    return fin


def sendable(deal):
    return format_post.has(deal.get('sum')) or (deal.get('seller') or deal.get('seller_id')) \
        or (deal.get('target') or deal.get('asset') or deal.get('asset_id'))


def initial_post_text(deal, comps):
    """Текст ПЕРВОГО поста о сделке. Приоритет: `post_override` (владелец
    продиктовал текст сам — его решение сильнее всего) > `post_preview`
    (снимок текста, который владелец уже видел и одобрил кнопкой в консоли,
    см. `pipeline/ingest/send_drafts.py`) > свежая сборка `format_post.render`
    — только если превью почему-то не сохранилось (например, у карточек до
    11 сентября 2026, когда снимок еще не делался).

    БЕЗ ПРИОРИТЕТА `post_preview` ПОСТ МОГ РАЗОЙТИСЬ С ОДОБРЕННЫМ. До этой
    правки текст всегда собирался заново, из ТЕКУЩИХ полей карточки: между
    показом черновика в консоли и настоящей отправкой карточку успевает
    дообогатить ФНС или вычитка — владелец одобрял кнопкой один текст,
    подписчики получали другой. На карточке «Трамплин Холдинг»/«Мальт
    Систем» (`g6743f902`, 11 сентября 2026) так в уже одобренный пост
    молча добавились две строки «Финансы покупателя/покупаемой компании» и
    переписалось несколько фраз — владелец увидел это только после
    публикации. `post_preview` не используется для ПРАВОК уже вышедшего
    поста (`to_edit`, «⟳ Обновлено») — те как раз ОБЯЗАНЫ собираться заново,
    в них и смысл сообщить о том, что стало известно НОВОГО."""
    # Строка «Подробнее в карточке сделки» — в конце любого первого поста,
    # и продиктованного владельцем, и одобренного снимка, снятого до
    # 13 октября 2026 (`with_card_link` не дает ей задвоиться).
    if deal.get('post_override'):
        return format_post.with_card_link(format_post.strip_platform_links(deal['post_override']), deal)
    if deal.get('post_preview'):
        return format_post.with_card_link(deal['post_preview'], deal)
    return format_post.render(deal, comps)


# ---------- ВЕХИ: отдельные посты по закрытому списку видов (раздел A) ------
# Молчание сутки = веха выходит, тот же принцип, что у карточек предпросмотра
# (approve.py's SILENCE_HOURS). Отсчет — от `event['milestone_drafted_at']`,
# который ставит pipeline/ingest/send_milestone_drafts.py в момент отправки
# черновика в консоль, а не от даты самого этапа (`event['date']`) — молчание
# считается с момента, когда человек МОГ увидеть черновик, а не с момента
# самого события.
MILESTONE_SILENCE_HOURS = 24
# Молчание публикует веху, только пока она новость. Веха о закрытии сделки,
# три недели провисевшая в консоли, — уже не новость, а повтор поста о самой
# сделке (найдено 24 сентября 2026: веха «НМГ закрыла сделку по „Комсомольской
# правде"» от 3 сентября держалась ложной находкой вычитки; когда вычитку
# починили, молчание выпустило бы ее в канал с опозданием на 21 день). Старше
# этого срока молчание веху не публикует; явная кнопка «пост в канал» —
# публикует, решение человека сильнее.
MILESTONE_MAX_SILENCE_DAYS = 7


# Этап, который первый пост сделки уже рассказал: пост вышел со статусом
# этапа (или с этим этапом в «Ходе сделки») — отдельная веха о нем повторит
# пост слово в слово. 29 октября 2026 «Агропромкредит» (`g1f8414a3`) вышел
# 27 октября уже «Закрыта», а через два дня консоль предложила веху
# «закрытие», партнер нажал — в канале два одинаковых поста
# («Мы это уже постили»).
_STAGE_STATUS = {'closed': 'Закрыта', 'cancelled': 'Не состоялась',
                 'approval': 'Согласование получено'}


def first_post_already_told(event, post_snapshot):
    """Снимок поста (`telegram_post_state[id]`) уже нес этот этап."""
    if not post_snapshot:
        return False
    kind = str(event.get('kind') or '')
    if any(str(e.get('kind') or '') == kind for e in (post_snapshot.get('events') or [])
           if isinstance(e, dict)):
        return True
    return bool(_STAGE_STATUS.get(kind)) and str(post_snapshot.get('status') or '') == _STAGE_STATUS[kind]


def milestone_candidates(deals, stage_posts, post_state=None):
    """Вехи (`newsworthy` + `headline` + вид из закрытого списка), которым еще
    не отправлен отдельный пост и которые первый пост сделки не рассказал
    (`post_state` — `data['telegram_post_state']`, см. `first_post_already_told`).

    Дедуп — по `event['id']` в `stage_posts` (`data['telegram_milestones']`,
    отдельный от `telegram_posts` словарь верхнего уровня: `telegram_posts[id]`
    — либо `None`, либо голое число (message_id) без вложенности, это уже
    закреплено тестами и читается `main.py`'s `_ops_numbers()`, менять форму
    существующего поля ради вех рискованно и не нужно — у события уже есть
    свой стабильный `id`, отдельный словарь по нему ничего не ломает и
    ничего не мигрирует)."""
    out = []
    for deal in deals:
        for event in deal.get('events') or []:
            if not (isinstance(event, dict) and event.get('newsworthy') and event.get('headline')
                    and event.get('id') and event.get('kind') in review.POSTWORTHY_MILESTONE_KINDS):
                continue
            if event['id'] in stage_posts:
                continue
            if first_post_already_told(event, (post_state or {}).get(deal.get('id'))):
                continue
            out.append((deal, event))
    return out


def milestone_decisions(decisions):
    """{event_id: (verdict, decision_id)} — последнее решение по каждой вехе.

    Кнопки вехи используют ТЕ ЖЕ вердикты, что «пост в канал»/«без поста» у
    обычной карточки (`post_ok`/`post_no` -> `post_yes`/`post_no` в main.py),
    а не собственное имя: это тот же модификатор канала, только для события,
    а не для сделки целиком. Отличает веху от карточки форма `deal_id` в
    решении — `<id сделки>~<kind>` (разделитель `~`, а не `:` — двоеточие уже
    занято разбором `mod:<id>:<вердикт>`, и не `-`, потому что сами id сделок
    бывают с дефисами: `event['id']` тогда было бы неоднозначно резать
    обратно). `event['id']` собирается конкатенацией: `<id сделки>-<kind>`
    (тот же формат, что `mark_milestone()` в review.py уже присваивает)."""
    out = {}
    for d in decisions:
        did = str(d.get('deal_id') or '')
        # `digest~2026-08` — решение по месячной сводке, а не по вехе: тот же
        # разделитель, другая сущность (см. `digest_decisions`).
        if did.startswith('digest~') or did.endswith('~edit'):
            continue
        if '~' not in did or d.get('verdict') not in ('post_yes', 'post_no'):
            continue
        deal_id, _, kind = did.partition('~')
        event_id = '%s-%s' % (deal_id, kind)
        out[event_id] = (d['verdict'], d['id'])
    return out


# Сколько минут считать, что сайт еще публикует этап (отметка
# `posting_since` в решении). Дольше — значит, сайт упал посреди отправки, и
# этап выпускает рутина, как раньше.
SITE_POSTING_GRACE_MIN = 10


def _milestone_event_id(decision):
    """`<id сделки>-<вид>` для решения по этапу, иначе ''."""
    did = str(decision.get('deal_id') or '')
    if did.startswith('digest~') or '~' not in did:
        return ''
    deal_id, _, kind = did.partition('~')
    return '%s-%s' % (deal_id, kind)


def site_posted_milestones(decisions, now):
    """Этапы, которые сайт опубликовал сам по кнопке «пост в канал»
    (5 октября 2026, `main._instant_milestone_post`): ({event_id: запись для
    `telegram_milestones`}, {event_id, которые сайт публикует прямо сейчас}).

    Номер поста сайт пишет в само решение (`edited_text`), потому что больше
    ему писать некуда: база сделок живет в git, а не на сайте. Рутина
    записывает этап вышедшим и второй раз его не шлет; решение после этого
    гасится как обычное устаревшее (`plan_milestones`)."""
    posted, posting = {}, set()
    for d in decisions:
        eid = _milestone_event_id(d)
        if not eid or d.get('verdict') != 'post_yes':
            continue
        try:
            mark = json.loads(d.get('edited_text') or '')
        except (TypeError, ValueError):
            continue
        if not isinstance(mark, dict):
            continue
        if mark.get('posted_message_id'):
            posted[eid] = {'at': mark.get('posted_at') or d.get('created_at'),
                           'message_id': mark['posted_message_id'], 'by': 'site'}
        elif mark.get('posting_since'):
            try:
                since = datetime.fromisoformat(str(mark['posting_since']))
            except ValueError:
                continue
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            if (now - since).total_seconds() < SITE_POSTING_GRACE_MIN * 60:
                posting.add(eid)
    return posted, posting - set(posted)


def milestone_age_hours(event, now):
    raw = str(event.get('milestone_drafted_at') or '')
    try:
        drafted = datetime.fromisoformat(raw)
    except ValueError:
        return 0.0
    if drafted.tzinfo is None:
        drafted = drafted.replace(tzinfo=timezone.utc)
    return (now - drafted).total_seconds() / 3600.0


DIGEST_SILENCE_HOURS = 24
# Со второго числа: за первое число месяца еще приезжают сделки последних
# дней — сводка, собранная в ночь на первое, недосчитается их.
DIGEST_FROM_DAY = 2


def digest_due(data, today):
    """Месяц (год, номер), за который сводка еще не выходила, — или None.

    Смотрим только на ПРЕДЫДУЩИЙ месяц: сводка за август выходит в начале
    сентября и один раз. Признак «уже выходила» — запись с `message_id` в
    `telegram_digests`; черновик без `message_id` не считается вышедшим."""
    if today.day < DIGEST_FROM_DAY:
        return None
    year, month = monthly_digest.previous_month(today)
    key = monthly_digest.month_key(year, month)
    state = (data.get('telegram_digests') or {}).get(key) or {}
    if state.get('message_id'):
        return None
    if not monthly_digest.enough(monthly_digest.stats(data, year, month)):
        return None
    return year, month


def late_owner_texts(decisions):
    """{id сделки: (HTML текста поста, id решения)} — «опубликовать» со своим
    текстом по карточке, которая уже вышла из очереди (approve.py забрал
    решения раньше, чем владелец ответил). Последнее по времени."""
    out = {}
    for d in sorted(decisions, key=lambda x: str(x.get('created_at') or '')):
        did = str(d.get('deal_id') or '')
        text = (d.get('edited_text') or '').strip()
        if '~' in did or d.get('verdict') != 'approve' or not text or text.startswith('{'):
            continue
        out[did] = (format_post.owner_text_as_html(text), d['id'])
    return out


def post_edit_decisions(decisions):
    """{id сделки: (вердикт, id решения, текст владельца или None)} — ответ на
    предложение правки вышедшего поста (`propose_post_edit.py`): `deal_id`
    решения — `<id>~edit`, вердикты те же, что у поста карточки; текст —
    когда владелец ответил своей редакцией, а не кнопкой."""
    out = {}
    for d in sorted(decisions, key=lambda x: str(x.get('created_at') or '')):
        did = str(d.get('deal_id') or '')
        if not did.endswith('~edit') or d.get('verdict') not in ('post_yes', 'post_no'):
            continue
        out[did[:-len('~edit')]] = (d['verdict'], d['id'], (d.get('edited_text') or '').strip() or None)
    return out


def plan_post_edits(deals, decisions, posts, realty_posts):
    """(правки [(id, {канал: номер поста}, текст)], снятые предложения [id],
    id решений к гашению) по ответам на предложения правки поста."""
    answers = post_edit_decisions(decisions)
    edits, dropped, decision_ids = [], [], []
    for deal in deals:
        did = deal['id']
        answer = answers.get(did)
        if not answer:
            continue
        verdict, decision_id, owner_text = answer
        decision_ids.append(decision_id)
        proposal = deal.get('post_edit_proposal')
        if owner_text and verdict == 'post_yes':
            # Своя редакция владельца сильнее предложенного текста — как у
            # первого поста (approve.py: owner_text_as_html + ссылка на карточку).
            proposal = format_post.with_card_link(
                format_post.strip_platform_links(format_post.owner_text_as_html(owner_text)), deal)
            deal['post_edit_proposal'] = proposal
        if not proposal:
            continue
        where = {ch: mid for ch, mid in ((channels.MAIN, posts.get(did)),
                                         (channels.REALTY, realty_posts.get(did))) if mid}
        if verdict == 'post_yes' and where:
            edits.append((did, where, proposal))
        else:
            dropped.append(did)
    return edits, dropped, decision_ids


def digest_decisions(decisions):
    """{ключ месяца: (вердикт, id решения)} — кнопки сводки используют те же
    вердикты `post_ok`/`post_no`, что карточка и веха; отличает ее форма
    `deal_id` в решении — `digest~2026-08`."""
    out = {}
    for d in decisions:
        did = str(d.get('deal_id') or '')
        if not did.startswith('digest~') or d.get('verdict') not in ('post_yes', 'post_no'):
            continue
        out[did.split('~', 1)[1]] = (d['verdict'], d['id'])
    return out


def digest_age_hours(state, now):
    raw = str((state or {}).get('drafted_at') or '')
    try:
        drafted = datetime.fromisoformat(raw)
    except ValueError:
        return 0.0
    if drafted.tzinfo is None:
        drafted = drafted.replace(tzinfo=timezone.utc)
    return (now - drafted).total_seconds() / 3600.0


def plan_digest(data, decisions, now, today=None):
    """('draft'|'send'|None, ключ месяца, причина, id решений на консумацию).

    Тот же порядок, что у вехи: черновик в консоль -> сутки молчания ->
    публикация. Чистая функция — проверяется без сети."""
    due = digest_due(data, today or now.astimezone(MSK).date())
    if not due:
        return None, None, 'сводка за прошлый месяц уже выходила или месяц пустой', []
    year, month = due
    key = monthly_digest.month_key(year, month)
    state = (data.get('telegram_digests') or {}).get(key) or {}
    decision = digest_decisions(decisions).get(key)
    if decision and decision[0] == 'post_no':
        return None, key, 'основатели решили не публиковать', [decision[1]]
    if decision and decision[0] == 'post_yes':
        return 'send', key, 'одобрено в консоли', [decision[1]]
    if not state.get('drafted_at'):
        return 'draft', key, 'черновик еще не отправлен в консоль', []
    age = digest_age_hours(state, now)
    if age >= DIGEST_SILENCE_HOURS:
        return 'send', key, 'молчание %.0f ч' % age, []
    return None, key, 'ждет решения (%.0f ч из %d)' % (age, DIGEST_SILENCE_HOURS), []


def deliver_digest(action, key, text, token, chat_id, digests, now, client_factory=None):
    """Отправить сводку — в канал или черновиком в консоль. Возвращает
    (изменилось ли состояние, ошибка или None).

    Отдельной функцией, а не куском `main()`, ровно по одной причине: у
    `main()` есть ранний выход «отправлять сейчас нечего» — и в самый частый
    для сводки день (спокойное начало месяца, новых сделок нет) она бы просто
    не дошла до кода отправки. Функция вызывается ДО этого выхода."""
    client = (client_factory or _client)()
    try:
        if action == 'send':
            mid = post_message(client, token, chat_id, text,
                               monthly_digest.render_buttons(int(key[:4]), int(key[5:7])))
            digests[key] = dict(digests.get(key) or {}, message_id=mid,
                                at=now.isoformat(timespec='seconds'))
            print('Сводка %s опубликована (message_id %s)' % (key, mid))
            return True, None
        import send_drafts                                        # noqa: E402
        chats = send_drafts.send_targets()
        if not chats:
            print('Сводка %s: консоль не настроена — черновик некому показать' % key)
            return False, None
        buttons = monthly_digest.render_buttons(int(key[:4]), int(key[5:7]))
        thread = console_topics.thread_id('decision')
        for chat in chats:
            send_drafts.send_one(client, token, chat,
                                 digest_draft_message(text, key, buttons),
                                 digest_keyboard(key), thread, html=True)
        digests[key] = dict(digests.get(key) or {},
                            drafted_at=now.isoformat(timespec='seconds'))
        print('Сводка %s: черновик отправлен в консоль' % key)
        return True, None
    except (TelegramError, OSError) as e:
        # Сводка — не критичный шаг: ее сбой не должен ронять отчет по постам
        # сделок, которые уже ушли.
        return False, str(e)


def digest_keyboard(key):
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:digest~%s:post_ok' % key},
        {'text': '🔕 Без поста', 'callback_data': 'mod:digest~%s:post_no' % key},
    ]]}


def digest_draft_message(text, key, buttons):
    """Уходит с разметкой (`send_one(..., html=True)`), как и сам пост."""
    return ('📊 [сводка %s] — В КАНАЛ, на проверку\n'
            'Итоги месяца одним постом. Молчание сутки — выходит как есть; '
            'ответ своим текстом заменит пост.\n'
            '━━━━━━━━━━━━\n%s\n\n%s'
            % (format_post.esc(key), text, format_post.esc(format_post.buttons_preview(buttons))))


def answered_an_earlier_draft(created_at, event):
    """Решение принято ДО того, как ушел нынешний черновик вехи, — значит,
    человек отвечал на прежний текст, а не на этот. Так бывает, когда
    черновик отозвали и отправили заново (25 сентября 2026: владелец не
    пустил веху «Ростех»/«Швабе» из-за формата; после починки формата она
    ушла в консоль еще раз, и старое «без поста» не должно решать за новый
    текст). Черновика нет вовсе (метку сняли, чтобы отправить заново) — тоже
    прежний. Время решения неизвестно — считаем решение действующим, как
    раньше."""
    if not created_at:
        return False
    try:
        decided = datetime.fromisoformat(str(created_at))
        drafted = datetime.fromisoformat(str(event['milestone_drafted_at'])) \
            if event.get('milestone_drafted_at') else None
    except ValueError:
        return False
    if drafted is None:
        return True
    if decided.tzinfo is None:
        decided = decided.replace(tzinfo=timezone.utc)      # сайт пишет наивное UTC
    if drafted.tzinfo is None:
        drafted = drafted.replace(tzinfo=timezone.utc)
    return decided < drafted


def rejected_milestones(deals, decisions, discard_ids, stage_posts=()):
    """id вех, которым в этом прогоне сказали «без поста» — их запоминает
    `telegram_milestones`. Решение о прежнем черновике гасится, но вехой
    не отказывает (`answered_an_earlier_draft`); веха, уже записанная в
    `stage_posts` (вышла или отклонена раньше), не перезаписывается."""
    created = {d.get('id'): d.get('created_at') for d in decisions}
    events = {e.get('id'): e for deal in deals for e in (deal.get('events') or [])
              if isinstance(e, dict)}
    return [eid for eid, (verdict, did) in milestone_decisions(decisions).items()
            if verdict == 'post_no' and did in discard_ids and eid in events
            and eid not in stage_posts
            and not answered_an_earlier_draft(created.get(did), events[eid])]


def plan_milestones(deals, stage_posts, decisions, now, post_state=None):
    """(отправить, придержать, отклоненные id решений-заглушек) — чистая
    функция аналогично `approve.plan_actions`, чтобы логика проверялась без
    сети. `discard_ids` — decision id вехам с `post_no` и решениям о прежнем
    черновике: их надо consume'нуть, даже если сама веха никогда не
    отправится."""
    by_event = milestone_decisions(decisions)
    created = {d.get('id'): d.get('created_at') for d in decisions}
    send, hold, discard_ids, sent_decision_ids = [], [], [], []
    for deal, event in milestone_candidates(deals, stage_posts, post_state):
        decision = by_event.get(event['id'])
        if decision and answered_an_earlier_draft(created.get(decision[1]), event):
            discard_ids.append(decision[1])
            decision = None
        if decision and decision[0] == 'post_no':
            discard_ids.append(decision[1])
            continue
        if decision and decision[0] == 'post_yes':
            send.append((deal, event))
            sent_decision_ids.append(decision[1])
            continue
        # Черновик еще не отправлялся (нет milestone_drafted_at) — не
        # кандидат на молчание, его отправит send_milestone_drafts.py.
        if not event.get('milestone_drafted_at'):
            hold.append((deal, event, 'черновик еще не отправлен в консоль'))
            continue
        age = milestone_age_hours(event, now)
        if age >= MILESTONE_MAX_SILENCE_DAYS * 24:
            hold.append((deal, event, 'устарела: черновик в консоли %.0f дн., молчание уже не '
                         'публикует — только кнопка «пост в канал»' % (age / 24)))
        elif age >= MILESTONE_SILENCE_HOURS:
            send.append((deal, event))
        else:
            hold.append((deal, event, 'ждет решения (%.0f ч из %d)' % (age, MILESTONE_SILENCE_HOURS)))
    # Решения, которые больше ничего не решают, тоже гасим: перекрытые более
    # поздним нажатием по той же вехе и решения по вехе, которая уже вышла
    # или отклонена. Иначе они висят на сайте вечно (25.09.2026: «без поста»
    # на прежний черновик «Швабе» осталось после выхода нового по кнопке).
    chosen = {did for _v, did in by_event.values()}
    for d in decisions:
        did = str(d.get('deal_id') or '')
        if did.startswith('digest~') or did.endswith('~edit') or '~' not in did \
                or d.get('verdict') not in ('post_yes', 'post_no'):
            continue
        deal_id, _, kind = did.partition('~')
        stale = d['id'] not in chosen or '%s-%s' % (deal_id, kind) in stage_posts
        if stale and d['id'] not in discard_ids and d['id'] not in sent_decision_ids:
            discard_ids.append(d['id'])
    return send, hold, discard_ids, sent_decision_ids


def deals_missing_on_site(deal_ids):
    """Каких карточек сайт еще НЕ отдает. Пусто — все на месте или проверить
    не удалось.

    Сайт живет на своей копии базы: код едет деплоем, а
    `deals_promoted.json` подтягивается из `main` раз в
    DATA_REFRESH_MINUTES. Между коммитом и появлением карточки на сайте —
    минуты, и ровно в это окно пост со ссылкой «Открыть карточку сделки»
    ведет в никуда (жалоба владельца 11 сентября 2026).

    Сеть недоступна -> возвращаем пусто, то есть шлем как раньше: молчащий
    канал хуже, чем ссылка, которая заработает через пять минут. Это то же
    решение, что в `send_drafts.site_pending_ids`."""
    ids = {d for d in deal_ids if d}
    if not ids or os.environ.get('PUBLISH_WAIT_FOR_SITE', '1') != '1':
        # Выключатель того же рода, что `DATA_REFRESH_ENABLED=0` и пустой
        # `TELEGRAM_BOT_TOKEN`: тесты гоняют `main()` на выдуманных
        # карточках, которых на боевом сайте нет и быть не может, — без
        # выключателя страховка честно отсекала бы их все, и пять тестов
        # публикации проверяли бы пустой список вместо поста.
        return set()
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    try:
        import httpx
        # С 16 октября 2026 база отдается сайтом через api/data/... и только
        # своим (scrape_guard.py): рутина предъявляет служебный ключ — тот же
        # MODERATION_TOKEN, что у моста решений. Старый адрес — запасной, на
        # время, пока на сервере код до этой правки.
        key = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
        hdrs = {'X-Data-Key': key} if key else {}
        # Старый сервер на новый адрес отвечает страницей сайта (200, HTML) —
        # поэтому годится только ответ, который разбирается как база.
        base = None
        for path in ('/api/data/deals_promoted.json', '/static/data/deals_promoted.json'):
            r = httpx.get(site + path, params={'nocache': os.getpid()},
                          headers=hdrs, timeout=30)
            if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
                base = r.json()
                break
        if base is None:
            return set()
        live = {d.get('id') for d in base.get('deals', [])}
    except Exception as e:                                    # noqa: BLE001
        print('Не удалось спросить сайт, какие карточки он уже отдает (%s) — '
              'шлем как есть.' % e)
        return set()
    return {d for d in ids if d not in live}


def main(write, ignore_pace=False, skip_ids=frozenset(), wait_for_site=0):
    """`ignore_pace` — то же, что ключ `--now`, но параметром.

    Нужен тестам: они проверяют лимит сообщений за прогон и правило бэклога, а
    не дневное окно, и без явного обхода темпа проходили бы только с 10 до 21
    по Москве — то есть падали бы по вечерам, ничего при этом не сломавшись.

    `skip_ids` — П3-10: id сделок, которые НЕ уходят в этот прогон, даже если
    прошли механическую вычитку (`check_post.py`) — решение читающего (рутина
    публикации ПОСЛЕ того, как прочла полные тексты в сухом прогоне), не
    ошибка формата. Не помечаются отправленными: следующий прогон увидит их
    заново, если владелец не решит иначе.

    `wait_for_site` — сколько минут ждать, пока сайт покажет только что
    одобренные карточки (ключ `--wait-for-site N`; см. комментарий у
    `deals_missing_on_site` в теле)."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if write and token and not take_send_lock():
        print('Другой прогон публикации уже отправляет посты — этот ничего не шлет '
              '(иначе каждый пост вышел бы дважды).')
        return
    # Без токена слать все равно некуда — не спрашиваем сайт за адресом
    # канала: без этой проверки функция без токена все равно делала
    # живой сетевой запрос (см. `channel_address()`), а в средах, где
    # `MODERATION_TOKEN`/`TELEGRAM_WEBHOOK_SECRET` заданы, но исходящая
    # сеть к боевому сайту не работает или отвечает медленно, — это
    # реальный, воспроизводимый сетевой вызов там, где по докстрингу и
    # тесту (`test_main_without_token_never_touches_network_or_writes`)
    # его быть не должно.
    site = site_channels() if token else {}
    chat_id = channel_address(site) if token else ''
    # КАНАЛ НЕДВИЖИМОСТИ (2 октября 2026, см. `channels.py`). Его посты
    # записываются в `telegram_posts_realty` — отдельный словарь, а не
    # вложенность в `telegram_posts`: там значение — голое число или null, и
    # это читают `main.py`, `accept_card.py` и тесты. Пост, вышедший только в
    # канале недвижимости, оставляет в `telegram_posts` null — «в основном
    # канале не публиковался», и все, что считает очередь первых постов,
    # видит его обработанным.
    realty_chat = realty_channel_address(site, chat_id) if token else ''
    if token and not realty_chat:
        print('Адрес канала «Компас - Недвижимость» неизвестен — посты о '
              'недвижимости идут в основной канал, как раньше.')
    addr = {channels.MAIN: chat_id, channels.REALTY: realty_chat}
    data = json.load(open(DATA, encoding='utf-8'))
    posts = data.setdefault('telegram_posts', {})
    realty_posts = data.get('telegram_posts_realty') or {}
    milestones = data.setdefault('telegram_milestones', {})
    comps = data['companies']
    updates_by_id = load_today_updates()
    # Карточка дополнена мимо притока — пост все равно правится (см.
    # `card_changes_since_post`). Задание из data/inbox/updates/ главнее:
    # там изменения названы точнее.
    post_state = data.setdefault('telegram_post_state', {})
    for did, found in card_changes_since_post(data['deals'], posts, realty_posts, post_state).items():
        updates_by_id.setdefault(did, found)

    # ВЕХИ (раздел A). Решения приходят с сайта тем же мостом, что и у
    # карточек (approve.fetch_decisions) — консуммируются здесь же, сразу:
    # в отличие от approve.py, дедуп вехи не зависит от того, подтвердил ли
    # сайт «применено» — он держится на `milestones[event_id]` (git-нативно,
    # см. docstring `milestone_candidates`), поэтому двухфазный `--consume`
    # не нужен: повторная выборка того же решения безопасна в любом порядке.
    m_decisions, m_handle = approve.fetch_decisions()
    now_utc = datetime.now(timezone.utc)
    # Этап, который сайт уже выпустил по кнопке, записываем вышедшим — тогда
    # план его не шлет, а решение гасит как устаревшее. Этап, который сайт
    # публикует в эти секунды, не трогаем вовсе: ни поста, ни гашения.
    site_posted, site_posting = site_posted_milestones(m_decisions, now_utc)
    for event_id, record in site_posted.items():
        milestones.setdefault(event_id, record)
    if site_posting:
        print('Сайт публикует прямо сейчас: %s — в этом прогоне не трогаем.'
              % ', '.join(sorted(site_posting)))
        m_decisions = [d for d in m_decisions if _milestone_event_id(d) not in site_posting]
    # Снимок первого поста — обязательно (30 октября 2026): без него веха
    # «закрыта» по «Агропромкредиту» вышла третьим постом, хотя первый пост
    # уже рассказал о закрытии и `first_post_already_told` это видит.
    m_send, m_hold, m_discard_ids, m_sent_decision_ids = plan_milestones(
        data['deals'], milestones, m_decisions, now_utc, post_state)
    if site_posting:
        m_hold += [(deal, event, 'сайт публикует его прямо сейчас')
                   for deal, event in m_send if event['id'] in site_posting]
        m_send = [(deal, event) for deal, event in m_send if event['id'] not in site_posting]
    # «Без поста» у вехи ЗАПОМИНАЕТСЯ в `telegram_milestones`, как и
    # отправленная веха. До 25 сентября 2026 решение только гасилось на сайте,
    # а сама веха оставалась кандидатом — и в следующем прогоне, уже без
    # решения, выходила по суткам молчания (нашлось на вехе «Ростех»/«Швабе»,
    # которую владелец не пустил из-за формата).
    m_rejected = rejected_milestones(data['deals'], m_decisions, m_discard_ids, milestones)

    # МЕСЯЧНАЯ СВОДКА (просьба владельца 2 сентября 2026). Тот же путь, что у
    # вехи: черновик в консоль -> сутки молчания -> публикация. Живет здесь, а
    # не отдельной рутиной: единственный момент, когда сводку есть смысл
    # собирать, — тот же прогон публикации, который и так ходит в канал
    # («расписание не нужно там, где уже есть естественное событие»).
    digests = data.setdefault('telegram_digests', {})
    digest_action, digest_key_, digest_why, digest_decision_ids = plan_digest(
        data, m_decisions, now_utc)
    digest_text = ''
    if digest_action:
        y, mth = int(digest_key_[:4]), int(digest_key_[5:7])
        digest_text = monthly_digest.render(data, y, mth)
        problems = check_post.check_digest(digest_text) if digest_text else ["сводка не собралась"]
        if problems:
            print('Сводка %s не отправлена: %s' % (digest_key_, '; '.join(problems)))
            digest_action, digest_text = None, ''
    print('Сводка месяца: %s (%s)' % (digest_action or 'ничего', digest_why))
    to_send_m = [(deal, event, format_post.render_milestone(deal, event)) for deal, event in m_send]
    m_flagged = []
    for deal, event, text in list(to_send_m):
        problems = check_post.check(text)
        if problems:
            m_flagged.append((event['id'], problems))
            to_send_m = [(d, e, t) for d, e, t in to_send_m if e['id'] != event['id']]

    to_send, to_edit, to_seed, needs_review, needs_acceptance = [], [], [], [], []
    # Предложенная правка вышедшего поста, одобренная в консоли
    # (`propose_post_edit.py`, 29 октября 2026): правится и пост с текстом
    # владельца — владелец сам одобрил новый текст, он и становится его текстом.
    approved_edits, dropped_edits, edit_decision_ids = plan_post_edits(
        data['deals'], m_decisions, posts, realty_posts)
    approved_edit_ids = {did for did, _w, _t in approved_edits}
    for did in dropped_edits:
        next(d for d in data['deals'] if d['id'] == did).pop('post_edit_proposal', None)
    to_edit.extend(approved_edits)
    for deal in data['deals']:
        did = deal['id']
        if did in approved_edit_ids:
            continue
        # Уже вышедший пост (в любом из каналов) только правится — там, где
        # он вышел. `where` — {канал: номер поста}.
        where = {ch: mid for ch, mid in ((channels.MAIN, posts.get(did)),
                                         (channels.REALTY, realty_posts.get(did))) if mid}
        if where:
            changes = updates_by_id.get(did)
            # Общий пост на несколько карточек (`post_covers`, 16 октября
            # 2026) — текст, одобренный владельцем целиком; правка из полей
            # ОДНОЙ карточки заменила бы его постом про одну компанию.
            # Текст владельца (`post_override`) — тоже: 21 октября 2026 пост
            # Swordfish Security, вышедший текстом владельца, через три часа
            # переписался автотекстом после дополнения карточки («Выложили не
            # тот пост, который я в консоль отправил»).
            if changes is not None and not format_post.is_joint_post(deal) and not deal.get('post_override'):
                to_edit.append((did, where, format_post.render(deal, comps, updates=changes)))
            continue
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
                    # 5 сентября 2026, просьба владельца: не оживлять
                    # молчавшую бэклог-карточку постом, если сама сделка все
                    # еще не свежая — даже настоящий новый факт о ней читатель
                    # канала увидит как «зачем мне это старье» и отпишется.
                    # Гейт `is_fresh()` тот же, что решает заголовок поста
                    # («Новое о сделке» / «Сделка из базы») — только раньше он
                    # выбирал ФОРМУЛИРОВКУ, а теперь решает, публиковать ли
                    # вообще. `post_override` пропускает его: там уже есть
                    # решение владельца по этой конкретной сделке.
                    if not deal.get('post_override') and not format_post.is_fresh(deal):
                        pass
                    elif not deal.get('post_override') and format_post.needs_review_before_post(deal):
                        # П2-9: пустая, еще не прочитанная карточка ждет дочитывания,
                        # а не уходит первым постом со всеми пустыми линзами.
                        needs_review.append(did)
                    elif not deal.get('post_override') and not deal.get('accepted'):
                        needs_acceptance.append(did)
                    else:
                        text = initial_post_text(deal, comps)
                        to_send.append((did, text))
        elif deal.get('no_post'):
            # Решение модерации «карточка без поста»: сайт получает карточку,
            # канал молчит. Засеваем состояние как бэклог (None) — если позже
            # у сделки появится настоящий новый факт, канал узнает о нем как
            # о новости, а не получит запоздалый первый пост.
            to_seed.append(did)
        elif sendable(deal):
            # 5 сентября 2026, просьба владельца: сделка не первой свежести не публикуется
            # в канал вовсе, даже честным «Сделка из базы · Публикуем впервые»
            # — подписчик читает любое новое сообщение как новость и от архива
            # отписывается. Повод — пост про «МорТехПром» с этой шапкой; сама та
            # сделка оказалась свежей (дата стояла годом без месяца — уточнено в
            # format_post.is_fresh), но правило владелец сформулировал общее:
            # не новые сделки в канал не идут. Засеваем как бэклог (None), тем же
            # путем, что решение модерации «без поста», — если позже найдется
            # настоящий новый факт, тот же гейт в ветке выше решит его судьбу заново.
            if not deal.get('post_override') and not format_post.is_fresh(deal):
                to_seed.append(did)
            # П2-9: та же дочитка — но для самого обычного, первого-в-жизни
            # поста. `post_override` пропускает гейт: там уже есть текст,
            # который владелец продиктовал сам, — читать за него нечего.
            elif not deal.get('post_override') and format_post.needs_review_before_post(deal):
                needs_review.append(did)
            elif not deal.get('post_override') and not deal.get('accepted'):
                # ПРИЕМКА (11 сентября 2026): первый пост о сделке уходит
                # только после того, как карточку прочитали целиком по
                # чек-листу (`pipeline/ingest/accept_card.py`, штамп
                # `accepted`). Пост наследует каждый дефект карточки и
                # показывает его подписчикам; «Зачем» об объеме рынка и
                # предмет-описание владелец увидел именно в канале. Текст,
                # продиктованный владельцем (`post_override`), — его решение,
                # гейт его не перекрывает; правки уже вышедших постов
                # (`to_edit`) — тоже не здесь.
                needs_acceptance.append(did)
            else:
                # Текст, который владелец продиктовал в Telegram при модерации
                # черновика (`post_override`), или снимок того, что он уже
                # видел и одобрил кнопкой (`post_preview`), важнее автоформата
                # — но только для ПЕРВОГО поста: дальнейшие обновления снова
                # собирает format_post (см. initial_post_text).
                text = initial_post_text(deal, comps)
                to_send.append((did, text))

    # ОБЩИЙ ПОСТ ЖДЕТ ВСЕ СВОИ КАРТОЧКИ (16 октября 2026, указ № 738: пять
    # карточек — один пост). Он ссылается на каждую из них; пока хоть одна
    # еще в очереди модерации, ее ссылка вела бы в никуда.
    deal_ids = {d['id'] for d in data['deals']}
    deals_by_id_all = {d['id']: d for d in data['deals']}
    joint_waiting = []
    for did, _text in list(to_send):
        covers = (deals_by_id_all.get(did) or {}).get('post_covers') or []
        missing = [c for c in covers if c not in deal_ids]
        if missing:
            joint_waiting.append((did, missing))
            to_send = [(d, t) for d, t in to_send if d != did]
    if joint_waiting:
        for did, missing in joint_waiting:
            print('Общий пост %s ждет, пока на сайт выйдут его карточки: %s'
                  % (did, ', '.join(missing)))

    # ВЫЧИТКА ПЕРЕД ОТПРАВКОЙ — ДО отчета и до выхода из сухого прогона: план
    # читает человек, и задержанные посты он должен видеть именно в плане.
    # Пост наследует дефекты карточки и показывает их публично: 9 августа
    # четыре поста подряд ушли с падежом вместо именительного («Предмет:
    # Дальневосточного банка»), и заметил это читатель, а не пайплайн.
    # Проверка механическая (без сети и токенов) и НЕ молчаливая: подозрительный
    # пост не уходит в канал, а называется в отчете прогона — дальше его судьбу
    # решает человек в консоли.
    flagged = []
    for did, text in list(to_send):
        problems = check_post.check(text)
        if problems:
            flagged.append((did, problems))
            to_send = [(d, t) for d, t in to_send if d != did]
    for did, mid, text in list(to_edit):
        problems = check_post.check(text)
        if problems:
            flagged.append((did, problems))
            to_edit = [(d, m, t) for d, m, t in to_edit if d != did]

    # ПОСТ НЕ УХОДИТ РАНЬШЕ САМОЙ КАРТОЧКИ. 11 сентября 2026 владелец нажал
    # в свежем посте «Открыть карточку сделки» и попал в никуда: пост ушел
    # сразу после коммита, а сайт подтягивает базу из `main` по расписанию
    # (`data_refresh.py`, раз в DATA_REFRESH_MINUTES) — несколько минут
    # ссылка ведет на несуществующую карточку. У консоли эта страховка есть
    # с 6 августа (`send_drafts.site_pending_ids`), у канала ее не было:
    # тот же урок применили к одному из двух мест. Разница между ними в
    # цене ошибки — в консоли пустую ссылку видят двое, в канале
    # подписчики.
    wanted = [d for d, _t in to_send] + [d['id'] for d, _e, _t in to_send_m]
    # У общего поста на сайте должны быть все его карточки, а не только та,
    # под чьим id он записан.
    wanted += [c for d, _t in to_send for c in (deals_by_id_all.get(d) or {}).get('post_covers') or []]
    not_on_site = deals_missing_on_site(wanted)
    # ПОДОЖДАТЬ САЙТ В ЭТОМ ЖЕ ПРОГОНЕ (25 сентября 2026). Без ожидания пост
    # только что одобренной карточки уходил лишь в СЛЕДУЮЩИЙ прогон публикации
    # — через час после того, как карточка уже легла в `main`: «Т-Технологии»/
    # «Точка» применена в 10:18 МСК, пост — в 11:18; Element/ПИК — 10:19 и
    # 11:33. `--wait-for-site N` (после git push) опрашивает сайт раз в минуту
    # до N минут: сайт подтягивает базу раз в DATA_REFRESH_MINUTES (5), и
    # пост уходит в том же прогоне.
    deadline = time.monotonic() + wait_for_site * 60
    while not_on_site and write and time.monotonic() < deadline:
        print('Жду, пока сайт покажет %d карточ. (%s)…' % (len(not_on_site), ', '.join(sorted(not_on_site))))
        time.sleep(SITE_POLL_S)
        not_on_site = deals_missing_on_site(wanted)
    if not_on_site:
        covers_of = lambda d: set((deals_by_id_all.get(d) or {}).get('post_covers') or [])
        to_send = [(d, t) for d, t in to_send if d not in not_on_site and not (covers_of(d) & not_on_site)]
        to_send_m = [(deal, e, t) for deal, e, t in to_send_m
                     if deal['id'] not in not_on_site]
        print('Отложено до следующего прогона: %d — сайт еще не отдает эти '
              'карточки, ссылка в посте вела бы в никуда (%s).'
              % (len(not_on_site), ', '.join(sorted(not_on_site))))

    # П3-10: решение читающего — «эта карточка сейчас не идет», даже если
    # механическая вычитка ее пропустила. Не помечается отправленной —
    # следующий прогон увидит ее заново, если ее не отредактируют иначе.
    skipped = [did for did, _t in to_send if did in skip_ids] + \
              [did for did, _m, _t in to_edit if did in skip_ids]
    if skip_ids:
        to_send = [(d, t) for d, t in to_send if d not in skip_ids]
        to_edit = [(d, m, t) for d, m, t in to_edit if d not in skip_ids]
        to_send_m = [(deal, event, t) for deal, event, t in to_send_m if deal['id'] not in skip_ids]

    print('Новых постов: %d, правок существующих: %d, без поста по решению: %d, новых вех: %d'
          % (len(to_send), len(to_edit), len(to_seed), len(to_send_m)))
    if needs_review:
        # П2-9: не тормоз — окно. Карточка не потеряна, просто первый пост
        # ждет того же чтения источника, что и дневной обыск G7: тот же
        # review.py-путь, сеть и модель есть у рутины, не у этого скрипта.
        print('Ждут дочитывания перед первым постом (пусты сверх заголовка, П2-9): %d — %s'
              % (len(needs_review), ', '.join(needs_review)))
    if flagged:
        print('Вычитка задержала постов: %d (в канал не уйдут, нужен человек).' % len(flagged))
        for did, problems in flagged:
            print('   %s: %s' % (did, '; '.join(problems)))
    if skipped:
        print('Пропущено по --skip (%d): %s' % (len(skipped), ', '.join(skipped)))
    if m_flagged:
        print('Вычитка задержала вех: %d.' % len(m_flagged))
        for eid, problems in m_flagged:
            print('   %s: %s' % (eid, '; '.join(problems)))
    if m_hold:
        print('Вех ждут решения/тишины: %d.' % len(m_hold))

    # П3-10: пока пост не отправлен — печатаем его ПОЛНЫЙ текст, а не три
    # штуки по 400 знаков. Рутина публикации САМА модель: до этой правки
    # сухой прогон с настоящим токеном печатал только счетчики, и читать
    # перед отправкой было physически нечего (просьба владельца 25 августа,
    # «давай читать пост перед публикацией», бриф Этап 10 П3-10).
    show_full_texts = not write or not token or not chat_id
    if show_full_texts and (to_send or to_edit or to_send_m):
        print('\nТЕКСТЫ ДЛЯ ПРОВЕРКИ ПЕРЕД ОТПРАВКОЙ:')
        deals_by_id_ = {d['id']: d for d in data['deals']}

        def where_to(deal):
            return channels.destination(deal) if realty_chat or not token else 'В КАНАЛ'
        for did, text in to_send:
            print('\n--- новый пост: %s · %s ---\n%s' % (did, where_to(deals_by_id_[did]), text))
        for did, _mid, text in to_edit:
            print('\n--- правка поста: %s ---\n%s' % (did, text))
        for deal, event, text in to_send_m:
            print('\n--- веха: %s · %s ---\n%s' % (event['id'], where_to(deal), text))
        print('\nПрочитайте тексты выше. Пост со смысловой чушью (сторона не похожа на '
             'сторону, предложение обрывается на полуслове, число явно не к месту, факт из '
             'чужого абзаца) не отправляйте: перечислите такие id в `--skip <id> [<id>…]` и '
             'назовите причину в отчете.')

    if not token or not chat_id:
        print('TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID не заданы — не отправляю, только показываю план.')
        return

    if not write:
        print('Сухой прогон с настоящим токеном: не отправляю. Запись — с ключом --write.')
        return

    # Лимит и пауза — см. docstring («защита от первого запуска»). Правки
    # делят лимит с новыми постами: считаем оба списка одной очередью, а не
    # отдельными лимитами каждый, иначе включенная одновременно куча правок
    # обойдет защиту с другой стороны. Вехи в дневное окно намеренно НЕ
    # уложены (упрощение v1, раздел A): они редки — по замеру на живой базе
    # 22 августа 2026 их пока 0 отправленных вообще, — и добавлять
    # распределение по часам для события, которое может не случиться неделями,
    # значило бы усложнять код ради еще не наступившей проблемы; если частота
    # вырастет, вернуться и измерить, а не гадать порог заранее.
    # Равномерная выдача. Ключ `--now` ее отключает: он для ручного запуска,
    # когда владелец сам решил опубликовать все немедленно.
    if ignore_pace or '--now' in sys.argv:
        allow, why = len(to_send), 'ключ --now: равномерная выдача отключена'
    else:
        allow, why = pace_allowance(len(to_send))
    print('Темп: %s' % why)
    held = to_send[allow:]
    to_send = to_send[:allow]
    if held:
        print('Придержано новых постов: %d — уйдут следующими прогонами.' % len(held))
    # СВОДКА — ДО раннего выхода. Самый частый для нее день (начало месяца,
    # новых сделок еще нет) — это ровно тот прогон, который выходит здесь.
    digest_failed = None
    if write and digest_action and digest_text:
        digest_saved, digest_failed = deliver_digest(
            digest_action, digest_key_, digest_text, token, chat_id, digests, now_utc)
    else:
        digest_saved = False

    if not to_send and not to_edit and not to_send_m and not m_discard_ids:
        # Засев «без поста» — тоже изменение состояния: не записать его —
        # значит показывать эти карточки в плане каждый прогон заново.
        if to_seed or digest_saved or dropped_edits:
            for did in to_seed:
                posts[did] = None
            with open(DATA, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print('Постов нет; засеяно без поста: %d.' % len(to_seed))
        else:
            print('Отправлять сейчас нечего.')
        if digest_failed:
            print('Сводка %s не ушла: %s' % (digest_key_, digest_failed))
        approve.consume(m_handle, digest_decision_ids + edit_decision_ids)
        return

    queue = [('send', did, text) for did, text in to_send] + \
            [('edit', did, (mid, text)) for did, mid, text in to_edit] + \
            [('milestone', deal['id'], (event, text)) for deal, event, text in to_send_m]
    batch, rest = queue[:MAX_SENDS_PER_RUN], queue[MAX_SENDS_PER_RUN:]
    if rest:
        print('Лимит за прогон: %d. В очереди еще %d — доберем в следующих прогонах.'
              % (MAX_SENDS_PER_RUN, len(rest)))

    # ТЕКСТ ВЛАДЕЛЬЦА, ПРИСЛАННЫЙ ПОСЛЕ ТОГО, КАК approve.py ЗАБРАЛ РЕШЕНИЯ.
    # 29 октября 2026, Velle (g3555ea6e): кнопка «опубликовать» нажата, прогон
    # публикации применил ее и ушел в pytest на двадцать минут; за это время
    # владелец ответил на проект поста своим текстом — а пост вышел
    # автотекстом («мне показали проект поста, я его поменял, а потом он
    # выложил пост без моих правок»). Решение с текстом лежало на сайте, но
    # его читал только approve.py — для карточки, которой в очереди уже нет.
    # Первый пост берет такой текст здесь, прямо перед отправкой.
    late = late_owner_texts(m_decisions)
    by_id = {d['id']: d for d in data['deals']}
    augmented = []
    for kind, did, payload in batch:
        deal = by_id.get(did)
        if kind == 'send' and deal and did in late:
            deal['post_override'] = late[did][0]
            payload = initial_post_text(deal, comps)
            print('  %s: пост уйдет текстом владельца, присланным после решения' % did)
        augmented.append((kind, did, payload))
    batch = augmented

    deals_by_id = {d['id']: d for d in data['deals']}
    manual_edits = site_channel_edits() if write and any(b[0] == 'edit' for b in batch) else {}
    client = _client()
    sent, edited, milestoned, failed, deleted = 0, 0, 0, [], []
    prev_kind = None
    paced = write and not (ignore_pace or '--now' in sys.argv)
    # --finish (владелец, 24 октября 2026: «приоритетно всегда заканчивать с
    # выпуском постов, а потом уже … остальные плановые задачи»): прогон
    # публикации ждет паузы между постами сколько нужно и выпускает всю
    # очередь, а не отдает остаток следующему прогону через 45 минут. Пауза
    # 20 минут и дневное окно остаются.
    finish = '--finish' in sys.argv
    if paced:
        # Правки — первыми: они не ждут паузы между новыми постами.
        batch = [b for b in batch if b[0] == 'edit'] + [b for b in batch if b[0] != 'edit']
    waited, gap_held = 0.0, 0

    def save_progress():
        if realty_posts:
            data['telegram_posts_realty'] = realty_posts
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)

    for i, (kind, did, payload) in enumerate(batch):
        new_post = kind in ('send', 'milestone')
        if new_post and paced:
            wait = gap_wait_s(data.get('telegram_last_post_at'))
            if wait and ((waited + wait > RUN_WAIT_S and not finish) or not in_window_after(wait)):
                gap_held += 1
                continue
            if wait:
                print('Пауза %d мин перед следующим постом (между новыми постами — %d мин).'
                      % (round(wait / 60), int(GAP_S // 60)), flush=True)
                time.sleep(wait)
                waited += wait
        elif i:
            # Без паузы-20 (--now, сухие тесты): два новых поста подряд все
            # равно разводим на SPREAD_S, остальное — технической паузой.
            time.sleep(SPREAD_S if (new_post and prev_kind in ('send', 'milestone')) else SEND_DELAY_S)
        prev_kind = kind
        if kind == 'send' and paced and already_posted_on_disk(did):
            print('  %s: пост уже вышел (записан другим прогоном) — второй раз не шлю' % did)
            continue
        deal = deals_by_id.get(did) or {'id': did}
        buttons = format_post.render_buttons(deal)
        if kind in ('send', 'milestone'):
            text = payload if kind == 'send' else payload[1]
            route = channels.channels_for(deal, realty_known=bool(realty_chat))
            mids, error = post_to_channels(client, token, addr, route, text, buttons)
            if error:
                failed.append((did, error))
            if not mids:
                continue
            # Записываем то, что УЖЕ вышло, даже если второй канал упал:
            # иначе следующий прогон повторил бы пост в первом.
            if kind == 'send':
                posts[did] = mids.get(channels.MAIN)
                if channels.REALTY in mids:
                    realty_posts[did] = mids[channels.REALTY]
                post_state[did] = post_snapshot(deal)
                if did in late:
                    m_sent_decision_ids.append(late[did][1])
                sent += 1
            else:
                record = {'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
                if channels.MAIN in mids:
                    record['message_id'] = mids[channels.MAIN]
                if channels.REALTY in mids:
                    record['realty_message_id'] = mids[channels.REALTY]
                milestones[payload[0]['id']] = record
                milestoned += 1
            data['telegram_last_post_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
            if paced:
                save_progress()
            continue
        where, text = payload
        done = False
        for ch, mid in where.items():
            if manual_edits is None:
                print('  %s: правку поста %s откладываю — сайт не сказал, правили ли его руками' % (did, mid))
                continue
            if ('%s:%s' % (addr.get(ch), mid)) in manual_edits and did not in approved_edit_ids:
                # Пост поправил человек прямо в канале — его текст сильнее
                # автоправки (21 октября 2026, Swordfish Security: «Я уже
                # поправил пост!!!»).
                print('  %s: пост %s поправлен в канале вручную — автоправку не делаю' % (did, mid))
                post_state[did] = post_snapshot(deal)
                continue
            if not addr.get(ch):
                failed.append((did, 'адрес канала «%s» неизвестен — правка поста %s не сделана' % (ch, mid)))
                continue
            try:
                edit_message(client, token, addr[ch], mid, text, buttons)
                done = True
            except TelegramError as e:
                # П4-10: удаленный из канала пост (человек убрал его руками —
                # ни один наш скрипт message_id не трогает) — не такая же
                # ошибка, как сбой сети или неверный токен. Отдельный список и
                # явная формулировка нужны, чтобы рутина не пропустила вопрос,
                # требующий решения человека (перепостить или пометить «без
                # поста»), среди обычных ошибок.
                if is_message_gone(str(e)):
                    deleted.append((did, mid, ch))
                else:
                    failed.append((did, str(e)))
        edited += done
        if done:
            post_state[did] = post_snapshot(deal)
            if did in approved_edit_ids:
                deal['post_override'] = deal.pop('post_edit_proposal', text)

    if digest_failed:
        failed.append(('сводка %s' % digest_key_, digest_failed))

    for did in to_seed:
        posts[did] = None
    for event_id in m_rejected:
        milestones[event_id] = {'no_post': True,
                                'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    if realty_posts:
        data['telegram_posts_realty'] = realty_posts
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    # Решения по вехам консуммируются ПОСЛЕ того, как их эффект (сообщение
    # ушло, id записан) уже лег на диск в том же json.dump выше — дедуп на
    # повторной выборке того же решения держит `milestones[event_id]`, а не
    # факт консумации (см. комментарий в начале main()), поэтому здесь можно
    # без второго прохода `--consume` после git push, в отличие от approve.py.
    approve.consume(m_handle, m_discard_ids + m_sent_decision_ids + digest_decision_ids + edit_decision_ids)
    print('Отправлено новых: %d, отредактировано: %d, засеяно без поста: %d, вех отправлено: %d, ошибок: %d'
          % (sent, edited, len(to_seed), milestoned, len(failed)))
    if gap_held:
        print('Придержано паузой между постами: %d — уйдут следующим прогоном.' % gap_held)
    for did, err in failed:
        print('  %s: %s' % (did, err))
    if deleted:
        print('УДАЛЕННЫЕ ПОСТЫ (%d) — нужно решение человека, не сбой:' % len(deleted))
        for did, mid, ch in deleted:
            title = (deals_by_id.get(did) or {}).get('title', did)
            store = 'telegram_posts_realty' if ch == channels.REALTY else 'telegram_posts'
            print('  пост сделки «%s» (%s, message_id %s) удален из канала%s — '
                 'перепостить (снять message_id из %s и запустить снова) '
                 'или пометить «без поста»' % (title, did, mid,
                                               ' недвижимости' if ch == channels.REALTY else '', store))


def parse_skip_ids(argv):
    """id'ы после `--skip`, до следующего `--`-флага или конца строки —
    тот же легкий разбор без argparse, что уже используется для `--now`."""
    if '--skip' not in argv:
        return frozenset()
    i = argv.index('--skip') + 1
    ids = []
    while i < len(argv) and not argv[i].startswith('--'):
        ids.append(argv[i])
        i += 1
    return frozenset(ids)


def parse_wait_minutes(argv):
    """`--wait-for-site N` → N минут (по умолчанию 0 — не ждать)."""
    if '--wait-for-site' not in argv:
        return 0
    i = argv.index('--wait-for-site') + 1
    try:
        return max(0, int(argv[i]))
    except (IndexError, ValueError):
        return 15


if __name__ == '__main__':
    main('--write' in sys.argv, skip_ids=parse_skip_ids(sys.argv),
         wait_for_site=parse_wait_minutes(sys.argv))
