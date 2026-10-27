"""Защита базы от легкого скачивания целиком (16 октября 2026).

Владелец: «так как мы запускаемся — подумай над защитой, чтобы нас спарсить
не могли легко и вытащить всю инфу». Записка с разбором дыр, ценой и
планом — docs/scraping_protection.md. Здесь только первый шаг, который не
меняет того, что видит обычный посетитель:

1. База отдается не публичным файлом `/static/data/deals_promoted.json`, а
   эндпойнтом `/api/data/deals_promoted.json`, который требует
   короткоживущий подписанный токен. Токен ставится страницей: сервер кладет
   его в cookie, отдавая index.html (`issue_cookie`), а если он истек —
   страница берет новый в `/api/data/session` и повторяет запрос.
2. Referer / Origin / Sec-Fetch-Site: ЧУЖОЙ сайт получает отказ. Отсутствие
   заголовков отказом не считается (их режут расширения приватности) —
   это дополнительный барьер, а главный — токен.
3. Очевидные роботы (пустой User-Agent, curl, python-requests, wget, scrapy
   и т. п.) к базе не допускаются. Страница сайта для них открыта как была:
   поисковики индексируют HTML, а не базу.
4. Частота запросов с одного адреса — в памяти процесса, по группам путей
   (база, ассистент, PDF, платная ФНС, вход). Внешних сервисов нет.
5. Служебный ключ: рутины (send_telegram.py, acceptance_check.py) ходят
   к базе с `MODERATION_TOKEN` — тем же, что у моста решений.

Выключатель — `SCRAPE_GUARD=0` в окружении: тогда старый путь к файлу снова
открыт, эндпойнт отдает базу без проверок, лимиты не считаются.

Чего это НЕ дает (честно, см. записку): человек с браузером или скрипт,
который сначала открывает главную и держит cookie, базу получит — сайт
показывает ее целиком в браузере. Шаг закрывает «одну строку curl» и
прямую ссылку на файл, делает сбор заметным и дает юридически важное:
доступ к базе контролируется, обход — осознанное действие.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import re
import secrets
import threading
import time
from collections import deque
from urllib.parse import urlsplit

COOKIE_NAME = "kd_t"
DATA_PATH = "/api/data/deals_promoted.json"
SESSION_PATH = "/api/data/session"
STATIC_DATA_PATH = "/static/data/deals_promoted.json"


def enabled() -> bool:
    """По умолчанию ВКЛЮЧЕНО. Читается на каждый вызов: тесты и владелец
    меняют переменную без перезапуска интерпретатора."""
    return (os.environ.get("SCRAPE_GUARD", "1") or "").strip().lower() \
        not in ("0", "false", "no", "off")


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


def ttl_seconds() -> float:
    return max(300.0, _float_env("DATA_TOKEN_TTL_HOURS", 6.0) * 3600.0)


def bind_ip() -> bool:
    """Привязка токена к адресу — по желанию и по умолчанию ВЫКЛЮЧЕНА:
    у мобильных посетителей адрес меняется посреди сессии, и токен,
    привязанный к нему, ломал бы загрузку базы без всякой причины."""
    return (os.environ.get("DATA_TOKEN_BIND_IP", "0") or "").strip() == "1"


# --------------------------------------------------------------------------
# Секрет подписи. Порядок: DATA_TOKEN_SECRET → производный от
# MODERATION_TOKEN / TELEGRAM_WEBHOOK_SECRET (уже есть на сервере, переживает
# перезапуск) → случайный на процесс (после перезапуска старые токены
# недействительны — страница сама возьмет новый).
# --------------------------------------------------------------------------
_PROCESS_SECRET = secrets.token_bytes(32)


def _secret() -> bytes:
    own = (os.environ.get("DATA_TOKEN_SECRET") or "").strip()
    if own:
        return own.encode()
    other = (os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    if other:
        return hmac.new(other.encode(), b"kompas-data-token", hashlib.sha256).digest()
    return _PROCESS_SECRET


def _ua_hash(ua: str) -> str:
    return hashlib.sha256((ua or "").encode("utf-8", "replace")).hexdigest()[:12]


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(ua: str, ip: str | None = None, now: float | None = None) -> str:
    ts = int(now if now is not None else time.time())
    payload = "%d.%s" % (ts, _ua_hash(ua))
    signed = payload + ("." + (ip or "") if bind_ip() else "")
    return payload + "." + _sign(signed)


def check_token(token: str, ua: str, ip: str | None = None, now: float | None = None) -> bool:
    parts = (token or "").split(".")
    if len(parts) != 3:
        return False
    ts_s, uah, sig = parts
    try:
        ts = int(ts_s)
    except ValueError:
        return False
    now = now if now is not None else time.time()
    if ts > now + 60 or now - ts > ttl_seconds():
        return False
    if not hmac.compare_digest(uah, _ua_hash(ua)):
        return False
    signed = "%s.%s" % (ts_s, uah) + ("." + (ip or "") if bind_ip() else "")
    return hmac.compare_digest(sig, _sign(signed))


# --------------------------------------------------------------------------
# Адрес посетителя. Сайт стоит за фронтом хостинга: request.client — это
# прокси, а настоящий адрес — в X-Forwarded-For. Берем САМЫЙ ПРАВЫЙ
# публичный адрес: его дописал наш фронт, а левые значения посетитель может
# подставить сам, чтобы обойти лимит. Не нашли публичного — None, и лимит не
# считается: лучше не ограничить никого, чем ограничить всех разом по адресу
# прокси (весь сайт за одним IP).
# --------------------------------------------------------------------------

def _public(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    return not (a.is_private or a.is_loopback or a.is_link_local or a.is_reserved
                or a.is_multicast or a.is_unspecified)


def client_ip(headers, client_host: str | None) -> str | None:
    xff = headers.get("x-forwarded-for") or ""
    for part in reversed([p.strip() for p in xff.split(",") if p.strip()]):
        if _public(part):
            return part
    real = (headers.get("x-real-ip") or "").strip()
    if real and _public(real):
        return real
    if client_host and _public(client_host):
        return client_host
    return None


# --------------------------------------------------------------------------
# Роботы. Только для базы и выдачи токена — НЕ для HTML-страницы.
# HeadlessChrome здесь сознательно нет: им ходят наши же тесты, а настоящего
# сборщика с браузером по строке User-Agent все равно не отличить.
# --------------------------------------------------------------------------
_BOT_UA = re.compile(
    r"curl|wget|python|httpx|aiohttp|requests|urllib|scrapy|go-http-client|java/|okhttp|"
    r"libwww|perl|php|node-fetch|axios|undici|got \(|httpclient|postman|insomnia|"
    r"powershell|ruby|reqwest|colly|httrack|nutch|spider|crawler|scraper|"
    r"bot/|semrush|ahrefs|mj12|dotbot|petalbot|bytespider|gptbot|ccbot|claudebot|"
    r"anthropic|perplexity|dataforseo|headlesschrome-scraper",
    re.I)


def is_robot(ua: str) -> bool:
    ua = (ua or "").strip()
    return not ua or bool(_BOT_UA.search(ua))


def foreign_origin(headers, host: str) -> bool:
    """True — запрос пришел со страницы ЧУЖОГО сайта. Пустые заголовки —
    не повод для отказа."""
    host = (host or "").split(":")[0].lower()
    site = (headers.get("sec-fetch-site") or "").lower()
    if site in ("cross-site", "same-site"):
        return True
    for name in ("origin", "referer"):
        val = headers.get(name)
        if not val or val == "null":
            continue
        h = (urlsplit(val).hostname or "").lower()
        if h and h != host:
            return True
    return False


# --------------------------------------------------------------------------
# Частота запросов. Скользящее окно на (группа, адрес). Числа с запасом на
# офис за одним адресом: аудитория — юристы и банкиры, у которых весь этаж
# выходит в сеть через один NAT.
# --------------------------------------------------------------------------
WINDOW = 600.0
_GROUPS = (
    # (имя, переменная окружения, умолчание за 10 минут, проверка пути)
    ("data", "RATE_DATA_PER_10MIN", 60,
     lambda p, m: p in (DATA_PATH, SESSION_PATH, STATIC_DATA_PATH)),
    ("assistant", "RATE_ASSISTANT_PER_10MIN", 40,
     lambda p, m: m == "POST" and p in ("/api/ask", "/api/assistant/lookup")),
    ("pdf", "RATE_PDF_PER_10MIN", 30,
     lambda p, m: m == "POST" and (p == "/api/companies/export"
                                   or (p.startswith("/api/deals/") and p.endswith("/export")))),
    ("fns_paid", "RATE_FNS_PAID_PER_10MIN", 20,
     lambda p, m: p.startswith("/api/companies/") and ("/fns/extract" in p or "/fns/bo/" in p)),
    ("fns", "RATE_FNS_PER_10MIN", 300,
     lambda p, m: (p.startswith("/api/companies/") and p.endswith("/fns"))
     or p in ("/api/finance/screening", "/api/analytics/multiples")),
    ("auth", "RATE_AUTH_PER_10MIN", 30,
     lambda p, m: m == "POST" and p in ("/api/auth/login", "/api/auth/register",
                                         "/api/auth/password")),
)

_lock = threading.Lock()
_hits: dict[tuple[str, str], deque] = {}
_stats: dict[str, int] = {}
_last_sweep = [0.0]


def bump(key: str) -> None:
    with _lock:
        _stats[key] = _stats.get(key, 0) + 1


def stats() -> dict:
    with _lock:
        return {"enabled": enabled(), "counters": dict(_stats), "tracked_addresses": len(_hits)}


def reset() -> None:
    """Для тестов."""
    with _lock:
        _hits.clear()
        _stats.clear()


def group_of(path: str, method: str) -> tuple[str, int] | None:
    for name, env, default, match in _GROUPS:
        if match(path, method):
            return name, int(_float_env(env, default))
    return None


def too_many(group: str, limit: int, ip: str, now: float | None = None) -> float:
    """0 — можно; иначе сколько секунд ждать."""
    now = now if now is not None else time.monotonic()
    with _lock:
        if now - _last_sweep[0] > WINDOW:
            for k in [k for k, q in _hits.items() if not q or now - q[-1] > WINDOW]:
                del _hits[k]
            _last_sweep[0] = now
        q = _hits.setdefault((group, ip), deque())
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= limit:
            return max(1.0, WINDOW - (now - q[0]))
        q.append(now)
        return 0.0


def service_key_ok(headers, query_token: str = "") -> bool:
    expected = (os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    got = (headers.get("x-data-key") or query_token or "").strip()
    return bool(expected) and bool(got) and hmac.compare_digest(got, expected)


def cookie_secure(request) -> bool:
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "").split(",")[0].strip()
    return proto == "https"


def issue_cookie(response, request) -> None:
    ua = request.headers.get("user-agent", "")
    ip = client_ip(request.headers, request.client.host if request.client else None)
    response.set_cookie(COOKIE_NAME, make_token(ua, ip), max_age=int(ttl_seconds()),
                        httponly=True, samesite="lax", secure=cookie_secure(request), path="/")
