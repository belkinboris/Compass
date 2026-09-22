# -*- coding: utf-8 -*-
"""Выложить КОД на боевой сайт: ветка `release`.

ЗАЧЕМ ОТДЕЛЬНАЯ ВЕТКА (и почему её нельзя отменить). Timeweb пересобирает
приложение на каждый пуш в ветку сборки. Рутины коммитят 4–5 раз в час, и
почти всегда это данные, а не код. В ночь на 3 сентября 2026 три пуша за
минуту наложились друг на друга, и сайт отдавал 502 девять минут подряд.
Поэтому данные и код разъехались: приложение собирается из `release`, куда
попадает только код, а свежую базу сайт тянет сам из `main` (см.
`data_refresh.py`). Пересборка случается тогда и только тогда, когда
изменился код.

ЧТО СЛОМАЛОСЬ ИЗ-ЗА ЭТОГО 22 сентября 2026. Ветка задачи была сведена в
`main`, полный pytest прошёл, всё выложено — и ничего не появилось на сайте.
`main.py` на проде оставался версией от 20 сентября: `main` не собирается.
Владелец в это время не находил кнопку, которую мы «уже сделали». Шаг
«обновить release» держался в голове и в pull request'ах, то есть нигде.

ЧТО ДЕЛАЕТ СКРИПТ. Сравнивает `release` и `main` по КОДУ (не по данным) и,
если код разошёлся, переносит `main` в `release` и пушит. Если разошлись
только данные — не делает ничего и говорит об этом: лишняя пересборка это
те самые 502 на девять минут.

    python3 pipeline/release.py            # показать, что выложится
    python3 pipeline/release.py --write    # выложить
"""
from __future__ import annotations

import subprocess
import sys

# Файлы, которые сайт читает НА ХОДУ (data_refresh.py). Их изменение не
# требует пересборки — и не должно её вызывать.
DATA_PATHS = (
    "static/data/",
    "data/inbox/",
    "pipeline/fns_registry.py",
    "pipeline/access_requests_sent.json",
    # Папка с финансовой моделью и записками к ней: на сайте не исполняется
    # ничего из неё, а пересборка из-за правки таблицы — это те самые 502.
    "finance/",
)
# Документация и заметки на работу сайта не влияют.
DOC_SUFFIXES = (".md", ".xlsx")


def git(*args: str) -> str:
    # core.quotepath=false обязателен: иначе git отдаёт кириллические имена в
    # кавычках и восьмеричных escape-последовательностях, и любая проверка
    # вида path.endswith(".md") на них молча не срабатывает — документ уезжает
    # как код и тянет за собой лишнюю пересборку сайта.
    out = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit("git %s: %s" % (" ".join(args), out.stderr.strip()[:300]))
    return out.stdout.strip()


def is_code(path: str) -> bool:
    if any(path.startswith(p) for p in DATA_PATHS):
        return False
    if path.endswith(DOC_SUFFIXES):
        return False
    # Тесты кодом сайта не являются, но пусть едут вместе с ним: иначе на
    # `release` окажется код без своих проверок, и откат станет гаданием.
    return True


def main(write: bool) -> int:
    git("fetch", "origin", "main", "release")
    changed = [p for p in git("diff", "--name-only", "origin/release", "origin/main").splitlines() if p]
    code = sorted(p for p in changed if is_code(p))
    data = sorted(p for p in changed if not is_code(p))

    print("Расхождение release и main: %d файлов" % len(changed))
    print("  код:    %d" % len(code))
    print("  данные и документы: %d" % len(data))
    if not code:
        print("\nКод не менялся — выкладывать нечего. Свежую базу сайт возьмёт сам "
              "(data_refresh.py), пересборка ради данных вызвала бы простой на минуты.")
        return 0
    for p in code[:25]:
        print("   %s" % p)
    if len(code) > 25:
        print("   … и ещё %d" % (len(code) - 25))
    if not write:
        print("\n(сухой прогон; чтобы выложить — --write)")
        return 0

    was = git("rev-parse", "--abbrev-ref", "HEAD")
    git("checkout", "-B", "release", "origin/release")
    try:
        subprocess.run(["git", "merge", "origin/main", "--no-edit"], check=True)
        git("push", "origin", "release")
        print("\nВыложено: release -> %s" % git("rev-parse", "--short", "HEAD"))
        print("Сборка на хостинге занимает несколько минут. Проверить, что доехало:")
        print("  curl -s https://projectcompass.ru/health")
    finally:
        git("checkout", was)
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
