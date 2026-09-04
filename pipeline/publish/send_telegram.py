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
`TELEGRAM_WINDOW` (по умолчанию 10:00–21:00 МСК). Ночью новые посты не
отправляются вовсе — никого не будим; правки уже опубликованных постов идут
всегда, `editMessageText` уведомления не даёт. Подробности расчёта — у
`pace_allowance()`.

Запуск:
    python3 pipeline/publish/send_telegram.py              # сухой прогон
    python3 pipeline/publish/send_telegram.py --write      # отправить свою долю
    python3 pipeline/publish/send_telegram.py --write --now  # отправить всё сразу
    python3 pipeline/publish/send_telegram.py --write --skip gX1 gX2
        # П3-10: отправить всё, КРОМЕ перечисленных сделок — решение читающего
        # ПОСЛЕ того, как он прочёл полные тексты в сухом прогоне (см. ниже),
        # не механическая находка check_post.py. Пропущенные не помечаются
        # отправленными: следующий прогон покажет их снова.
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
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import approve  # noqa: E402  (fetch_decisions/consume — тот же мост, что у карточек)
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
# @имя публичного канала видит любой подписчик — не секрет, значит, надёжнее
# держать его в коде, где оно не потеряется.
#
# 4 сентября 2026 канал сделали ПРИВАТНЫМ (чтобы закрытый тест не привёл
# посторонних). У приватного канала @имени нет вовсе: и `sendMessage`, и
# `getChat` по старому имени отвечают «chat not found», публикация встала.
# Постить в него можно — бот там администратор, — но только по ЧИСЛОВОМУ id.
# А этот id, в отличие от @имени, публиковать в открытом репозитории не надо:
# репозиторий публичный, а канал теперь закрытый. Поэтому адрес снова живёт
# только в окружении рутин, а здесь пусто — и если его не положили, скрипт
# говорит об этом прямым текстом, а не бьётся в мёртвое имя.
DEFAULT_CHANNEL = ''
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
    # Клавиатуру передаём и при правке: `editMessageText` без `reply_markup`
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


def fns_client_or_none():
    """Живой клиент ФНС — или `None`, если `API_FNS_KEY` не задан в этом
    окружении. Тихо, не падая: финстрока (П7-9) — украшение поста, а не его
    обязательная часть, и её отсутствие не должно ронять весь прогон."""
    try:
        from fns_client import ApiFnsClient
        return ApiFnsClient()
    except Exception:                                                     # noqa: BLE001
        return None


def build_fin(deal, confirmed_inns, client):
    """{'target': fin_summary()|None, 'buyer': ...} — по confirmed ИНН сторон
    сделки, живым `bo()` (Этап 9, П7-9). `confirmed_inns` — только
    `decision == "confirmed"` (см. `fns_registry.confirmed_inns()`), поэтому
    банки сюда не попадают сами по себе: ФНС для них не даёт коммерческую
    отчётность (форма для банков другая — блок «По данным Банка России» на
    сайте берёт её из ЦБ, не отсюда). Каждая роль — отдельный, независимый
    запрос: сбой по одной стороне не должен стоить финстроки другой стороне
    того же поста. Повторный запрос уже известной организации бесплатен
    (`bo` — лимит «по организациям», см. CLAUDE.md) — считать сторон сделок,
    которые мы и так синхронизируем, можно на каждый прогон."""
    if client is None:
        return {}
    from fns_client import normalize_bo
    fin = {}
    for role in ('target', 'buyer'):
        company_id = deal.get(role)
        inn = confirmed_inns.get(company_id) if company_id else None
        if not inn:
            continue
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


# ---------- ВЕХИ: отдельные посты по закрытому списку видов (раздел A) ------
# Молчание сутки = веха выходит, тот же принцип, что у карточек предпросмотра
# (approve.py's SILENCE_HOURS). Отсчёт — от `event['milestone_drafted_at']`,
# который ставит pipeline/ingest/send_milestone_drafts.py в момент отправки
# черновика в консоль, а не от даты самого этапа (`event['date']`) — молчание
# считается с момента, когда человек МОГ увидеть черновик, а не с момента
# самого события.
MILESTONE_SILENCE_HOURS = 24


