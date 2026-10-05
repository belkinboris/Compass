# -*- coding: utf-8 -*-
"""Посещаемость сайта из Яндекс Метрики — для ежедневной сводки в консоль.

ЗАЧЕМ. Владелец 5 октября 2026: сводку притока — «1 раз в день в 18:00 и
отправляй статистику из Яндекс Метрики». Счётчик сайта уже стоит на
странице (`mc.yandex.ru/watch/112192428`), но читать его статистику можно
только с ключом доступа (OAuth-токен с правом «Получение статистики»):
переменная `METRIKA_TOKEN` на хостинге. Без ключа функция честно отвечает
`None`, и сводка говорит, что посещаемость появится после подключения, —
не выдумывает цифр.

Запросы — к API отчётов (`/stat/v1/data`): итог дня (посетители, визиты,
просмотры, среднее время, доля новых), источники визитов и вчерашний день
для сравнения. Три запроса раз в сутки — далеко от любых лимитов.
"""
import os

import httpx

API = "https://api-metrika.yandex.net/stat/v1/data"
COUNTER = os.environ.get("METRIKA_COUNTER", "112192428").strip()


def _get(client, token, params):
    r = client.get(API, params={**params, "ids": COUNTER, "lang": "ru", "accuracy": "full"},
                   headers={"Authorization": "OAuth " + token})
    r.raise_for_status()
    return r.json()


def day_stats(day="today", token=None, client=None):
    """Цифры за день (`today`/`yesterday`/`YYYY-MM-DD`) или None без ключа.
    Ошибка сети или ключа — исключение: вызывающий решает, что сказать."""
    token = (token if token is not None else os.environ.get("METRIKA_TOKEN", "")).strip()
    if not token:
        return None
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        main = _get(client, token, {"metrics": "ym:s:users,ym:s:visits,ym:s:pageviews,"
                                               "ym:s:avgVisitDurationSeconds,ym:s:percentNewVisitors",
                                    "date1": day, "date2": day})
        src = _get(client, token, {"metrics": "ym:s:visits", "dimensions": "ym:s:lastTrafficSource",
                                   "sort": "-ym:s:visits", "limit": 4, "date1": day, "date2": day})
        prev = _get(client, token, {"metrics": "ym:s:users,ym:s:visits",
                                    "date1": "yesterday", "date2": "yesterday"})
    finally:
        if own:
            client.close()
    t = (main.get("totals") or []) + [0] * 5
    p = (prev.get("totals") or []) + [0] * 2
    total_src = (src.get("totals") or [0])[0] or 0
    sources = [(row["dimensions"][0]["name"], row["metrics"][0]) for row in src.get("data") or []]
    return {"users": int(t[0] or 0), "visits": int(t[1] or 0), "pageviews": int(t[2] or 0),
            "avg_seconds": int(t[3] or 0), "new_pct": float(t[4] or 0),
            "sources": [(name, round(v / total_src * 100)) for name, v in sources if total_src],
            "yesterday": {"users": int(p[0] or 0), "visits": int(p[1] or 0)}}


def _num(n):
    return f"{int(n):,}".replace(",", " ")


def _duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m} мин {s} с" if m else f"{s} с"


def render(stats):
    """Строки блока «Сайт сегодня» — словами, без кода метрик."""
    if not stats:
        return ["📈 Посещаемость сайта из Яндекс Метрики появится здесь, как только подключим доступ к Метрике."]
    lines = ["📈 <b>Сайт сегодня</b> (Яндекс Метрика)",
             f"Посетителей — {_num(stats['users'])}, визитов — {_num(stats['visits'])}, "
             f"просмотров страниц — {_num(stats['pageviews'])}."]
    if stats["visits"]:
        lines.append(f"Новых посетителей — {round(stats['new_pct'])}%, "
                     f"в среднем на сайте {_duration(stats['avg_seconds'])}.")
    if stats["sources"]:
        lines.append("Откуда пришли: " + ", ".join(
            f"{name[:1].lower() + name[1:]} — {pct}%" for name, pct in stats["sources"] if pct) + ".")
    y = stats["yesterday"]
    lines.append(f"Вчера: посетителей — {_num(y['users'])}, визитов — {_num(y['visits'])}.")
    return lines
