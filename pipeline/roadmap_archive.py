# -*- coding: utf-8 -*-
"""Бэклог держит открытую работу, закрытая уезжает в архив.

ЗАЧЕМ. PRODUCT_ROADMAP.md читается КАЖДЫМ прогоном всех трёх рутин — это
постоянная стоимость, одна и та же для любой работы (см. CLAUDE.md,
«Стоимость прогона — это контекст, а не работа»). Значит, каждый знак в нём
должен что-то менять в том, что прогон СДЕЛАЕТ. Закрытый пункт не меняет
ничего: его перечитывают каждый час и не действуют по нему никогда.

Тот же приём уже применён 9 августа к журналу работ (свежие записи — в
основном файле, остальные — в архиве), и накладные тогда упали с 284 до
173 тыс. токенов на прогон. Здесь — то же самое для бэклога.

ЧТО ОСТАЁТСЯ В БЭКЛОГЕ ОТ ЗАКРЫТОГО. Одна строка: номер, название, вердикт
и куда смотреть. Строка нужна не для отчётности, а чтобы следующий прогон
не открыл заново то, что уже измерено и отвергнуто, — это прямое
продолжение правила «отвергнутая гипотеза с цифрами ценнее ненаписанного
правила». Всё остальное — разбор, грабли, цифры замеров — уезжает в архив
целиком, ни одного знака не выбрасывается.

    python3 pipeline/roadmap_archive.py --stats
    python3 pipeline/roadmap_archive.py --archive            # показать
    python3 pipeline/roadmap_archive.py --archive --write
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, "PRODUCT_ROADMAP.md")
ARCHIVE = os.path.join(ROOT, "PRODUCT_ROADMAP_ARCHIVE.md")

BACKLOG_HEAD = "## 4. Бэклог"
JOURNAL_HEAD = "## 5. Журнал работ"
ITEM = re.compile(r"^- ", re.M)
BLOCK = re.compile(r"^(### .*)$", re.M)
# «~~**A1. …**~~ — ЗАКРЫТ (прогон 9).» — вердикт стоит сразу за названием.
TITLE = re.compile(r"^- (?:~~)?\*\*(?P<code>[A-ZА-Я]\d+[a-zа-я]?)[.\s]\s*(?P<name>[^*]*?)\*\*(?:~~)?")
VERDICT = re.compile(r"(ЗАКРЫТ[А-ЯЁ]*|СДЕЛАН[А-ЯЁ]*|ПРОВЕРЕН[А-ЯЁ]*|СНЯТ[А-ЯЁ]*|"
                     r"ОТВЕРГНУТ[А-ЯЁ]*|ИСЧЕРПАН[А-ЯЁ]*|ГОТОВ[А-ЯЁ]*)"
                     r"(\s*\([^)]{0,60}\))?")


def missing_lines(before: str, after: str, archived: str) -> list:
    """Строки, которые исчезли бы вовсе, — ни в файле, ни в архиве.

    Проверка по СТРОКАМ, а не по абзацам: первая версия сверяла абзацы
    длиннее 80 знаков и поэтому не заметила пропажу заголовка блока и его
    вступления — они короткие. Перенос обязан быть переносом: всё, что ушло
    из бэклога, должно найтись в архиве дословно.
    """
    def norm(s):
        return re.sub(r"\s+", " ", s).strip()
    haystack = norm(after + "\n" + archived)
    out = []
    for line in before.splitlines():
        line = line.rstrip()
        n = norm(line)
        if len(n) < 4:
            continue
        if n not in haystack:
            out.append(line)
    return out


def tokens(text: str) -> int:
    """Оценка в токенах. Точный счётчик — если он есть в окружении."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return round(len(text) / 2.1)


def split_backlog(text: str) -> tuple:
    i, j = text.index(BACKLOG_HEAD), text.index(JOURNAL_HEAD)
    return text[:i], text[i:j], text[j:]


