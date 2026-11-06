# -*- coding: utf-8 -*-
"""Ежедневная проверка модели ассистента на боевом сервере (6 ноября 2026).

ЗАЧЕМ. 3 ноября основная модель в папке Яндекса начала отвечать 403, а YandexGPT на
темах санкций отдает заглушку — «Разбор сделки», «Контекст» и ассистент молча писали
«недоступен», и заметил это владелец, а не мы. Проверка задает один вопрос о сделке
«на остром» материале основной модели сервера (через стенд `assistant_bench.py`,
ключи только на сервере) и смотрит отметки /health.

    python3 pipeline/llm_check.py        # «ОК: …» (код 0) или «СБОЙ: …» (код 1)

Сбой — строка в отчет рутины и PushNotification один раз на сбой (routines/quality.md).
"""
import json
import os
import subprocess
import sys

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get("KOMPAS_SITE", "https://projectcompass.ru")
QUESTION = "Почему иностранные компании продают бизнес в России с дисконтом?"


def main():
    try:
        health = httpx.get(SITE + "/health", timeout=30).json()
    except Exception as exc:  # noqa: BLE001
        print("СБОЙ: сайт не ответил на /health (%s)" % exc)
        return 1
    model = health.get("model")
    row = None
    for _ in range(2):   # обрыв сети по дороге к сайту — не сбой модели: одна повторная попытка
        out = subprocess.run([sys.executable, os.path.join(ROOT, "pipeline", "assistant_bench.py"), "--models", "current",
                              "--repeats", "1", "--json", "--question", QUESTION],
                             capture_output=True, text=True, timeout=300).stdout
        try:
            row = json.loads(out)[0]
        except Exception:  # noqa: BLE001
            row = None
        if row and (row.get("ok") or "сеть:" not in str(row.get("error"))):
            break
    if not row:
        print("СБОЙ: стенд моделей не вернул ответ (нет токена MODERATION_TOKEN?)")
        return 1
    if row.get("ok"):
        print("ОК: модель %s ответила за %s с" % (model, row.get("seconds")))
        return 0
    seen = (health.get("llm") or {}).get(model) or {}
    print("СБОЙ: модель %s не ответила (%s); последний успех — %s" % (model, str(row.get("error"))[:120], seen.get("ok") or "нет данных"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
