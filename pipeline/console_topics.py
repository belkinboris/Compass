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


def review_group_id():
    """Актуальный id группы-консоли, если сайт его уже знает.

    4 сентября 2026 включение тем в группе незаметно превратило её в
    супергруппу — Bot API при этом ВСЕГДА меняет chat_id, старый номер
    умирает («group chat was upgraded to a supergroup chat»). Переменная
    окружения `TELEGRAM_REVIEW_GROUP_ID` могла остаться со старым значением
    и выглядеть настроенной, ничего не сигналя об ошибке заранее. Сайт узнаёт
    свежий id из любого сообщения владельца/партнёра в группе и хранит его —
    это надёжнее, чем номер, вписанный один раз и забытый."""
    global _group_cache
    if _group_cache is not None:
        return _group_cache or None
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    _group_cache = ''
    if not token:
        return None
    try:
        import httpx
        r = httpx.get('%s/api/moderation/group' % site, params={'token': token}, timeout=20)
        if r.status_code == 200:
            _group_cache = r.json().get('chat_id') or ''
    except Exception:                                       # noqa: BLE001
        pass
    return _group_cache or None


def console_chats():
    """Куда слать сообщения консоли: группа в первую очередь (сайт знает
    свежий id — см. review_group_id — иначе TELEGRAM_REVIEW_GROUP_ID из
    окружения), без неё — личные id из TELEGRAM_REVIEW_CHAT_IDS. Общее место
    для send_drafts.py, send_access_requests.py, send_open_questions.py и
    ops_status.py — раньше каждый читал переменные по-своему, и обновлять
    логику приходилось в четырёх местах сразу."""
    group = review_group_id() or os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip()
    if group:
        return [group]
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',') if x.strip()]


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
