# -*- coding: utf-8 -*-
"""Совпадает ли код на боевом сайте с тем, что в этом чекауте.

ЗАЧЕМ. 19 сентября 2026 выкладка встала: за день в git уехало восемь
коммитов, а сайт продолжал отдавать сборку 18-го. Заметили это случайно —
рутина заметок не смогла забрать заявки, потому что её эндпоинта на сайте
ещё не было. Всё остальное за тот день (в том числе гейт, который перестаёт
отвечать на «найди компромат на X») молча лежало в репозитории.

Чтобы понять, какой код на сайте, пришлось сравнивать размер index.html,
искать в нём признаки отдельных коммитов и в конце спрашивать сам ассистент.
Это расследование на полчаса там, где должен быть один запрос.

Теперь `/health` отдаёт отпечаток выложенных файлов, и сравнение — две
строки. Скрипт печатает один из трёх исходов:
  * сайт и чекаут совпадают;
  * сайт отстал — названы файлы, которые разошлись;
  * сайт не ответил или отвечает старым кодом без отпечатка (тогда он
    точно отстал: поле `build` появилось в тот же день).

Запуск: python3 pipeline/check_deploy.py
Код возврата 1 — сайт отстал или недоступен; так рутина может остановиться
и сказать человеку, вместо того чтобы делать вид, что всё применилось.
"""
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("main.py", "static/index.html")
SITE = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")


def local_fingerprint() -> dict:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:8]
            for name in FILES}


def site_fingerprint():
    import httpx
    r = httpx.get(SITE + "/health", timeout=20)
    r.raise_for_status()
    if "json" not in (r.headers.get("content-type") or "").lower():
        return None
    return (r.json() or {}).get("build")


def main() -> int:
    mine = local_fingerprint()
    try:
        theirs = site_fingerprint()
    except Exception as e:                                  # noqa: BLE001
        print("Сайт не ответил (%s): %s" % (SITE, e))
        return 1
    if not theirs:
        print("Сайт отвечает, но отпечатка сборки не отдаёт — значит, на нём код\n"
              "старше 19 сентября 2026: поле появилось в тот же день. Сайт отстал.")
        return 1
    diff = [name for name in FILES if mine.get(name) != theirs.get(name)]
    if not diff:
        print("Сайт и этот чекаут совпадают: %s" % ", ".join(
            "%s %s" % (n, mine[n]) for n in FILES))
        return 0
    print("Сайт отстал от репозитория. Разошлись: %s" % ", ".join(diff))
    for name in FILES:
        print("   %-18s на сайте %s, здесь %s" % (name, theirs.get(name), mine.get(name)))
    print("\nЭто не ошибка рутины: код в git есть, на сайт он не выложен.\n"
          "Проверить сборку на хостинге.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
