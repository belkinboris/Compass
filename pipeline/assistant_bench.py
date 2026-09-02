#!/usr/bin/env python3
"""Стенд сравнения моделей ассистента — через боевой сервер, где есть ключи.

ЗАЧЕМ. Партнёр 2 сентября 2026: «40 секунд ту мач» — ответ модели на странице
«Яндекса» шёл 40 секунд, а в режиме «по всему интернету» модель не успела
вовсе. Владелец: «можем потенциально потестировать модели». Ключей Yandex AI
Studio в среде разработки нет, есть только на Timeweb — поэтому модель
вызывается не отсюда, а сервером: `POST /api/assistant/bench` (main.py) идёт
ТЕМ ЖЕ путём, что `/api/ask` (та же сводка по базе, тот же промпт, тот же
дедлайн), и возвращает время, успех, длину и расход токенов по каждой модели.
Этот скрипт только собирает таблицу. Ничего не пишет: ни в базу, ни в git,
ни в диалоги пользователей.

КАК ЗАПУСКАТЬ (токен — тот же, что у /api/moderation/decisions):

    MODERATION_TOKEN=... python3 pipeline/assistant_bench.py
    python3 pipeline/assistant_bench.py --mode web --repeats 2
    python3 pipeline/assistant_bench.py --models current yandexgpt/latest --effort low
    python3 pipeline/assistant_bench.py --question "Почему яндекс так много покупает?" \
        --context company yandex

`current` — модель, которая стоит на сервере сейчас (YANDEX_MODEL). Имена
моделей передаются серверу как есть: неверное имя даст честную строку ошибки
в таблице (HTTP 4xx от Responses API), а не тихий ноль. Список по умолчанию —
из документации Yandex AI Studio и её SDK; какие из них реально включены в
папке владельца, покажет только сам прогон. `--effort` передаёт
`reasoning: {"effort": ...}` (none | minimal | low | medium | high | xhigh),
пустая строка `--effort ""` — не передавать параметр вовсе.

Между запросами пауза (`--pause`, по умолчанию 2 с): 30 августа после 10+
вопросов подряд без пауз сервер начал отвечать пустотой за 0,2 с — похоже на
защиту от всплеска, и стенд не должен её будить.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

DEFAULT_SITE = "https://projectcompass.ru"
DEFAULT_MODELS = [
    "current",
    "yandexgpt/latest",
    "yandexgpt-lite/latest",
    "qwen3-235b-a22b-fp8/latest",
    "gpt-oss-120b/latest",
    "deepseek-v4-flash/latest",
]
# Те же вопросы, что в test_assistant_retrieval.py — у каждого есть точный
# ответ по базе, то есть модели дают одинаково содержательную сводку.
DEFAULT_QUESTIONS = [
    "Какие сделки сопровождала Orion?",
    "Какие сделки были у компании «Магнит»?",
    "Самая крупная сделка 2025 года",
    "сделки с опционом обратного выкупа",
    "Кто выходил из российского рынка?",
]


def bench_token() -> str:
    return os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or ""


def summarize(rows: list[dict]) -> list[dict]:
    """Строки стенда → по одной на модель: успешных, среднее время, средняя длина."""
    by_model: dict[str, list[dict]] = {}
    for r in rows:
        by_model.setdefault(r["model"], []).append(r)
    out = []
    for model, items in by_model.items():
        ok = [r for r in items if r.get("ok")]
        secs = [r["seconds"] for r in items if isinstance(r.get("seconds"), (int, float))]
        reasoning = [r["reasoning_tokens"] for r in ok if isinstance(r.get("reasoning_tokens"), (int, float))]
        errors = [r["error"] for r in items if r.get("error")]
        out.append({
            "model": model,
            "ok": len(ok),
            "total": len(items),
            "avg_seconds": round(sum(secs) / len(secs), 1) if secs else None,
            "avg_chars": round(sum(r["chars"] for r in ok) / len(ok)) if ok else 0,
            "avg_reasoning": round(sum(reasoning) / len(reasoning)) if reasoning else None,
            "error": errors[0] if errors else "",
        })
    return out


def render_table(summary: list[dict]) -> str:
    head = f"{'Модель':32} | {'успешных':>9} | {'ср. время, с':>12} | {'ср. длина, зн.':>14} | {'рассуждение, ток.':>17} | ошибка"
    lines = [head, "-" * len(head)]
    for s in summary:
        avg = "—" if s["avg_seconds"] is None else f"{s['avg_seconds']:.1f}"
        reasoning = "—" if s["avg_reasoning"] is None else str(s["avg_reasoning"])
        err = (s["error"] or "")[:70]
        lines.append(f"{s['model'][:32]:32} | {s['ok']:>4}/{s['total']:<4} | {avg:>12} | {s['avg_chars']:>14} | {reasoning:>17} | {err}")
    return "\n".join(lines)


def run(site: str, token: str, questions: list[str], models: list[str], mode: str, repeats: int,
        effort: str | None, context: tuple[str, str] | None, pause: float, verbose: bool) -> list[dict]:
    import httpx
    rows: list[dict] = []
    url = site.rstrip("/") + "/api/assistant/bench"
    # Дедлайн сервера — до 60 с на попытку; запрос стенда обязан ждать дольше.
    per_call_timeout = 60 * repeats + 30
    with httpx.Client(timeout=per_call_timeout) as client:
        for q in questions:
            for m in models:
                body = {"token": token, "question": q, "models": [m], "mode": mode, "repeats": repeats}
                if effort is not None:
                    body["reasoning_effort"] = effort
                if context:
                    body["context_type"], body["context_id"] = context
                started = time.monotonic()
                try:
                    r = client.post(url, json=body)
                    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    if r.status_code != 200:
                        rows.append({"model": m, "question": q, "ok": False, "seconds": round(time.monotonic() - started, 1),
                                     "chars": 0, "error": f"HTTP {r.status_code}: {data.get('error') or r.text[:200]}"})
                    else:
                        for row in data.get("results", []):
                            row["question"] = q
                            rows.append(row)
                        if verbose:
                            for row in data.get("results", []):
                                print(f"[{q[:40]}] {row['model']}: {'ok' if row['ok'] else 'сбой'} "
                                      f"{row['seconds']} с, {row['chars']} зн., попыток {row.get('attempts')}, "
                                      f"рассуждение {row.get('reasoning_tokens')} — "
                                      f"{(row.get('answer_head') or row.get('error') or '')[:120]!r}")
                except httpx.HTTPError as e:
                    rows.append({"model": m, "question": q, "ok": False, "seconds": round(time.monotonic() - started, 1),
                                 "chars": 0, "error": f"сеть: {e}"})
                time.sleep(pause)
    return rows


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Стенд сравнения моделей ассистента через боевой сервер")
    p.add_argument("--site", default=os.environ.get("APP_BASE_URL", DEFAULT_SITE))
    p.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    p.add_argument("--mode", choices=["base", "web"], default="base")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--question", action="append", help="свой вопрос (можно несколько); без него — пять из тестов")
    p.add_argument("--context", nargs=2, metavar=("TYPE", "ID"), help="страница, с которой задан вопрос: company yandex")
    p.add_argument("--effort", default=None, help="reasoning effort: none|minimal|low|medium|high|xhigh; \"\" — не передавать")
    p.add_argument("--pause", type=float, default=2.0)
    p.add_argument("--json", action="store_true", help="напечатать все строки как JSON вместо таблицы")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    token = bench_token()
    if not token:
        print("Нужен MODERATION_TOKEN (или TELEGRAM_WEBHOOK_SECRET) в окружении — тот же, что у /api/moderation/decisions.")
        return 2
    questions = a.question or DEFAULT_QUESTIONS
    rows = run(a.site, token, questions, a.models, a.mode, a.repeats, a.effort,
               tuple(a.context) if a.context else None, a.pause, a.verbose)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    print(f"Сервер: {a.site}; режим: {a.mode}; вопросов: {len(questions)}; повторов: {a.repeats}"
          + (f"; reasoning effort: {a.effort!r}" if a.effort is not None else ""))
    print(render_table(summarize(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
