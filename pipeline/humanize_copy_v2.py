#!/usr/bin/env python3
"""Убирает из карточек канцелярские и шаблонные обороты.

Скрипт намеренно консервативный: меняет только повествовательные поля и только
устойчивые конструкции. Названия сторон, суммы, условия и цитаты источников не
переписываются.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "static/data/deals_promoted.json",
    ROOT / "static/data/deals_2026.json",
    ROOT / "static/data/curated_deals.json",
    ROOT / "static/data/bulk_deals.json",
]

FIELDS = {
    "extra", "role",
    "eco.rationale", "eco.context", "eco.fin", "eco.target_fin", "eco.share",
    "law.struct", "law.terms", "law.appr",
}

def _match_case(replacement: str):
    def repl(match: re.Match[str]) -> str:
        return replacement if match.group(0)[:1].isupper() else replacement[:1].lower() + replacement[1:]
    return repl


RULES: list[tuple[str, re.Pattern[str], object]] = [
    ("данная сделка", re.compile(r"\bданная сделка\b", re.I), _match_case("Сделка")),
    ("по данной сделке", re.compile(r"\bпо данной сделке\b", re.I), _match_case("По этой сделке")),
    ("в рамках сделки", re.compile(r"\bв рамках сделки\b", re.I), _match_case("По сделке")),
    ("объект представляет собой", re.compile(r"\bОбъект представляет собой\b", re.I), _match_case("Это")),
    ("структурирована следующим образом", re.compile(r"\bСделка структурирована следующим образом:\s*", re.I), _match_case("Структура сделки: ")),
    ("структурирована как", re.compile(r"\bСделка структурирована как\s+", re.I), _match_case("Структура сделки: ")),
    ("структурирована через", re.compile(r"\bСделка структурирована через\s+", re.I), _match_case("Сделка проведена через ")),
    ("цель сделки", re.compile(r"\bСделка направлена на\b", re.I), _match_case("Цель сделки —")),
    ("цель приобретения", re.compile(r"\bПриобретение направлено на\b", re.I), _match_case("Цель приобретения —")),
    ("представляет собой", re.compile(r"(?:(?<=^)|(?<=[.!?])\s+)Сделка представляет собой\s+"), lambda m: (m.group(0)[:-len("Сделка представляет собой ")] + "Это ")),
    ("является", re.compile(r"(?:(?<=^)|(?<=[.!?])\s+)Сделка является\s+"), lambda m: (m.group(0)[:-len("Сделка является ")] + "Это ")),
    ("описана как", re.compile(r"(?:(?<=^)|(?<=[.!?])\s+)Сделка описана как\s+"), lambda m: (m.group(0)[:-len("Сделка описана как ")] + "По публичным источникам, это ")),
]

THUS = re.compile(r"\bТаким образом,\s*([а-яё])")
INLINE_THUS = [
    (re.compile(r"—\s*таким образом,?\s*", re.I), "— "),
    (re.compile(r";\s*таким образом,?\s*", re.I), "; в результате "),
    (re.compile(r",\s*таким образом,?\s*", re.I), "; "),
]


def humanize(text: str, stats: Counter) -> str:
    out = text
    # Заголовок внутри повествовательного поля не нужен: «Сделка: компания...»
    # читается как машинная выгрузка. Убираем его только в начале строки.
    out, n = re.subn(r"^\s*Сделка:\s*", "", out, flags=re.I)
    if n and out[:1].isalpha():
        out = out[:1].upper() + out[1:]
    stats["Сделка: в начале"] += n
    # Иногда модель сохраняла JSON-null как слово. Переписываем только точный
    # шаблон, не затрагивая раскрытые суммы и исходные цитаты.
    out, n = re.subn(
        r"Сумма:\s*null\s*\(сумма по (?:данной|этой) сделке не указана;\s*([^()]*)\)\.?",
        lambda m: "Сумма этой части сделки не раскрыта; " + m.group(1).strip().rstrip(".") + ".",
        out,
        flags=re.I,
    )
    stats["Сумма: null"] += n
    for name, rx, replacement in RULES:
        out, n = rx.subn(replacement, out)
        stats[name] += n
    def repl_thus(match: re.Match[str]) -> str:
        stats["таким образом"] += 1
        return match.group(1).upper()
    out = THUS.sub(repl_thus, out)
    for rx, replacement in INLINE_THUS:
        out, n = rx.subn(replacement, out)
        stats["таким образом — внутри фразы"] += n
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()


def walk_deal(deal: dict, stats: Counter) -> int:
    changed = 0
    for key in ("extra", "role"):
        if isinstance(deal.get(key), str):
            old = deal[key]; new = humanize(old, stats)
            if new != old: deal[key] = new; changed += 1
    for parent in ("eco", "law"):
        obj = deal.get(parent)
        if not isinstance(obj, dict):
            continue
        for key, value in list(obj.items()):
            path = f"{parent}.{key}"
            if path not in FIELDS or not isinstance(value, str):
                continue
            new = humanize(value, stats)
            if new != value:
                obj[key] = new
                changed += 1
    return changed


def main() -> None:
    stats = Counter(); files = Counter()
    for path in FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        deals = data.get("deals", []) if isinstance(data, dict) else data
        for deal in deals:
            files[path.name] += walk_deal(deal, stats)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Изменённые поля:")
    for name, count in files.items(): print(f"  {name}: {count}")
    print("Замены:")
    for name, count in stats.most_common(): print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
