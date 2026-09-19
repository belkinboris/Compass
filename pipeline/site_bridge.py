# -*- coding: utf-8 -*-
"""Мост «рутина → сайт»: запрос к API сайта, который честно говорит, что не так.

ЗАЧЕМ ОТДЕЛЬНЫЙ МОДУЛЬ. Рутины живут в одноразовых контейнерах, до базы
сайта им не достать (приватная сеть), и единственная дорога — HTTP-вызовы
к `/api/...?token=…`. Все такие вызовы были написаны одинаково:

    r = httpx.get(SITE + path, params={'token': token}, timeout=20)
    r.raise_for_status()
    return r.json()

19 сентября 2026 этот код упал трассировкой `JSONDecodeError` на первом же
реальном прогоне рутины «заметки от пользователей»: сайт ответил кодом 200
и HTML-страницей. Причина не в сети и не в токене — эндпоинта на боевом
сайте ещё НЕ БЫЛО (новый код не выкачен), а неизвестные адреса ловит
catch-all, который отдаёт страницу приложения с кодом 200. `raise_for_status`
такой ответ пропускает, `r.json()` на нём взрывается, и рутина сообщает
человеку трассировку вместо диагноза. Тот же catch-all однажды уже съел
`/favicon.ico` (см. KNOWN_ISSUES.md) — то есть класс дефекта известен, а
чинился до сих пор по одному месту.

ЧТО ДЕЛАЕТ ЭТОТ МОДУЛЬ. Один вызов вместо трёх строк, и у каждого отказа
есть человеческая причина: нет токена, сайт не ответил, сайт ответил
страницей вместо данных. Рутина ловит `BridgeUnavailable`, печатает `.reason`
и заканчивает прогон честным отчётом, а не падением.
"""
import os

SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')


class BridgeUnavailable(Exception):
    """Сайт не отдал данные. `reason` — фраза для человека, без диалекта."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def token() -> str:
    return (os.environ.get('MODERATION_TOKEN') or
            os.environ.get('TELEGRAM_WEBHOOK_SECRET') or '').strip()


def _as_json(response, path: str):
    """Ответ сайта как JSON — или понятный отказ.

    Проверяем СОДЕРЖИМОЕ, а не только код: catch-all отдаёт страницу
    приложения с кодом 200, и по коду «эндпоинта нет» от «данных нет» не
    отличить."""
    kind = (response.headers.get('content-type') or '').lower()
    if 'json' not in kind:
        raise BridgeUnavailable(
            'сайт ответил обычной страницей вместо данных по адресу %s — '
            'скорее всего, новый код ещё не выложен на боевой сайт' % path)
    try:
        return response.json()
    except ValueError:
        raise BridgeUnavailable('сайт ответил по адресу %s чем-то, что не разбирается '
                                'как данные' % path) from None


def get_json(path: str, params: dict | None = None, timeout: int = 20):
    import httpx
    url = SITE + path
    try:
        r = httpx.get(url, params=params or {}, timeout=timeout)
    except Exception as e:                                  # noqa: BLE001
        raise BridgeUnavailable('не удалось связаться с сайтом (%s): %s' % (url, e)) from None
    if r.status_code == 404:
        raise BridgeUnavailable('сайт не знает адреса %s (или не принял токен)' % path)
    if r.status_code >= 400:
        raise BridgeUnavailable('сайт ответил ошибкой %d по адресу %s' % (r.status_code, path))
    return _as_json(r, path)


def post_json(path: str, payload: dict, timeout: int = 20):
    import httpx
    url = SITE + path
    try:
        r = httpx.post(url, json=payload, timeout=timeout)
    except Exception as e:                                  # noqa: BLE001
        raise BridgeUnavailable('не удалось связаться с сайтом (%s): %s' % (url, e)) from None
    if r.status_code == 404:
        raise BridgeUnavailable('сайт не знает адреса %s (или не принял токен)' % path)
    if r.status_code >= 400:
        raise BridgeUnavailable('сайт ответил ошибкой %d по адресу %s' % (r.status_code, path))
    return _as_json(r, path)
