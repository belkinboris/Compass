# -*- coding: utf-8 -*-
"""Свежая база на боевом сайте без пересборки и перезапуска процесса.

ЗАЧЕМ. Timeweb собирает приложение заново на КАЖДЫЙ пуш в ветку, из которой
оно собирается, и перезапускает процесс. Рутины («приток», «публикация»,
«качество», «вычитка») коммитят по 4–5 раз в час, и почти всегда это НЕ код,
а данные: `static/data/deals_promoted.json` и очередь предпросмотра. В ночь на
3 сентября 2026 три пуша за одну минуту наложились друг на друга, и сайт
отдавал 502 больше девяти минут подряд; за сутки владелец дважды не смог
открыть сайт — с телефона и с компьютера. Причина не в объёме данных и не в
коде: пересборка запускалась ради файла, который приложению достаточно просто
прочитать с диска.

РЕШЕНИЕ. Данные и код разъезжаются. Приложение собирается из отдельной ветки
(`release`), куда попадает только код, а свежие данные сайт подтягивает сам,
раз в несколько минут, прямо из ветки `main` публичного репозитория.
Пересборка случается тогда и только тогда, когда меняется код.

ПОЧЕМУ ЭТО НЕ ПЛАНИРОВЩИК РАДИ ПЛАНИРОВЩИКА. Естественного события, которым
сопровождается появление новых данных, у сайта больше НЕТ — раньше им был
деплой (см. `subscription_feed.py`), и именно его мы здесь и отменяем. Значит,
таймер тут не «лишняя деталь, просыпающаяся 24 раза в сутки, чтобы 23 раза
ничего не найти» (правило CLAUDE.md), а единственный способ вообще узнать о
новых данных. Внешний cron при этом не нужен: процесс на хостинге один, и
поток внутри него — то же решение, что уже применено в соседнем проекте
владельца («Автопост», APScheduler в lifespan FastAPI).

ЧТО ИМЕННО КАЧАЕТСЯ — только то, что реально читает сайт и что меняют рутины:
сама база, очередь предпросмотра (без неё ссылки `#/preview/<id>` из консоли
модерации протухнут навсегда, потому что деплоя по их коммитам больше не
будет) и две выгрузки ЦБ. `static/index.html` — КОД и приезжает только
деплоем: интерфейс, прилетевший мимо сборки, невозможно откатить откатом
релиза.

ЧЕСТНОСТЬ ВМЕСТО ОПТИМИЗМА. Урок CLAUDE.md «флаг „загружено" не должен
становиться true после неудачи» здесь главный: недоступный GitHub — не авария
(raw.githubusercontent.com из России отвечает не всегда), сайт продолжает жить
на файле, который приехал деплоем. Но «работает» и «молча не работает» обязаны
различаться снаружи: каждая попытка и каждая ошибка попадают в `status()`, а
он — в `/api/data/status`. Файл на диске не трогается, пока скачанное не
прошло проверку: битая или обрезанная закачка не должна заменить живую базу.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import httpx

import assistant_retrieval
import subscription_feed

logger = logging.getLogger("kompas.data")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Репозиторий ПУБЛИЧНЫЙ: raw.githubusercontent.com отдаёт 200 без токена.
# Держать здесь секрет было бы и лишним, и опасным — сайту не нужно уметь
# ничего сверх чтения того, что и так открыто всему миру.
DATA_REPO = os.environ.get("DATA_REPO", "belkinboris/Compass")
RAW_HOST = os.environ.get("DATA_RAW_HOST", "https://raw.githubusercontent.com")

MAIN_FILE = "static/data/deals_promoted.json"


# Момент импорта модуля — это и есть старт процесса: `main.py` импортирует
# data_refresh на первой же секунде, до подъёма uvicorn. Отдельного способа
# спросить у системы «когда поднялся текущий процесс» без новых зависимостей
# нет, а разница между импортом и стартом — миллисекунды.
_STARTED_AT = time.time()


class RefreshError(RuntimeError):
    """Скачанное не годится для записи на диск — оставляем то, что лежит."""


# --------------------------------------------------------------------------
# Настройки окружения. Читаются на каждый вызов, а не при импорте: тесты
# и владелец меняют их без перезапуска интерпретатора.
# --------------------------------------------------------------------------

def enabled() -> bool:
    """По умолчанию ВКЛЮЧЕНО. На ветке `main` подтягивание безвредно: оно
    скачивает ровно то, что и так уехало бы деплоем."""
    return (os.environ.get("DATA_REFRESH_ENABLED", "1") or "").strip().lower() \
        not in ("0", "false", "no", "off")


def branch() -> str:
    return (os.environ.get("DATA_BRANCH") or "main").strip() or "main"


def interval_seconds() -> float:
    try:
        minutes = float(os.environ.get("DATA_REFRESH_MINUTES", "5"))
    except (TypeError, ValueError):
        minutes = 5.0
    # Нижняя граница — минута: чаще бессмысленно (рутины коммитят реже) и
    # уже похоже на долбёжку чужого сервиса.
    return max(60.0, minutes * 60.0)


def raw_url(path: str) -> str:
    return "%s/%s/%s/%s" % (RAW_HOST.rstrip("/"), DATA_REPO, branch(), path)


def full_path(path: str) -> str:
    return os.path.join(BASE_DIR, *path.split("/"))


# --------------------------------------------------------------------------
# Проверки перед записью. У каждого файла своя: у базы законно только расти,
# а очередь предпросмотра законно пустеет до нуля — общий порог «не меньше
# 90% прежнего» стёр бы её обновление навсегда.
# --------------------------------------------------------------------------

def _count_deals(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0
    deals = data.get("deals") if isinstance(data, dict) else None
    return len(deals) if isinstance(deals, list) else 0


def validate_base(data, disk_path: str) -> str | None:
    """Причина отказа или None. Ловит ровно то, от чего защищаемся: обрезанную
    закачку (сделок вдруг стало заметно меньше), чужой файл (нет `deals`/
    `companies`) и пустышку."""
    if not isinstance(data, dict):
        return "это не объект JSON"
    deals, companies = data.get("deals"), data.get("companies")
    if not isinstance(deals, list) or not deals:
        return "нет непустого списка deals"
    if not isinstance(companies, dict) or not companies:
        return "нет непустого словаря companies"
    ids = {str(d.get("id")) for d in deals if isinstance(d, dict) and d.get("id")}
    if not ids:
        return "ни у одной сделки нет id"
    have = _count_deals(disk_path)
    if have and len(deals) < have * 0.9:
        return ("сделок %d, а на диске уже %d — падение больше 10%%, "
                "похоже на обрезанную закачку" % (len(deals), have))
    return None


def validate_pending(data, disk_path: str) -> str | None:
    # Пустой список карточек — нормальное состояние очереди («всё решено»),
    # поэтому проверяем только форму, а не размер.
    if not isinstance(data, dict):
        return "это не объект JSON"
    if not isinstance(data.get("cards"), list):
        return "нет списка cards"
    return None


def validate_nonempty(data, disk_path: str) -> str | None:
    if not isinstance(data, (dict, list)) or not data:
        return "пустой или не объект/список JSON"
    return None


@dataclass(frozen=True)
class Target:
    path: str
    validate: Callable[[object, str], "str | None"]
    required: bool


TARGETS: tuple[Target, ...] = (
    Target(MAIN_FILE, validate_base, True),
    # Очередь предпросмотра: без неё ссылки #/preview/<id>, которые консоль
    # модерации шлёт в Telegram, показывали бы «карточка не найдена» — деплой,
    # который раньше их довозил, по коммитам данных больше не случается.
    Target("static/data/pending.json", validate_pending, False),
    # Выгрузки ЦБ — их обновляет ежедневный триггер, тем же коммитом в main.
    Target("static/data/bank_finance.json", validate_nonempty, False),
    Target("static/data/bank_full_balance.json", validate_nonempty, False),
)


# --------------------------------------------------------------------------
# Состояние: чем отчитываемся в /api/data/status
# --------------------------------------------------------------------------

_LOCK = threading.RLock()
_STATE: dict = {
    "started": False,
    "checks": 0,        # сколько раз спрашивали GitHub (включая ответы 304)
    "downloads": 0,     # сколько раз он отдал тело файла
    "writes": 0,        # сколько раз мы реально заменили файл на диске
    "rejects": 0,       # сколько раз скачанное не прошло проверку
    "last_try": None,   # когда последний раз пробовали (успешно или нет)
    "last_ok": None,    # когда последняя попытка прошла БЕЗ единой ошибки
    "last_change": None,
    "last_change_files": [],
    "last_error": None,
    "last_error_at": None,
    "fails_in_row": 0,
    "files": {},        # path -> {etag, modified, sha, changed_at}
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _file_state(path: str) -> dict:
    with _LOCK:
        return dict(_STATE["files"].get(path) or {})


def _remember(path: str, etag, modified, sha) -> None:
    with _LOCK:
        row = _STATE["files"].setdefault(path, {})
        row["etag"], row["modified"], row["sha"] = etag, modified, sha


def _bump(key: str, n: int = 1) -> None:
    with _LOCK:
        _STATE[key] = _STATE.get(key, 0) + n


def _note_error(text: str) -> None:
    with _LOCK:
        _STATE["last_error"], _STATE["last_error_at"] = text, _now()
    logger.warning("обновление данных: %s", text)


# --------------------------------------------------------------------------
# Скачивание. Вынесено отдельной функцией, чтобы тесты подменяли её целиком:
# сеть в тестах не нужна и не должна быть нужна.
# --------------------------------------------------------------------------

def _download(url: str, etag=None, modified=None) -> tuple[int, bytes, str | None, str | None]:
    """Возвращает (код, тело, ETag, Last-Modified). 304 — «не менялось»:
    условный запрос экономит 7 МБ трафика на каждой проверке, а проверок
    288 в сутки."""
    headers = {"User-Agent": "kompas-data-refresh"}
    if etag:
        headers["If-None-Match"] = etag
    if modified:
        headers["If-Modified-Since"] = modified
    # Таймаут на чтение большой: база — семь мегабайт, и на медленном канале
    # честнее подождать, чем счесть это отказом и качать заново следующим
    # заходом.
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0), follow_redirects=True) as client:
        r = client.get(url, headers=headers)
    if r.status_code == 304:
        return 304, b"", etag, modified
    return r.status_code, r.content, r.headers.get("ETag"), r.headers.get("Last-Modified")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _disk_sha(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return _sha(f.read())
    except OSError:
        return None


def _atomic_write(path: str, body: bytes) -> None:
    """Временный файл рядом + os.replace. Пиши мы «поверх» — посетитель,
    качающий базу в этот момент, получил бы половину файла; замена по
    os.replace атомарна на уровне файловой системы, а уже открытый
    дескриптор дочитывает старую версию до конца."""
    tmp = "%s.tmp-%d" % (path, os.getpid())
    try:
        with open(tmp, "wb") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# --------------------------------------------------------------------------
# Сброс кэшей. Главный подводный камень задачи: файл заменён, а процесс
# продолжает отвечать по старому — снаружи это выглядит как «данные не
# доехали», хотя они лежат на диске.
# --------------------------------------------------------------------------

def drop_in_process_caches() -> None:
    """Единственный кэш базы в памяти сайта — индекс ассистента
    (`assistant_retrieval._INDEX`). Остальные читатели (`deal_catalog`,
    `company_catalog`, `main._read_json`, `deal_multiples`) ходят на диск на
    каждый запрос — это записано в их комментариях как сознательный выбор,
    и менять его не нужно.

    ВНИМАНИЕ на будущее: заведёте ещё один кэш базы в памяти — сбрасывать
    его надо ЗДЕСЬ, иначе он тихо устареет до ближайшего деплоя.
    """
    try:
        # force=True не только сбрасывает, но и сразу греет индекс: он
        # строится около секунды, и платить этой секундой должен фоновый
        # поток, а не первый посетитель с вопросом.
        assistant_retrieval.get_index(force=True)
    except Exception as exc:  # noqa: BLE001 — сайт важнее ассистента
        logger.error("индекс ассистента не пересобрался: %s", exc)


def _rescan_subscriptions() -> None:
    """Раньше подписки сверялись при старте процесса после деплоя — теперь
    новые карточки приезжают БЕЗ старта, и без этого вызова рассылка молча
    перестала бы работать вовсе (урок «функция, которую никто не вызывает,
    выглядит на экране работающей»). Сверка идемпотентна: она помнит состав
    базы в таблице `deals_seen` и второй раз о том же не пишет."""
    try:
        subscription_feed.scan_on_startup()
    except Exception as exc:  # noqa: BLE001
        logger.error("подписки не сверены после обновления данных: %s", exc)


def _after_change(changed: list[str]) -> None:
    if MAIN_FILE not in changed:
        return
    drop_in_process_caches()
    _rescan_subscriptions()


# --------------------------------------------------------------------------
# Сама работа
# --------------------------------------------------------------------------

def _refresh_target(target: Target) -> bool:
    """True — файл на диске заменён. Исключение — попытка не удалась;
    файл при этом НЕ тронут."""
    path = full_path(target.path)
    st = _file_state(target.path)
    status, body, etag, modified = _download(raw_url(target.path), st.get("etag"), st.get("modified"))
    _bump("checks")
    if status == 304:
        return False
    if status == 404 and not target.required:
        # Файла нет в ветке — это не сбой: выгрузки ЦБ появляются не сразу,
        # а очередь предпросмотра бывает не закоммичена вовсе.
        return False
    if status != 200:
        raise RefreshError("ответ GitHub %s" % status)
    _bump("downloads")

    digest = _sha(body)
    if digest == st.get("sha") or digest == _disk_sha(path):
        # Сервер не прислал 304 (бывает — заголовки теряются на прокси), но
        # содержимое то же. Не пишем и не сбрасываем кэши: лишняя пересборка
        # индекса стоит секунды на ровном месте.
        _remember(target.path, etag, modified, digest)
        return False

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        _bump("rejects")
        raise RefreshError("скачанное не разбирается как JSON: %s" % exc) from exc
    why = target.validate(data, path)
    if why:
        _bump("rejects")
        raise RefreshError("проверка не пройдена (%s)" % why)

    _atomic_write(path, body)
    _bump("writes")
    _remember(target.path, etag, modified, digest)
    with _LOCK:
        _STATE["files"].setdefault(target.path, {})["changed_at"] = _now()
    logger.info("обновлён %s (%d КБ)", target.path, len(body) // 1024)
    return True


def refresh_once() -> dict:
    """Одна попытка по всем файлам. Наружу не бросает: сеть, недоступный
    GitHub и порченый файл — обычные события, а не авария."""
    changed: list[str] = []
    errors: list[str] = []
    for target in TARGETS:
        try:
            if _refresh_target(target):
                changed.append(target.path)
        except Exception as exc:  # noqa: BLE001 — сеть/JSON/диск, всё сюда
            errors.append("%s: %s" % (target.path, exc))
            _note_error("%s: %s" % (target.path, exc))
    with _LOCK:
        _STATE["last_try"] = _now()
        if errors:
            _STATE["fails_in_row"] += 1
        else:
            _STATE["last_ok"] = _STATE["last_try"]
            _STATE["fails_in_row"] = 0
        if changed:
            _STATE["last_change"] = _STATE["last_try"]
            _STATE["last_change_files"] = list(changed)
    if changed:
        _after_change(changed)
    return {"changed": changed, "errors": errors}


def _loop() -> None:
    # Небольшая пауза перед первым заходом: старт и так занят прогревом
    # индекса, созданием таблиц и сверкой подписок — семимегабайтная закачка
    # в этот же момент только замедлит первые ответы сайта. Это же и есть
    # окно проверки состояния на Timeweb: у владельца там стоит путь «/»,
    # то есть целый index.html (~1,2 с) вместо «/health» (0,5 с), и первый
    # ответ не должен конкурировать с нашей закачкой за процесс.
    time.sleep(15)
    while True:
        try:
            refresh_once()
        except Exception as exc:  # noqa: BLE001 — поток обязан пережить всё
            logger.error("обновление данных сорвалось целиком: %s", exc)
        time.sleep(interval_seconds())


def start() -> bool:
    """Запустить фоновый поток. False — не запускали, и это нормальное
    состояние, а не ошибка."""
    # Под тестами в сеть не ходим никогда — тот же гвард, что у докачки ФНС.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    if not enabled():
        logger.info("подтягивание данных выключено (DATA_REFRESH_ENABLED=0) — "
                    "сайт живёт на файлах, приехавших деплоем")
        return False
    with _LOCK:
        if _STATE["started"]:
            return False
        _STATE["started"] = True
    threading.Thread(target=_loop, daemon=True, name="data-refresh").start()
    logger.info("подтягиваю данные из ветки %s каждые %.0f мин",
                branch(), interval_seconds() / 60)
    return True


# --------------------------------------------------------------------------
# Наблюдение: как часто сайт перезапускается и не разъехались ли код и данные.
# Журнала сборок за ту ночь у владельца уже нет, причину девятиминутного 502
# установить было нечем — значит, следующий раз должен быть виден по одному
# запросу, без чужих логов.
# --------------------------------------------------------------------------

def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).replace(microsecond=0).isoformat()


def _human_age(seconds: float) -> str:
    """По-русски, без «uptime» и прочего диалекта: это читает владелец."""
    seconds = int(max(0, seconds))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return "%d дн %d ч" % (days, hours)
    if hours:
        return "%d ч %d мин" % (hours, minutes)
    return "%d мин" % minutes


def _read_text(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _git_head(base_dir: str) -> tuple[str | None, str | None]:
    """(короткий хеш, имя ветки) из `.git` рядом с кодом — БЕЗ вызова git.

    Timeweb выкладывает приложение из репозитория, и `.git` при этом обычно
    оказывается на диске; если нет — честно возвращаем None, а не выдумываем
    версию. Ветка полезна как перекрёстная проверка: код обязан быть собран
    из `release`, данные — приезжать из `main`, и если тут вдруг `main`,
    значит переключение в панели не сделано.
    """
    gitdir = os.path.join(base_dir, ".git")
    if os.path.isfile(gitdir):  # рабочее дерево git worktree — указатель, не папка
        line = _read_text(gitdir) or ""
        if not line.startswith("gitdir:"):
            return None, None
        pointed = line.split(":", 1)[1].strip()
        gitdir = pointed if os.path.isabs(pointed) else os.path.normpath(os.path.join(base_dir, pointed))
    if not os.path.isdir(gitdir):
        return None, None
    head = _read_text(os.path.join(gitdir, "HEAD"))
    if not head:
        return None, None
    if not head.startswith("ref:"):
        # Отсоединённая голова — деплой чаще всего выглядит именно так.
        return (head[:12], None) if len(head) >= 7 else (None, None)
    ref = head.split(":", 1)[1].strip()
    branch = ref.rsplit("/", 1)[-1]
    common = gitdir
    pointer = _read_text(os.path.join(gitdir, "commondir"))
    if pointer:
        common = os.path.normpath(os.path.join(gitdir, pointer))
    for candidate in (os.path.join(gitdir, ref), os.path.join(common, ref)):
        sha = _read_text(candidate)
        if sha:
            return sha[:12], branch
    packed = _read_text(os.path.join(common, "packed-refs")) or ""
    for row in packed.splitlines():
        parts = row.split()
        if len(parts) == 2 and parts[1] == ref:
            return parts[0][:12], branch
    return None, branch


def code_version() -> dict:
    """Версия КОДА, из которого поднят процесс, — отдельно от версии данных.

    Хеш ищем там, где его можно узнать честно: сначала переменная окружения
    (её владелец или хостинг могут задать явно), потом `.git` на диске. Не
    нашли — `null`, а не догадка: неверная версия хуже отсутствующей.
    """
    for name in ("CODE_VERSION", "GIT_COMMIT", "COMMIT_SHA", "SOURCE_COMMIT", "GIT_SHA"):
        value = (os.environ.get(name) or "").strip()
        if value:
            return {"commit": value[:12], "source": "переменная окружения %s" % name, "branch": None}
    commit, branch = _git_head(BASE_DIR)
    return {"commit": commit, "branch": branch,
            "source": ".git рядом с кодом" if commit else
                      "неизвестна: ни переменной окружения, ни .git на диске"}


def _code_mtime() -> str | None:
    """Когда файлы кода легли на диск. Работает всегда, даже без `.git`, и
    отвечает на вопрос «а деплой-то вообще был?» — в отличие от хеша."""
    times = []
    for name in ("main.py", os.path.join("static", "index.html")):
        try:
            times.append(os.path.getmtime(os.path.join(BASE_DIR, name)))
        except OSError:
            pass
    return _iso(max(times)) if times else None


def status() -> dict:
    """Всё, что нужно, чтобы за минуту понять: доступен ли GitHub с боевого
    хоста, что и когда приехало, на каких данных сайт сейчас живёт, как давно
    он не перезапускался и не разъехались ли код и данные."""
    with _LOCK:
        state = {k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v)
                 for k, v in _STATE.items()}
    files = []
    for target in TARGETS:
        path = full_path(target.path)
        row = {"path": target.path, "required": target.required,
               "url": raw_url(target.path), "on_disk": os.path.exists(path)}
        try:
            row["bytes"] = os.path.getsize(path)
            row["mtime"] = datetime.fromtimestamp(
                os.path.getmtime(path), timezone.utc).replace(microsecond=0).isoformat()
        except OSError:
            row["bytes"], row["mtime"] = None, None
        row["changed_at"] = (state["files"].get(target.path) or {}).get("changed_at")
        files.append(row)
    return {
        "enabled": enabled(),
        "running": bool(state["started"]),
        "repo": DATA_REPO,
        "branch": branch(),
        "interval_minutes": round(interval_seconds() / 60, 2),
        "now": _now(),
        "last_try": state["last_try"],
        "last_ok": state["last_ok"],
        "last_change": state["last_change"],
        "last_change_files": state["last_change_files"],
        "last_error": state["last_error"],
        "last_error_at": state["last_error_at"],
        "fails_in_row": state["fails_in_row"],
        "checks": state["checks"], "downloads": state["downloads"],
        "writes": state["writes"], "rejects": state["rejects"],
        # Сколько сделок в файле, на котором сайт живёт ПРЯМО СЕЙЧАС, — это и
        # есть ответ на вопрос «данные доехали?». Считается чтением файла:
        # эндпоинт зовут руками, а не в цикле.
        "deals_on_disk": _count_deals(full_path(MAIN_FILE)),
        "files": files,
        # Перезапуск процесса на Timeweb бывает ровно по одной причине —
        # пересборка. Значит, «сколько живёт процесс» и есть мера того, как
        # часто сайт пересобирается: до 3 сентября 2026 это были часы и
        # минуты (рутины коммитили данные), после перехода на ветку release
        # должны стать дни. Если тут снова минуты — код собирается не из той
        # ветки, и разъезд данных и кода не сработал.
        "process": {
            "started_at": _iso(_STARTED_AT),
            "uptime_seconds": int(time.time() - _STARTED_AT),
            "uptime": _human_age(time.time() - _STARTED_AT),
            "note": "процесс перезапускается только пересборкой: короткое "
                    "время жизни = сайт всё ещё собирается на каждый пуш",
        },
        # Версия кода и версия данных — РАЗНЫЕ величины с того же дня, и
        # смотреть на них надо порознь: на диске законно лежит база новее
        # кода. Хеш — только если его реально можно узнать, иначе null.
        "code": {**code_version(), "files_mtime": _code_mtime()},
        "data": {
            "branch": branch(),
            "deals": _count_deals(full_path(MAIN_FILE)),
            "base_mtime": next((f["mtime"] for f in files if f["path"] == MAIN_FILE), None),
            # Когда базу последний раз подтянули ЭТИМ процессом. None и при
            # этом свежий base_mtime означает «файл приехал деплоем, своих
            # обновлений ещё не было» — это разные вещи, и путать их нельзя.
            "pulled_at": (state["files"].get(MAIN_FILE) or {}).get("changed_at"),
        },
    }