def milestone_candidates(deals, stage_posts):
    """Вехи (`newsworthy` + `headline` + вид из закрытого списка), которым ещё
    не отправлен отдельный пост.

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
        if did.startswith('digest~'):
            continue
        if '~' not in did or d.get('verdict') not in ('post_yes', 'post_no'):
            continue
        deal_id, _, kind = did.partition('~')
        event_id = '%s-%s' % (deal_id, kind)
        out[event_id] = (d['verdict'], d['id'])
    return out


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
# Со второго числа: за первое число месяца ещё приезжают сделки последних
# дней — сводка, собранная в ночь на первое, недосчитается их.
DIGEST_FROM_DAY = 2


def digest_due(data, today):
    """Месяц (год, номер), за который сводка ещё не выходила, — или None.

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


def digest_decisions(decisions):
    """{ключ месяца: (вердикт, id решения)} — кнопки сводки используют те же
    вердикты `post_ok`/`post_no`, что карточка и веха; отличает её форма
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
        return 'draft', key, 'черновик ещё не отправлен в консоль', []
    age = digest_age_hours(state, now)
    if age >= DIGEST_SILENCE_HOURS:
        return 'send', key, 'молчание %.0f ч' % age, []
    return None, key, 'ждёт решения (%.0f ч из %d)' % (age, DIGEST_SILENCE_HOURS), []


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
        for chat in chats:
            send_drafts.send_one(client, token, chat,
                                 digest_draft_message(text, key, buttons),
                                 digest_keyboard(key))
        digests[key] = dict(digests.get(key) or {},
                            drafted_at=now.isoformat(timespec='seconds'))
        print('Сводка %s: черновик отправлен в консоль' % key)
        return True, None
    except (TelegramError, OSError) as e:
        # Сводка — не критичный шаг: её сбой не должен ронять отчёт по постам
        # сделок, которые уже ушли.
        return False, str(e)


def digest_keyboard(key):
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:digest~%s:post_ok' % key},
        {'text': '🔕 Без поста', 'callback_data': 'mod:digest~%s:post_no' % key},
    ]]}


def digest_draft_message(text, key, buttons):
    return ('📊 [сводка %s] — В КАНАЛ, на проверку\n'
            'Итоги месяца одним постом. Молчание сутки — выходит как есть; '
            'ответ своим текстом заменит пост.\n'
            '━━━━━━━━━━━━\n%s\n\n%s'
            % (key, text, format_post.buttons_preview(buttons)))


def plan_milestones(deals, stage_posts, decisions, now):
    """(отправить, придержать, отклонённые id решений-заглушек) — чистая
    функция аналогично `approve.plan_actions`, чтобы логика проверялась без
    сети. `discard_ids` — decision id вехам с `post_no`: их надо
    consume'нуть, даже если сама веха никогда не отправится."""
    by_event = milestone_decisions(decisions)
    send, hold, discard_ids, sent_decision_ids = [], [], [], []
    for deal, event in milestone_candidates(deals, stage_posts):
        decision = by_event.get(event['id'])
        if decision and decision[0] == 'post_no':
            discard_ids.append(decision[1])
            continue
        if decision and decision[0] == 'post_yes':
            send.append((deal, event))
            sent_decision_ids.append(decision[1])
            continue
        # Черновик ещё не отправлялся (нет milestone_drafted_at) — не
        # кандидат на молчание, его отправит send_milestone_drafts.py.
        if not event.get('milestone_drafted_at'):
            hold.append((deal, event, 'черновик ещё не отправлен в консоль'))
            continue
        age = milestone_age_hours(event, now)
        if age >= MILESTONE_SILENCE_HOURS:
            send.append((deal, event))
        else:
            hold.append((deal, event, 'ждёт решения (%.0f ч из %d)' % (age, MILESTONE_SILENCE_HOURS)))
    return send, hold, discard_ids, sent_decision_ids


