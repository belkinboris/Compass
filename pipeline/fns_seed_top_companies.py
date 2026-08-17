# -*- coding: utf-8 -*-
"""Первый, безопасный шаг синхронизации ФНС — заведомо верные ИНН.

ПОЧЕМУ ЭТОТ СКРИПТ СУЩЕСТВУЕТ. `--match` ищет юрлицо ПО ИМЕНИ через платный
метод `search` — с квотой 3000 запросов в год на метод и почти 1900
профилями в базе один неосторожный прогон тратит больше половины годовой
квоты `search` за раз. Но для самых заметных компаний ИНН и так известен
и легко проверяется по нескольким независимым источникам — тратить на них
`search` незачем: `confirm_by_inn()` идёт сразу в `egr` по номеру, а не
подбирает компанию по имени.

ИНН ниже — не из памяти модели, а проверены живым поиском 18 августа 2026
по НЕСКОЛЬКИМ независимым агрегаторам (rusprofile.ru, spark-interfax.ru,
companies.rbc.ru), у Сбербанка — дополнительно сверен с реестром Банка
России (cbr.ru/finorg) как самым авторитетным источником. Это первые семь
компаний по числу сделок в базе (`load_company_catalog()['deal_count']`) —
тот же признак важности, что уже используется для приоритета `--match` и
для профильных описаний.

НЕ ВКЛЮЧЕНЫ И ПОЧЕМУ. VK и Газпромбанк — следующие по deal_count, но
однозначный номер живым поиском в этом прогоне подтвердить не удалось (у
VK — сложная структура из МКАО/АО, у Газпромбанка поиск не вернул номер
надёжно). Softline — известная ловушка: у группы есть материнская
структура и минимум одно юрлицо-«дочка» («Софтлайн Решения»), и по имени
не разобрать, какое из них наша карточка `softline` имеет в виду; давать
здесь номер наугад — то же самое, что описано в CLAUDE.md как «конкретно
звучащее имя компании тоже бывает однофамильцем». Эти три остаются на
обычный `--match` (по имени, с порогом автоподтверждения) — риск получить
кандидата в очередь на ручную проверку безопаснее, чем зашить неверный ИНН.

ЗАПУСК (после того как API_FNS_KEY задан в окружении):
    python3 pipeline/fns_seed_top_companies.py            # сухой прогон
    python3 pipeline/fns_seed_top_companies.py --write    # запись

Каждая запись — один вызов `egr`, ни одного `search`: семь компаний это
семь запросов, меньше 0,3% годовой квоты `egr`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.session import SessionLocal, engine  # noqa: E402
from db.models import Base  # noqa: E402
from fns_client import ApiFnsClient, ApiFnsError  # noqa: E402
from pipeline.sync_fns import confirm_by_inn  # noqa: E402

# company_id -> (ИНН, источник проверки)
SEED = {
    "gc2792a44": ("7703104630", "rusprofile.ru, spark-interfax.ru, companies.rbc.ru — АФК «Система»"),
    "g28ff15bb": ("7707083893", "cbr.ru/finorg, spark-interfax.ru — ПАО Сбербанк"),
    "yandex":    ("7736207543", "rusprofile.ru, spark-interfax.ru, companies.rbc.ru — ООО «Яндекс»"),
    "gcafc31dc": ("7702070139", "list-org.com, zachestnyibiznes.ru — БАНК ВТБ (ПАО)"),
    "g00f14033": ("7707049388", "spark-interfax.ru, company.rt.ru (офиц. сайт) — ПАО «Ростелеком»"),
    "g69c88bc7": ("7740000076", "spark-interfax.ru, rusprofile.ru, companies.rbc.ru — ПАО «МТС»"),
    "g549ab474": ("9714053621", "rbc.ru, avoshop.ru — ООО «РВБ» (Wildberries & Russ)"),
}


def main(argv: list[str]) -> int:
    write = "--write" in argv
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        with ApiFnsClient() as client:
            for company_id, (inn, source) in SEED.items():
                print(f"{company_id}: ИНН {inn} ({source})")
                try:
                    confirm_by_inn(db, client, company_id, inn, dry_run=not write)
                except ApiFnsError as exc:
                    print(f"  ОШИБКА: {exc}", file=sys.stderr)
    if not write:
        print("\nСухой прогон: egr всё равно запрошен по каждому ИНН (иначе "
              "нечем проверить, что номер верный) — это те же 7 запросов, "
              "просто без записи в базу. Добавьте --write, когда результат "
              "выше выглядит правильно.")
    else:
        print("\nЗаписано. Следующий шаг — pipeline/sync_fns.py --sync "
              "--company-id <id> по каждой (или --sync --limit N без "
              "--company-id заберёт все подтверждённые разом).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
