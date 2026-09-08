"""Окна простоя сайта по журналу приложения с Timeweb.

Что делает. Берёт выгрузку журнала приложения из панели Timeweb (файл
`applogs…txt`, 20 000 последних строк) и печатает таблицу: когда процесс
замолчал, когда заговорил снова, сколько минут между ними, штатно ли он
завершился (строка «Shutting down» перед провалом) и стартовал ли после
провала новый процесс. Отдельно — какие пути и с каких адресов проверяют
живость (проверка из контейнера — 127.0.0.1, платформенный прокси —
172.18.0.x): вопрос «не сломала ли смена пути health-check» решается одной
строкой этой сводки, а не догадкой.

Почему это скрипт, а не разовый разбор. 8 сентября 2026 сайт за ночь лёг
трижды, и три диагноза подряд ставились по внешним признакам — тишине
порта, скриншотам панели, совпадению по времени с собственной правкой.
Все три оказались неточными. Журнал приложения за 41 час ответил за
минуту: ни в одном из 25 окон простоя процесс не завершался штатно — его
убивала платформа без SIGTERM в момент, когда новый образ доехал до
реестра; обычная дыра деплоя ≈5 минут, при сбое шага деплоя — 19–44 минуты
до отката. Держать этот разбор в голове не нужно — нужно уметь повторить
его на следующей выгрузке.

Как читать таблицу. В журнале метки времени несут только наши строки
(httpx, kompas.*), строки доступа uvicorn — без времени; поэтому окно
считается по соседним меткам, а простоем признаётся только промежуток, в
котором НЕТ вообще никаких строк (иначе интервал `data_refresh` в 5 минут
между двумя метками выглядел бы как провал). «ОБОРВАН» — перед тишиной нет
«Shutting down», то есть обработчик остановки нашего приложения не
запускался и ничего в процессе сделать не мог.

Запуск:
    python3 pipeline/deploy_outages.py <путь к applogs….txt> [--min-gap 3]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime

TS = re.compile(r"^(2026-\d\d-\d\d \d\d:\d\d:\d\d)")
STARTUP_MARKERS = (
    "Started server process",
    "Waiting for application startup",
    "Application startup complete",
    "Uvicorn running",
)
ACCESS = re.compile(r'^INFO:\s+([\d.]+):\d+ - "(\w+) (\S+) HTTP')


def outages(lines: list[str], min_gap_min: float):
    stamped = []
    for i, line in enumerate(lines):
        m = TS.match(line)
        if m:
            stamped.append((i, datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")))
    rows = []
    for (i1, t1), (i2, t2) in zip(stamped, stamped[1:]):
        gap = (t2 - t1).total_seconds() / 60
        if gap <= min_gap_min:
            continue
        inner = [l for l in lines[i1 + 1:i2] if l.strip()]
        noise = [l for l in inner if not any(k in l for k in STARTUP_MARKERS)]
        if len(noise) > 2:
            continue  # процесс жил и писал строки доступа — это не простой
        graceful = any("Shutting down" in l for l in lines[max(0, i1 - 12):i1 + 1])
        restarted = any("Started server process" in l for l in lines[i1:i2 + 6])
        rows.append((t1, t2, gap, graceful, restarted))
    return stamped, rows


def health_paths(lines: list[str]):
    seen: dict[tuple[str, str, str], int] = {}
    for line in lines:
        m = ACCESS.match(line)
        if not m:
            continue
        ip, method, path = m.groups()
        path = path.split("?")[0]
        origin = "контейнер (127.0.0.1)" if ip.startswith("127.") else "прокси платформы (%s)" % ip
        if path in ("/", "/health"):
            key = (origin, method, path)
            seen[key] = seen.get(key, 0) + 1
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--min-gap", type=float, default=3.0, help="минимальная тишина, минут (по умолчанию 3)")
    args = ap.parse_args()
    lines = open(args.path, encoding="utf-8", errors="replace").read().split("\n")
    stamped, rows = outages(lines, args.min_gap)
    if not stamped:
        print("в файле нет строк с меткой времени — это не журнал приложения?")
        return 1
    span_h = (stamped[-1][1] - stamped[0][1]).total_seconds() / 3600
    print("журнал: %s → %s (%.1f ч, %d строк)" % (stamped[0][1], stamped[-1][1], span_h, len(lines)))
    print()
    print("Проверки живости по путям / и /health:")
    for (origin, method, path), n in sorted(health_paths(lines).items(), key=lambda kv: -kv[1]):
        print("  %-26s %-5s %-8s %5d раз" % (origin, method, path, n))
    print()
    print("Окна простоя (тишина дольше %.0f мин без единой строки), UTC:" % args.min_gap)
    print("  %-17s%-10s%6s   %-30s  %s" % ("от", "до", "мин", "старый процесс", "после"))
    total = 0.0
    for t1, t2, gap, graceful, restarted in rows:
        total += gap
        print("  %-17s%-10s%6.1f   %-30s  %s" % (
            t1.strftime("%d.%m %H:%M:%S"), t2.strftime("%H:%M:%S"), gap,
            "штатно (Shutting down)" if graceful else "ОБОРВАН, без Shutting down",
            "новый процесс стартует" if restarted else "без старта"))
    if rows:
        print()
        print("итого: %d окон, %.0f мин простоя (%.1f%% времени журнала); "
              "самое длинное — %.0f мин" % (len(rows), total, 100 * total / 60 / span_h,
                                            max(r[2] for r in rows)))
        killed = sum(1 for r in rows if not r[3])
        print("обрывов без штатной остановки: %d из %d — столько раз процесс убивала платформа, "
              "а не останавливал наш код" % (killed, len(rows)))
    else:
        print("  простоев не найдено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