def main(write, ignore_pace=False, skip_ids=frozenset()):
    """`ignore_pace` — то же, что ключ `--now`, но параметром.

    Нужен тестам: они проверяют лимит сообщений за прогон и правило бэклога, а
    не дневное окно, и без явного обхода темпа проходили бы только с 10 до 21
    по Москве — то есть падали бы по вечерам, ничего при этом не сломавшись.

    `skip_ids` — П3-10: id сделок, которые НЕ уходят в этот прогон, даже если
    прошли механическую вычитку (`check_post.py`) — решение читающего (рутина
    публикации ПОСЛЕ того, как прочла полные тексты в сухом прогоне), не
    ошибка формата. Не помечаются отправленными: следующий прогон увидит их
    заново, если владелец не решит иначе."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID', '') or DEFAULT_CHANNEL
    if chat_id.startswith('@'):
        # Канал закрыт с 4 сентября 2026, и @имени у него нет. Сказать это
        # словами дешевле, чем разбирать «chat not found» второй раз.
        print('ВНИМАНИЕ: адрес канала задан именем (%s), а канал закрытый — '
              'по имени он боту не виден. Нужен числовой id канала в '
              'TELEGRAM_CHANNEL_ID.' % chat_id)
    elif not chat_id:
        print('ВНИМАНИЕ: адрес канала не задан. Положите числовой id канала '
              'в TELEGRAM_CHANNEL_ID — у закрытого канала другого адреса нет.')
    data = json.load(open(DATA, encoding='utf-8'))
    posts = data.setdefault('telegram_posts', {})
    milestones = data.setdefault('telegram_milestones', {})
    comps = data['companies']
    updates_by_id = load_today_updates()

    # ВЕХИ (раздел A). Решения приходят с сайта тем же мостом, что и у
    # карточек (approve.fetch_decisions) — консуммируются здесь же, сразу:
    # в отличие от approve.py, дедуп вехи не зависит от того, подтвердил ли
    # сайт «применено» — он держится на `milestones[event_id]` (git-нативно,
    # см. docstring `milestone_candidates`), поэтому двухфазный `--consume`
    # не нужен: повторная выборка того же решения безопасна в любом порядке.
    m_decisions, m_handle = approve.fetch_decisions()
    now_utc = datetime.now(timezone.utc)
    m_send, m_hold, m_discard_ids, m_sent_decision_ids = plan_milestones(
        data['deals'], milestones, m_decisions, now_utc)

    # МЕСЯЧНАЯ СВОДКА (просьба владельца 2 сентября 2026). Тот же путь, что у
    # вехи: черновик в консоль -> сутки молчания -> публикация. Живёт здесь, а
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

    to_send, to_edit, to_seed, needs_review = [], [], [], []
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
                    # П2-9: пустая, ещё не прочитанная карточка ждёт дочитывания,
                    # а не уходит первым постом со всеми пустыми линзами.
                    if not deal.get('post_override') and format_post.needs_review_before_post(deal):
                        needs_review.append(did)
                    else:
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
            # П2-9: та же дочитка — но для самого обычного, первого-в-жизни
            # поста. `post_override` пропускает гейт: там уже есть текст,
            # который владелец продиктовал сам, — читать за него нечего.
            if not deal.get('post_override') and format_post.needs_review_before_post(deal):
                needs_review.append(did)
            else:
                # Текст, который владелец продиктовал в Telegram при модерации
                # черновика, важнее автоформата — но только для ПЕРВОГО поста:
                # дальнейшие обновления снова собирает format_post.
                text = (format_post.strip_platform_links(deal['post_override'])
                        if deal.get('post_override') else format_post.render(deal, comps))
                to_send.append((did, text))

    # ВЫЧИТКА ПЕРЕД ОТПРАВКОЙ — ДО отчёта и до выхода из сухого прогона: план
    # читает человек, и задержанные посты он должен видеть именно в плане.
    # Пост наследует дефекты карточки и показывает их публично: 9 августа
    # четыре поста подряд ушли с падежом вместо именительного («Предмет:
    # Дальневосточного банка»), и заметил это читатель, а не пайплайн.
    # Проверка механическая (без сети и токенов) и НЕ молчаливая: подозрительный
    # пост не уходит в канал, а называется в отчёте прогона — дальше его судьбу
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

    # П3-10: решение читающего — «эта карточка сейчас не идёт», даже если
    # механическая вычитка её пропустила. Не помечается отправленной —
    # следующий прогон увидит её заново, если её не отредактируют иначе.
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
        # ждёт того же чтения источника, что и дневной обыск G7: тот же
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
    # сухой прогон с настоящим токеном печатал только счётчики, и читать
    # перед отправкой было physически нечего (просьба владельца 25 августа,
    # «давай читать пост перед публикацией», бриф Этап 10 П3-10).
    show_full_texts = not write or not token or not chat_id
    if show_full_texts and (to_send or to_edit or to_send_m):
        print('\nТЕКСТЫ ДЛЯ ПРОВЕРКИ ПЕРЕД ОТПРАВКОЙ:')
        for did, text in to_send:
            print('\n--- новый пост: %s ---\n%s' % (did, text))
        for did, _mid, text in to_edit:
            print('\n--- правка поста: %s ---\n%s' % (did, text))
        for deal, event, text in to_send_m:
            print('\n--- веха: %s ---\n%s' % (event['id'], text))
        print('\nПрочитайте тексты выше. Пост со смысловой чушью (сторона не похожа на '
             'сторону, предложение обрывается на полуслове, число явно не к месту, факт из '
             'чужого абзаца) не отправляйте: перечислите такие id в `--skip <id> [<id>…]` и '
             'назовите причину в отчёте.')

    if not token or not chat_id:
        print('TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID не заданы — не отправляю, только показываю план.')
        return

    if not write:
        print('Сухой прогон с настоящим токеном: не отправляю. Запись — с ключом --write.')
        return

    # Лимит и пауза — см. docstring («защита от первого запуска»). Правки
    # делят лимит с новыми постами: считаем оба списка одной очередью, а не
    # отдельными лимитами каждый, иначе включённая одновременно куча правок
    # обойдёт защиту с другой стороны. Вехи в дневное окно намеренно НЕ
    # уложены (упрощение v1, раздел A): они редки — по замеру на живой базе
    # 22 августа 2026 их пока 0 отправленных вообще, — и добавлять
    # распределение по часам для события, которое может не случиться неделями,
    # значило бы усложнять код ради ещё не наступившей проблемы; если частота
    # вырастет, вернуться и измерить, а не гадать порог заранее.
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
    # СВОДКА — ДО раннего выхода. Самый частый для неё день (начало месяца,
    # новых сделок ещё нет) — это ровно тот прогон, который выходит здесь.
    digest_failed = None
    if write and digest_action and digest_text:
        digest_saved, digest_failed = deliver_digest(
            digest_action, digest_key_, digest_text, token, chat_id, digests, now_utc)
    else:
        digest_saved = False

    if not to_send and not to_edit and not to_send_m and not m_discard_ids:
        # Засев «без поста» — тоже изменение состояния: не записать его —
        # значит показывать эти карточки в плане каждый прогон заново.
        if to_seed or digest_saved:
            for did in to_seed:
                posts[did] = None
            with open(DATA, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print('Постов нет; засеяно без поста: %d.' % len(to_seed))
        else:
            print('Отправлять сейчас нечего.')
        if digest_failed:
            print('Сводка %s не ушла: %s' % (digest_key_, digest_failed))
        approve.consume(m_handle, digest_decision_ids)
        return

    queue = [('send', did, text) for did, text in to_send] + \
            [('edit', did, (mid, text)) for did, mid, text in to_edit] + \
            [('milestone', deal['id'], (event, text)) for deal, event, text in to_send_m]
    batch, rest = queue[:MAX_SENDS_PER_RUN], queue[MAX_SENDS_PER_RUN:]
    if rest:
        print('Лимит за прогон: %d. В очереди ещё %d — доберём в следующих прогонах.'
              % (MAX_SENDS_PER_RUN, len(rest)))

    # Финстрока сторон из ФНС (Этап 9, П7-9) — ЗДЕСЬ, а не при сборке
    # to_send/to_edit: тот список — весь непубликованный бэклог (в реальной
    # базе — тысячи карточек), и живой запрос `bo()` на каждую сторону
    # каждой из них означал бы тысячи сетевых вызовов за прогон ради
    # ≤MAX_SENDS_PER_RUN штук, которые реально уйдут. Дорисовываем только
    # УЖЕ ОТОБРАННЫЙ батч. `fns_client_or_none()` тихо отдаёт `None` без
    # сети/без ключа — тогда `build_fin()` для каждой сделки честно
    # возвращает {}, посты уходят без финстроки, а не падают.
    fns_client = fns_client_or_none()
    if fns_client is not None:
        from pipeline import fns_registry
        confirmed_inns = fns_registry.confirmed_inns()
        by_id = {d['id']: d for d in data['deals']}
        augmented = []
        for kind, did, payload in batch:
            deal = by_id.get(did)
            if kind in ('send', 'edit') and deal and not deal.get('post_override'):
                fin = build_fin(deal, confirmed_inns, fns_client)
                if fin:
                    if kind == 'send':
                        payload = format_post.render(deal, comps, fin=fin)
                    else:
                        mid, _old_text = payload
                        payload = (mid, format_post.render(deal, comps, updates=updates_by_id.get(did), fin=fin))
            augmented.append((kind, did, payload))
        batch = augmented
        fns_client.close()

    deals_by_id = {d['id']: d for d in data['deals']}
    client = _client()
    sent, edited, milestoned, failed, deleted = 0, 0, 0, [], []
    prev_kind = None
    for i, (kind, did, payload) in enumerate(batch):
        if i:
            # Два новых поста подряд разводим по времени, всё остальное —
            # обычной технической паузой. Веха — тоже НОВОЕ сообщение
            # (sendMessage, не editMessageText), поэтому та же логика, что у
            # 'send': подряд с любым другим новым постом — разводим по времени.
            time.sleep(SPREAD_S if (kind in ('send', 'milestone') and prev_kind in ('send', 'milestone'))
                      else SEND_DELAY_S)
        prev_kind = kind
        try:
            buttons = format_post.render_buttons(deals_by_id.get(did) or {'id': did})
            if kind == 'send':
                posts[did] = post_message(client, token, chat_id, payload, buttons)
                sent += 1
            elif kind == 'milestone':
                event, text = payload
                mid = post_message(client, token, chat_id, text, buttons)
                milestones[event['id']] = {'message_id': mid,
                                           'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
                milestoned += 1
            else:
                mid, text = payload
                edit_message(client, token, chat_id, mid, text, buttons)
                edited += 1
        except TelegramError as e:
            # П4-10: удалённый из канала пост (человек убрал его руками — ни
            # один наш скрипт message_id не трогает) — не такая же ошибка, как
            # сбой сети или неверный токен. Раньше ЛЮБАЯ TelegramError на
            # правке просто копилась в общий список и терялась в потоке
            # отчёта; отдельный список и явная формулировка нужны, чтобы
            # рутина не пропустила вопрос, требующий решения человека
            # (перепостить или пометить «без поста»), среди обычных ошибок.
            if kind == 'edit' and is_message_gone(str(e)):
                deleted.append((did, payload[0]))
            else:
                failed.append((did, str(e)))

    if digest_failed:
        failed.append(('сводка %s' % digest_key_, digest_failed))

    for did in to_seed:
        posts[did] = None
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    # Решения по вехам консуммируются ПОСЛЕ того, как их эффект (сообщение
    # ушло, id записан) уже лёг на диск в том же json.dump выше — дедуп на
    # повторной выборке того же решения держит `milestones[event_id]`, а не
    # факт консумации (см. комментарий в начале main()), поэтому здесь можно
    # без второго прохода `--consume` после git push, в отличие от approve.py.
    approve.consume(m_handle, m_discard_ids + m_sent_decision_ids + digest_decision_ids)
    print('Отправлено новых: %d, отредактировано: %d, засеяно без поста: %d, вех отправлено: %d, ошибок: %d'
          % (sent, edited, len(to_seed), milestoned, len(failed)))
    for did, err in failed:
        print('  %s: %s' % (did, err))
    if deleted:
        print('УДАЛЁННЫЕ ПОСТЫ (%d) — нужно решение человека, не сбой:' % len(deleted))
        for did, mid in deleted:
            title = (deals_by_id.get(did) or {}).get('title', did)
            print('  пост сделки «%s» (%s, message_id %s) удалён из канала — '
                 'перепостить (снять message_id из telegram_posts и запустить снова) '
                 'или пометить «без поста»' % (title, did, mid))


def parse_skip_ids(argv):
    """id'ы после `--skip`, до следующего `--`-флага или конца строки —
    тот же лёгкий разбор без argparse, что уже используется для `--now`."""
    if '--skip' not in argv:
        return frozenset()
    i = argv.index('--skip') + 1
    ids = []
    while i < len(argv) and not argv[i].startswith('--'):
        ids.append(argv[i])
        i += 1
    return frozenset(ids)


if __name__ == '__main__':
    main('--write' in sys.argv, skip_ids=parse_skip_ids(sys.argv))
