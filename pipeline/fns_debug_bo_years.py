# -*- coding: utf-8 -*-
"""Диагностика: какие годы реально отдаёт метод `bo` прямо сейчас.

НИЧЕГО НЕ ПИШЕТ В БАЗУ — только печатает. Нужен, когда показатель на сайте
выглядит устаревшим (например, «АФК Система — отчётность 2021 года»), и
непонятно, это ограничение самого источника (ГИР БО) или наш разбор
пропустил более свежие годы (BO_LINES в fns_client.py заточен под обычную
коммерческую форму — 2110/2400/1600/1300 и т.д.; банковская форма
отчётности использует другие коды строк, и это ожидаемо даёт пустые поля,
а не баг).

ЗАПУСК:
    python3 pipeline/fns_debug_bo_years.py 7707083893 7702070139 7703104630
    (аргументы — ИНН через пробел; по умолчанию — Сбербанк, ВТБ, АФК Система)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fns_client import ApiFnsClient, BO_LINES, normalize_bo  # noqa: E402

DEFAULT_INNS = {
    "7707083893": "ПАО Сбербанк",
    "7702070139": "БАНК ВТБ (ПАО)",
    "7703104630": "АФК «Система»",
}


def main(argv):
    inns = {inn: DEFAULT_INNS.get(inn, inn) for inn in argv} if argv else DEFAULT_INNS
    with ApiFnsClient() as client:
        for inn, name in inns.items():
            print(f"\n{'='*60}\n{name} (ИНН {inn})")
            raw = client.bo(inn)
            top_keys = list(raw.keys()) if isinstance(raw, dict) else []
            print(f"  верхнеуровневые ключи ответа: {top_keys}")
            reports = normalize_bo(raw, inn)
            years = [r["year"] for r in reports]
            print(f"  годы, которые наш разбор увидел: {years}")
            if reports:
                latest = reports[-1]
                filled = [k for k in BO_LINES if latest.get(k) is not None]
                empty = [k for k in BO_LINES if latest.get(k) is None]
                print(f"  последний год {latest['year']}: заполнено полей {len(filled)} из {len(BO_LINES)}")
                if empty:
                    print(f"  пустые поля: {empty}")
            else:
                print("  разбор не нашёл ни одного года — проверьте raw ниже вручную")
            if not reports or not top_keys:
                print(f"  RAW (первые 800 знаков): {json.dumps(raw, ensure_ascii=False)[:800]}")


if __name__ == "__main__":
    main(sys.argv[1:])
