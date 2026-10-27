#!/usr/bin/env python3
"""Задает вопросы набора (questions.py) ассистенту сайта так же, как сайт.

На каждый вопрос — два запроса, как в runAsk() static/index.html: быстрый
поиск по базе `POST /api/assistant/lookup` (кроме уточнения в диалоге — там
сайт его не делает) и ответ модели `POST /api/ask` с тем же телом: режим,
context_type/context_id, history. Ответы пишутся построчно в jsonl в
data/inbox/assistant_eval/ (папка не в git).

ДИАЛОГИ НЕ СОХРАНЯЮТСЯ. Сервер пишет диалог в базу пользователей, только если
запрос пришел с куки вошедшего и `save_thread` истинно (main.py, ask). Скрипт
не входит и не шлет куки, а `save_thread` ставит false — в аккаунты ничего не
попадает.

ЛИМИТ ЧАСТОТЫ. У /api/ask и /api/assistant/lookup общий лимит на адрес —
40 запросов за 10 минут (scrape_guard.py). Если в окружении есть служебный
ключ (MODERATION_TOKEN или TELEGRAM_WEBHOOK_SECRET — тот же, что у стенда
assistant_bench.py), он уходит заголовком X-Data-Key и лимит не действует;
без ключа скрипт сам ждет 15 с между запросами (100 вопросов — около часа).

    python3 pipeline/assistant_eval/run.py                      # все 100 + подготовка к встрече
    python3 pipeline/assistant_eval/run.py --only 13,57,92      # выборка
    python3 pipeline/assistant_eval/run.py --prep-only
    python3 pipeline/assistant_eval/run.py --site http://127.0.0.1:8000 --out /tmp/x.jsonl
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from questions import PREP, QUESTIONS, SIGNALS  # noqa: E402

DEFAULT_SITE = "https://projectcompass.ru"
OUT_DIR = ROOT / "data" / "inbox" / "assistant_eval"
# Браузер ждет 45 с «по базе» и 75 с «по интернету» (aiAnswer) — так же.
TIMEOUT = {"base": 45, "web": 75}


def _key() -> str:
    return (os.environ.get("MODERATION_TOKEN") or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "").strip()


def post(site: str, path: str, body: dict, timeout: float, key: str) -> tuple[int, dict | None, float, str]:
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (kompas-assistant-eval)"}
    if key:
        headers["X-Data-Key"] = key
    req = urllib.request.Request(site.rstrip("/") + path, data=json.dumps(body).encode(), headers=headers)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "null"), time.monotonic() - t0, ""
    except urllib.error.HTTPError as e:
        return e.code, None, time.monotonic() - t0, e.read().decode(errors="replace")[:300]
    except Exception as e:  # noqa: BLE001 — сбой сети тоже результат проверки
        return 0, None, time.monotonic() - t0, f"{type(e).__name__}: {e}"


def ask_one(site: str, q: dict, key: str, pause: float) -> dict:
    history = q.get("history") or []
    base = {"question": q["question"], "context": "", "context_type": q.get("context_type") or "general",
            "context_id": q.get("context_id"), "history": history[-6:]}
    row = {k: q.get(k) for k in ("n", "group", "src", "question", "shown", "mode", "context_type",
                                 "context_id", "history", "note")}
    if not history:
        st, data, sec, err = post(site, "/api/assistant/lookup", base, 30, key)
        row["lookup"] = {"status": st, "seconds": round(sec, 2), "error": err,
                         "answer": (data or {}).get("answer"), "intent": (data or {}).get("intent")}
        time.sleep(pause)
    body = dict(base, mode=q.get("mode") or "base", thread_id=None, save_thread=False)
    st, data, sec, err = post(site, "/api/ask", body, TIMEOUT.get(body["mode"], 45) + 5, key)
    data = data or {}
    row.update(status=st, seconds=round(sec, 2), error=err, answer=data.get("answer"),
               deals=data.get("deals"), intent=data.get("intent"), refused=data.get("refused"),
               model=data.get("model", None if not data else True), fallback=data.get("fallback"))
    if data.get("thread_id"):
        row["warning"] = "сервер сохранил диалог — проверить, не пришли ли куки"
    time.sleep(pause)
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", default=DEFAULT_SITE)
    ap.add_argument("--only", default="", help="номера через запятую (P1…P4 — подготовка к встрече, S1…S8 — признаки сделок)")
    ap.add_argument("--prep-only", action="store_true")
    ap.add_argument("--no-prep", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--pause", type=float, default=None, help="пауза между запросами, с")
    a = ap.parse_args()

    key = _key()
    pause = a.pause if a.pause is not None else (1.0 if key else 15.0)
    items = [] if a.prep_only else list(QUESTIONS)
    if not a.no_prep:
        items += PREP
    if not a.prep_only:
        items += SIGNALS
    if a.only:
        want = {s.strip() for s in a.only.split(",") if s.strip()}
        items = [q for q in QUESTIONS + PREP + SIGNALS if str(q["n"]) in want]

    health = {}
    try:
        with urllib.request.urlopen(a.site.rstrip("/") + "/health", timeout=15) as r:
            health = json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        health = {"error": str(e)}
    out = Path(a.out) if a.out else OUT_DIR / f"answers_{dt.datetime.now():%Y-%m-%d_%H%M}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"сайт {a.site}, сборка {health.get('build')}, ключ {'есть' if key else 'нет'}, вопросов {len(items)} → {out}")
    with out.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": {"site": a.site, "health": health,
                                     "started": dt.datetime.now().isoformat(timespec="seconds")}},
                           ensure_ascii=False) + "\n")
        for q in items:
            row = ask_one(a.site, q, key, pause)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{row['n']:>4} {row['status']} {row['seconds']:5.1f} с {row.get('intent') or '—':10} "
                  f"{(row.get('answer') or row.get('error') or '')[:70]!r}", flush=True)


if __name__ == "__main__":
    main()
