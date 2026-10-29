# -*- coding: utf-8 -*-
"""Номер темы форума в группе-консоли — для рутин, которые шлют сообщения
из ДРУГОГО процесса, чем сайт.

4 сентября 2026 владелец превратил группу-консоль в форум и завел темы
(«Подтверждение постов», «Обновления», «Общая информация»), чтобы решения,
отчеты рутин и разное не лежали одной кучей: «Возможно развести сообщения
бота по топикам, чтобы все не было в одной куче?»

Bot API не дает список тем группы — номер узнает САЙТ (у него вебхук,
Telegram сам называет номер в служебном сообщении о создании/переименовании
темы; см. `_learn_console_topics` в main.py, тот же прием, что и для адреса
приватного канала). Рутина работает в другом процессе и спрашивает номер по
токену — `/api/moderation/topics`, тот же мост, что у решений модерации.

ИМЕНА ТЕМ ЗДЕСЬ И В main.py — ОДИН И ТОТ ЖЕ СПИСОК, но продублированы: сайт
хранит настройки в своей базе и не знает про pipeline/, а рутина не имеет
доступа к базе сайта напрямую. Оба места — просто строки, дрейф между ними
маловероятен и ничем не грозит (в худшем случае сообщение уйдет в общую
ленту темы, а не в конкретную — не потеря, а неудобство).
"""
import os

TOPIC_NAMES = {
    "decision": "Подтверждение постов",   # чего-то ждет решение владельца/партнера
    "update": "Обновления",               # отчет рутины о прогоне
    "info": "Общая информация",           # служебное: канал отозвался, адрес запомнили
    # Все, что написал ПОСЕТИТЕЛЬ: уточнение с карточки сделки, заметка из
    # футера и обе половины отзыва об ассистенте («Ответ помог?» и «Чем не
    # помог?»). Отзывы жили в «Общей информации» и тонули среди отчетов о
    # прогонах — переехали 22 сентября 2026.
    "user_notes": "Заметки от пользователей",
    # Служебные очереди, где вы отвечаете на ТЕХНИЧЕСКИЙ вопрос, а не решаете
    # судьбу поста: заявки на вход, «какой ИНН у этой компании», однофамильцы
    # в реестре, «не одна ли это сделка». Заведена 22 сентября 2026, чтобы в
    # «Подтверждении постов» остались только посты и карточки.
    "admin": "Админ",
    # Сообщения владельца и партнера агенту Claude и его ответы
    # (pipeline/claude_topic.py, routines/claude_topic.md). 17 октября 2026.
    "claude": "Клод",
}

# Пока номер темы не закреплен (владелец еще не дал /topic внутри нее),
# сообщение уходит НЕ в общую ленту, а в запасную тему: пропасть очереди
# заявок на вход хуже, чем полежать не в той теме.
FALLBACK = {"admin": "decision"}

_cache = None
# Сайт не ответил списком тем (сеть, 5xx) — это не «тема не заведена».
# 29 октября 2026 обрыв связи превращался в отметку «тема не заведена» и
# коммит, а через три часа сайт отвечал — и отметка снималась другим коммитом.
_unreachable = False


def site_answered() -> bool:
    """Последний запрос списка тем дошел до сайта и вернул ответ."""
    _fetch_topics()
    return not _unreachable


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
    global _unreachable
    _cache = {}
    if not token:
        return _cache
    try:
        import httpx
        r = httpx.get('%s/api/moderation/topics' % site, params={'token': token}, timeout=20)
        if r.status_code == 200:
            _cache = r.json().get('topics') or {}
        else:
            _unreachable = True
    except Exception:                                       # noqa: BLE001
        _unreachable = True
    return _cache


_group_cache = None
_group_source = None


def migrated_chat_id(data) -> str | None:
    """Новый номер чата, если Telegram отказал словами «группа стала
    супергруппой». Telegram отдает его прямо в отказе
    (`parameters.migrate_to_chat_id`) — значит, адрес не потерян, и
    единственно верная реакция на такой отказ не «сообщить о сбое», а
    повторить отправку по названному номеру. 6 сентября 2026 рутина вместо
    этого час за часом писала владельцу, что ждет от него сообщения."""
    if not isinstance(data, dict) or data.get('ok'):
        return None
    new = (data.get('parameters') or {}).get('migrate_to_chat_id')
    return str(new) if new else None


def address_note() -> str | None:
    """Откуда взят адрес консоли, если НЕ от сайта, — строка для отчета.
    Молчать здесь нельзя: переменная окружения контейнера могла остаться со
    старым номером и выглядеть настроенной, а рутина, не сказав об этом,
    придумывает диагноз вместо того, чтобы назвать факт."""
    if _group_source == 'сайт' or _group_source is None:
        return None
    return 'адрес консоли взят из переменной окружения (сайт не ответил) — он может быть устаревшим'