def parse(backlog: str) -> list:
    """Список пунктов: (блок, код, строка-заголовок, весь текст пункта)."""
    out, cur = [], None
    parts = BLOCK.split(backlog)
    for part in parts:
        if part.startswith("### "):
            cur = part.strip()
            continue
        if cur is None:
            continue
        starts = [m.start() for m in ITEM.finditer(part)]
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else len(part)
            body = part[s:e]
            # Последний пункт блока «съедал» всё до следующего пункта — а между
            # ним и следующим блоком стоит заголовок этого блока со вступлением.
            # 20 сентября так пропал весь заголовок «E. Живая база» с абзацем о
            # том, как устроен приток: пункт заменили строкой-заглушкой, и
            # заголовок ушёл вместе с ним.
            head = re.search(r"^#{2,3} ", body[1:], re.M)
            if head:
                e = s + 1 + head.start()
                body = part[s:e]
            m = TITLE.match(body)
            out.append({
                "block": cur,
                "code": m.group("code") if m else "",
                "name": re.sub(r"\s+", " ", m.group("name")).strip() if m else "",
                "text": body,
                "struck": body.startswith("- ~~"),
            })
    return out


def stub_for(item: dict) -> str:
    """Одна строка вместо пункта: название, вердикт, куда смотреть."""
    flat = re.sub(r"\s+", " ", item["text"])
    v = VERDICT.search(flat)
    verdict = (v.group(0).strip() if v else "ЗАКРЫТ")
    # Первая законченная мысль после вердикта — она и есть вывод.
    tail = flat[v.end():].lstrip(" .—-") if v else ""
    tail = re.split(r"(?<=[.!?])\s+(?=[А-ЯЁA-Z«*])", tail)[0] if tail else ""
    tail = re.sub(r"\*+", "", tail).strip()
    if tail and tail[:1].islower():
        tail = tail[:1].upper() + tail[1:]
    if len(tail) > 220:
        tail = tail[:217].rsplit(" ", 1)[0] + "…"
    # В названии пункта часто висит служебная скобка «(открыт 30 августа,
    # Этап 16)» — для строки-напоминания она лишняя, дата есть в вердикте.
    name = re.sub(r"\s*\([^()]*\)\s*$", "", item["name"].strip(" .")).strip(" .")
    head = "- ~~**%s. %s**~~ — %s." % (item["code"], name, verdict)
    return (head + (" " + tail if tail else "") +
            " Разбор — PRODUCT_ROADMAP_ARCHIVE.md.").replace("..", ".") + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--archive", action="store_true")
    ap.add_argument("--also", default="",
                    help="коды пунктов через запятую, закрытых без зачёркивания")
    ap.add_argument("--blocks", default="",
                    help="буквы блоков целиком, через запятую (например F)")
    ap.add_argument("--journal", action="store_true",
                    help="сдвинуть журнал: свежие дни остаются, остальные в архив")
    ap.add_argument("--keep-days", type=int, default=2,
                    help="сколько последних дней журнала оставить в основном файле")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)

    text = io.open(ROADMAP, encoding="utf-8").read()
    head, backlog, journal = split_backlog(text)
    items = parse(backlog)

    if a.journal:
        entries = [(m.start(), m.group(1)) for m in
                   re.finditer(r"^### (\d{4}-\d{2}-\d{2}).*$", journal, re.M)]
        if not entries:
            print("Записей журнала нет.")
            return 0
        days = sorted({d for _s, d in entries}, reverse=True)
        keep = set(days[:a.keep_days])
        bounds = [s for s, _d in entries] + [len(journal)]
        stay, move_j = [journal[:entries[0][0]]], []
        for i, (s, d) in enumerate(entries):
            chunk = journal[s:bounds[i + 1]]
            (stay if d in keep else move_j).append(chunk)
        if not move_j:
            print("Журнал и так короткий: дней %d, оставляем %d." % (len(days), a.keep_days))
            return 0
        new_journal = "".join(stay)
        print("Журнал: %d записей, дней %d. Остаются дни: %s"
              % (len(entries), len(days), ", ".join(sorted(keep, reverse=True))))
        print("В архив уезжает записей: %d" % len(move_j))
        print("Журнал: %d → %d токенов (освободилось %d)"
              % (tokens(journal), tokens(new_journal),
                 tokens(journal) - tokens(new_journal)))
        lost = missing_lines(text, head + backlog + new_journal,
                             io.open(ARCHIVE, encoding="utf-8").read() + "".join(move_j))
        if lost:
            print("\nОТКАЗ: %d строк исчезло бы вовсе, а не переехало:" % len(lost))
            for line in lost[:8]:
                print("   %s" % line[:110])
            return 1
        if not a.write:
            print("\n(сухой прогон; чтобы записать — --write)")
            return 0
        io.open(ARCHIVE, "a", encoding="utf-8").write(
            "\n\n## Записи журнала, сдвинутые %s\n\n" % date.today().isoformat()
            + "".join(move_j))
        io.open(ROADMAP, "w", encoding="utf-8").write(head + backlog + new_journal)
        print("\nзаписано")
        return 0

    if a.stats or not a.archive:
        print("PRODUCT_ROADMAP.md — %d токенов" % tokens(text))
        print("   шапка   %7d" % tokens(head))
        print("   бэклог  %7d" % tokens(backlog))
        print("   журнал  %7d" % tokens(journal))
        print()
        print("%-46s %5s %5s %9s" % ("блок", "откр", "закр", "ток. закр"))
        seen = {}
        for it in items:
            s = seen.setdefault(it["block"], [0, 0, 0])
            s[1 if it["struck"] else 0] += 1
            if it["struck"]:
                s[2] += tokens(it["text"])
        for b, s in seen.items():
            print("%-46s %5d %5d %9d" % (b[4:50], s[0], s[1], s[2]))
        print()
        print("Закрытые пункты стоят %d токенов в каждом прогоне каждой рутины."
              % sum(s[2] for s in seen.values()))
        return 0

    also = {c.strip() for c in a.also.split(",") if c.strip()}
    blocks = {c.strip() for c in a.blocks.split(",") if c.strip()}
    move = [it for it in items
            if it["struck"] or it["code"] in also
            or (it["block"][4:5] in blocks)]
    if not move:
        print("Переносить нечего.")
        return 0

    new_backlog = backlog
    for it in move:
        new_backlog = new_backlog.replace(it["text"], stub_for(it), 1)
    # Блок, от которого остались одни заглушки, остаётся на месте: он
    # показывает, что направление было пройдено целиком.
    saved = tokens(backlog) - tokens(new_backlog)
    print("Переносится пунктов: %d" % len(move))
    print("Бэклог: %d → %d токенов (освободилось %d)"
          % (tokens(backlog), tokens(new_backlog), saved))
    for it in move[:5]:
        print("   %-6s %s" % (it["code"], it["name"][:70]))
    lost = missing_lines(text, head + new_backlog + journal,
                         io.open(ARCHIVE, encoding="utf-8").read()
                         + "".join(it["text"] for it in move))
    if lost:
        print("\nОТКАЗ: %d строк исчезло бы вовсе, а не переехало:" % len(lost))
        for line in lost[:8]:
            print("   %s" % line[:110])
        return 1

    if not a.write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0

    chunk = ["\n\n## Закрытые пункты бэклога (перенесены %s)\n" % date.today().isoformat(),
             "\nПеренесены из PRODUCT_ROADMAP.md дословно: в бэклоге от каждого "
             "осталась строка с вердиктом.\n\n"]
    for it in move:
        chunk.append(it["text"].rstrip() + "\n\n")
    io.open(ARCHIVE, "a", encoding="utf-8").write("".join(chunk))
    io.open(ROADMAP, "w", encoding="utf-8").write(head + new_backlog + journal)
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main())
