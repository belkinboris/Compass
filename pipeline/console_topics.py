# -*- coding: utf-8 -*-
"""Номер темы форума в группе-консоли — для рутин, которые шлют сообщения
из ДРУГОГО процесса, чем сайт.

4 сентября 2026 владелец превратил группу-консоль в форум и завёл темы
(«Подтверждение постов», «Обновления», «Общая информация»), чтобы решения,
отчёты рутин и разное не лежали одной кучей: «Возможно развести сообщения
бота по топикам, чтобы всё не было в одной куче?»

Bot API не даёт список тем группы — номер узнаёт САЙТ (у него вебхук,
Telegram сам называет номер в служебном сообщении о создании/переименовании
темы; см. `_learn_console_topics` в main.py, тот же приём, что и для адреса
приватного канала). Рутина работает в другом процессе и спрашивает номер по
токену — `/api/moderation/topics`, тот же мост, что у решений модерации.

ИМЕНА ТЕМ ЗДЕСЬ И В main.py — ОДИН И ТОТ ЖЕ СПИСОК, но продублированы: сайт
хранит настройки в своей базе и не знает про pipeline/, а рутина не имеет
доступа к базе сайта напрямую. Оба места — просто строки, дрейф между ними
маловероятен и ничем не грозит (в худшем случае сообщение уйдёт в общую
ленту темы, а не в конкретную — не потеря, а неудобство).
"""
import os

TOPIC_NAMES = {
    "decision": "Подтверждение постов",   # чего-то ждёт решение владельца/партнёра
    "update": "Обновления",               # отчёт рутины о прогоне
    "info": "Общая информация",           # остальное: заметки, отзывы, служебное
}

_cache = None


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^\w\s-]", "", name.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s)


def _fetch_topics() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    _cache = {}
    if not token:
        return _cache
    try:
        import httpx
        r = httpx.get('%s/api/moderation/topics' % site, params={'token': token}, timeout=20)
        if r.status_code == 200:
            _cache = r.json().get('topics') or {}
    except Exception:                                       # noqa: BLE001
        pass
    return _cache


_group_cache = None
_group_source = None


def migrated_chat_id(data) -> str | None:
    """Новый номер чата, если Telegram отказал словами «группа стала
    супергруппой». Telegram отдаёт его прямо в отказе
    (`parameters.migrate_to_chat_id`) — значит, адрес не потерян, и
    единственно верная реакция на такой отказ не «сообщить о сбое», а
    повторить отправку по названному номеру. 6 сентября 2026 рутина вместо
    этого час за часом писала владельцу, что ждёт от него сообщения."""
    if not isinstance(data, dict) or data.get('ok'):
        return None
    new = (data.get('parameters') or {}).get('migrate_to_chat_id')
    return str(new) if new else None


def address_note() -> str | None:
    """Откуда взят адрес консоли, если НЕ от сайта, — строка для отчёта.
    Молчать здесь нельзя: переменная окружения контейнера могла остаться со
    старым номером и выглядеть настроенной, а рутина, не сказав об этом,
    придумывает диагноз вместо того, чтобы назвать факт."""
    if _group_source == 'сайт' or _group_source is None:
        return None
    return 'адрес консоли взят из переменной окружения (сайт не ответил) — он может быть устаревшим'


def review_group_id():
    """Актуальный id группы-консоли, если сайт его уже знает.

    4 сентября 2026 включение тем в группе незаметно превратило её в
    супергруппу — Bot API при этом ВСЕГДА меняет chat_id, старый номер
    умирает («group chat was upgraded to a supergroup chat»). Переменная
    окружения `TELEGRAM_REVIEW_GROUP_ID` могла остаться со старым значением
    и выглядеть настроенной, ничего не сигналя об ошибке заранее. Сайт узнаёт
    свежий id из любого сообщения владельца/партнёра в группе и хранит его —
    это надёжнее, чем номер, вписанный один раз и забытый."""
    global _group_cache, _group_source
    if _group_cache is not None:
        return _group_cache or None
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    _group_cache = ''
    if not token:
        return None
    # Сайт перезапускается при каждой сборке, и прогон рутины легко попадает
    # в эту минуту. Одна неудачная попытка роняла нас на переменную окружения
    # со старым номером — три попытки с паузой дешевле, чем сообщение,
    # ушедшее в мёртвый чат.
    for attempt in range(3):
        try:
            import httpx
            r = httpx.get('%s/api/moderation/group' % site, params={'token': token}, timeout=20)
            if r.status_code == 200:
                _group_cache = r.json().get('chat_id') or ''
                _group_source = 'сайт' if _group_cache else None
                break
        except Exception:                                   # noqa: BLE001
            pass
        if attempt < 2:
            import time
            time.sleep(3 * (attempt + 1))
    return _group_cache or None