def review_group_id():
    """Актуальный id группы-консоли, если сайт его уже знает.

    4 сентября 2026 включение тем в группе незаметно превратило ее в
    супергруппу — Bot API при этом ВСЕГДА меняет chat_id, старый номер
    умирает («group chat was upgraded to a supergroup chat»). Переменная
    окружения `TELEGRAM_REVIEW_GROUP_ID` могла остаться со старым значением
    и выглядеть настроенной, ничего не сигналя об ошибке заранее. Сайт узнает
    свежий id из любого сообщения владельца/партнера в группе и хранит его —
    это надежнее, чем номер, вписанный один раз и забытый."""
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
    # ушедшее в мертвый чат.
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
# 7 сентября 2026 отчет рутины «🔧 Компас · качество» ушел в ПУБЛИЧНЫЙ канал,
# к подписчикам: внутренняя кухня («дополнили 3 карточки», «еще в очереди на
# проверку: 165») на витрине проекта. Владелец удалил пост руками.
#
# Как это стало возможно. Адрес консоли берется у сайта, а если сайт не
# ответил — из переменной окружения `TELEGRAM_REVIEW_GROUP_ID`. В контейнере
# рутин эта переменная содержала номер КАНАЛА (тот же, что
# `TELEGRAM_CHANNEL_ID`), а сайт в ту минуту перезапускался после сборки —
# и запасной путь честно отработал, отправив отчет по неверному адресу.
#
# Вывод не «сделать запасной путь надежнее»: любой запасной путь однажды
# сработает, и цена ошибки здесь несимметрична. Сообщение консоли,
# не дошедшее до владельца, — неудобство; сообщение консоли, ушедшее
# подписчикам, — публичный ущерб. Поэтому адрес канала ВЫЧЕРКИВАЕТСЯ из
# кандидатов в консоль всегда, откуда бы он ни пришел, а если после этого
# группы не осталось — пишем лично владельцу и партнеру. Хуже личного
# сообщения быть не может; хуже публикации — может.
def channel_ids() -> set:
    """Адреса канала публикации — все, что мы о нем знаем. Из окружения и,
    если сайт отвечает, из его памяти (он узнает номер приватного канала от
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
                    # Оба канала — основной и «Компас - Недвижимость» (2 октября 2026):
                    # отчет консоли не должен уйти ни в один из них.
                    body = r.json()
                    _channel_cache = ' '.join(str(body.get(k) or '') for k in
                                              ('chat_id', 'realty_chat_id')).strip()
            except Exception:                               # noqa: BLE001
                pass
    ids.update(_channel_cache.split())
    realty_env = (os.environ.get('TELEGRAM_REALTY_CHANNEL_ID') or '').strip()
    if realty_env:
        ids.add(realty_env)
    return ids


def is_channel(chat_id) -> bool:
    """Правда ли, что этот адрес — КАНАЛ, а не группа. Спрашиваем сам Telegram.

    Сравнения с известным номером канала мало, и это выяснилось в тот же
    вечер: владелец, поправляя переменные после утечки, записал в
    `TELEGRAM_CHANNEL_ID` старое @имя канала — а оно перестало существовать,
    когда канал сделали приватным (`getChat` по нему отвечает «chat not
    found»). Номера канала мы после этого не знали ВООБЩЕ, и защита,
    построенная только на сравнении номеров, стала пустой.

    Тип чата — свойство самого чата, его не может «не быть» из-за того, что
    кто-то не так заполнил переменную. Один запрос на процесс, ответ
    запоминается. Сеть не ответила — не блокируем отправку (иначе любая
    заминка загоняла бы все сообщения в личку), но сравнение по номерам
    остается вторым рубежом."""
    chat_id = str(chat_id or '').strip()
    if not chat_id:
        return False
    if chat_id in _type_cache:
        return _type_cache[chat_id]
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    if not token:
        return False
    verdict = False
    try:
        import httpx
        import telegram_endpoint
        r = httpx.post(telegram_endpoint.method_url(token, 'getChat'),
                       json={'chat_id': chat_id}, timeout=20)
        data = r.json()
        if data.get('ok'):
            verdict = str((data.get('result') or {}).get('type') or '') == 'channel'
            _type_cache[chat_id] = verdict
    except Exception:                                       # noqa: BLE001
        pass
    return verdict


def channel_leak_note() -> str | None:
    """Строка для отчета, если адрес канала стоял там, где ждали консоль."""
    return _leak_note


_channel_cache = None
_leak_note = None
_type_cache: dict = {}

def console_chats():
    """Куда слать сообщения консоли: группа в первую очередь (сайт знает
    свежий id — см. review_group_id — иначе TELEGRAM_REVIEW_GROUP_ID из
    окружения), без нее — личные id из TELEGRAM_REVIEW_CHAT_IDS. Общее место
    для send_drafts.py, send_access_requests.py, send_open_questions.py и
    ops_status.py — раньше каждый читал переменные по-своему, и обновлять
    логику приходилось в четырех местах сразу."""
    global _group_source, _leak_note
    forbidden = channel_ids()
    group = review_group_id()
    if group and (str(group) in forbidden or is_channel(group)):
        _leak_note = ('адрес канала публикации стоял как адрес консоли — '
                      'сообщение туда НЕ отправлено')
        group = None
    if not group:
        env = os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip()
        if env and (env in forbidden or is_channel(env)):
            _leak_note = ('TELEGRAM_REVIEW_GROUP_ID указывает на канал публикации, '
                          'а не на группу-консоль — пишу лично владельцу и партнеру')
        elif env:
            group = env
            _group_source = 'переменная окружения'
    if group:
        return [group]
    # Личные адреса — последний рубеж: хуже личного сообщения быть не может,
    # хуже публикации — может. Канал вычеркиваем и отсюда тоже.
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',')
            if x.strip() and x.strip() not in forbidden]


def thread_id(kind: str):
    """Номер темы для сообщений вида `kind` ('decision'/'update'/'info'/'user_notes') —
    или None, если тема еще не заведена/не узнана (сообщение уйдет в общую
    ленту, ничего не потеряется). `TELEGRAM_TOPIC_<KIND>` в окружении
    переопределяет — на случай, если сайту еще не сказали номер, а ждать
    неохота."""
    override = os.environ.get('TELEGRAM_TOPIC_%s' % kind.upper(), '').strip()
    if override.lstrip('-').isdigit():
        return int(override)
    name = TOPIC_NAMES.get(kind)
    if not name:
        return None
    val = _fetch_topics().get(_slug(name))
    if val and str(val).lstrip('-').isdigit():
        return int(val)
    spare = FALLBACK.get(kind)
    return thread_id(spare) if spare else None