# ---------------------------------------------------------------------------
# КОНСОЛЬ И КАНАЛ — РАЗНЫЕ ЧАТЫ, И ПЕРЕПУТАТЬ ИХ НЕЛЬЗЯ НИ ПРИ КАКОМ СБОЕ.
#
# 7 сентября 2026 отчёт рутины «🔧 Компас · качество» ушёл в ПУБЛИЧНЫЙ канал,
# к подписчикам: внутренняя кухня («дополнили 3 карточки», «ещё в очереди на
# проверку: 165») на витрине проекта. Владелец удалил пост руками.
#
# Как это стало возможно. Адрес консоли берётся у сайта, а если сайт не
# ответил — из переменной окружения `TELEGRAM_REVIEW_GROUP_ID`. В контейнере
# рутин эта переменная содержала номер КАНАЛА (тот же, что
# `TELEGRAM_CHANNEL_ID`), а сайт в ту минуту перезапускался после сборки —
# и запасной путь честно отработал, отправив отчёт по неверному адресу.
#
# Вывод не «сделать запасной путь надёжнее»: любой запасной путь однажды
# сработает, и цена ошибки здесь несимметрична. Сообщение консоли,
# не дошедшее до владельца, — неудобство; сообщение консоли, ушедшее
# подписчикам, — публичный ущерб. Поэтому адрес канала ВЫЧЕРКИВАЕТСЯ из
# кандидатов в консоль всегда, откуда бы он ни пришёл, а если после этого
# группы не осталось — пишем лично владельцу и партнёру. Хуже личного
# сообщения быть не может; хуже публикации — может.
def channel_ids() -> set:
    """Адреса канала публикации — всё, что мы о нём знаем. Из окружения и,
    если сайт отвечает, из его памяти (он узнаёт номер приватного канала от
    самого Telegram — см. `_announce_channel_id` в main.py)."""
    ids = set()
    env = (os.environ.get('TELEGRAM_CHANNEL_ID') or '').strip()
    if env:
        ids.add(env)
    global _channel_cache
    if _channel_cache is None:
        _channel_cache = ''
        site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
        token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
        if token:
            try:
                import httpx
                r = httpx.get('%s/api/moderation/channel' % site,
                              params={'token': token}, timeout=20)
                if r.status_code == 200:
                    _channel_cache = str(r.json().get('chat_id') or '')
            except Exception:                               # noqa: BLE001
                pass
    if _channel_cache:
        ids.add(_channel_cache)
    return ids


def channel_leak_note() -> str | None:
    """Строка для отчёта, если адрес канала стоял там, где ждали консоль."""
    return _leak_note


_channel_cache = None
_leak_note = None

def console_chats():
    """Куда слать сообщения консоли: группа в первую очередь (сайт знает
    свежий id — см. review_group_id — иначе TELEGRAM_REVIEW_GROUP_ID из
    окружения), без неё — личные id из TELEGRAM_REVIEW_CHAT_IDS. Общее место
    для send_drafts.py, send_access_requests.py, send_open_questions.py и
    ops_status.py — раньше каждый читал переменные по-своему, и обновлять
    логику приходилось в четырёх местах сразу."""
    global _group_source, _leak_note
    forbidden = channel_ids()
    group = review_group_id()
    if group and str(group) in forbidden:
        _leak_note = ('адрес канала публикации стоял как адрес консоли — '
                      'сообщение туда НЕ отправлено')
        group = None
    if not group:
        env = os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip()
        if env and env in forbidden:
            _leak_note = ('TELEGRAM_REVIEW_GROUP_ID указывает на канал публикации, '
                          'а не на группу-консоль — пишу лично владельцу и партнёру')
        elif env:
            group = env
            _group_source = 'переменная окружения'
    if group:
        return [group]
    # Личные адреса — последний рубеж: хуже личного сообщения быть не может,
    # хуже публикации — может. Канал вычёркиваем и отсюда тоже.
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',')
            if x.strip() and x.strip() not in forbidden]


def thread_id(kind: str):
    """Номер темы для сообщений вида `kind` ('decision'/'update'/'info') —
    или None, если тема ещё не заведена/не узнана (сообщение уйдёт в общую
    ленту, ничего не потеряется). `TELEGRAM_TOPIC_<KIND>` в окружении
    переопределяет — на случай, если сайту ещё не сказали номер, а ждать
    неохота."""
    override = os.environ.get('TELEGRAM_TOPIC_%s' % kind.upper(), '').strip()
    if override.lstrip('-').isdigit():
        return int(override)
    name = TOPIC_NAMES.get(kind)
    if not name:
        return None
    val = _fetch_topics().get(_slug(name))
    return int(val) if val and str(val).lstrip('-').isdigit() else None
