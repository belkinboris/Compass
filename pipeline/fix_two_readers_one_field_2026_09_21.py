# -*- coding: utf-8 -*-
"""Два читателя, одно поле: второй затёр то, что первый туда только что перенёс.

СИМПТОМ. У карточки `g1f098415` (Kellogg → «Черноголовка») из базы совсем
исчезло предложение «Об интересе «Черноголовки» к бизнесу Kellogg стало
известно в декабре 2022 года.» — его не осталось ни в одном поле.

ЧТО ПРОИЗОШЛО. Две находки очереди аудита на одной карточке разбирали разные
читатели. Первый перенёс это предложение из «Зачем» (`eco.rationale`) в
пустой «Контекст». Второй читал карточку ПОСЛЕ него, увидел в «Контексте»
чужое предложение — и вернул туда своё описание завода ЦЕЛИКОМ, как и
требует формат ответа («new_full_text — полный текст поля»). Формат сделал
ровно то, что обещал: поле заменено целиком, вместе с содержимым.

ПОЧЕМУ ЭТОГО НЕ ПОЙМАЛА ПРОВЕРКА. `fix_audit_close_2026_09_21.py` сверяет
`old_full_text` с тем, что в базе, и откатывает находку, если «до» устарело.
Здесь «до» НЕ устарело: второй читатель видел свежее состояние и честно его
переписал. Проверка отвечает на вопрос «не изменилось ли поле с тех пор»,
а не на вопрос «не выбрасывает ли новая версия текст, которого нет больше
нигде в карточке».

ЧЕМ ЗАКРЫТО. Предложение возвращено в «Контекст» рядом с описанием завода.
Инвариантом по всей базе такое не поймать — у базы нет состояния «до», а
потеря видна только в сравнении. Поэтому проверка стоит там, где сравнение
есть: `fix_audit_close_2026_09_21.lost_sentences()` откатывает находку,
после которой предложение не находится в карточке нигде. Случай Kellogg
воспроизведён в `test_ingest.py::test_a_move_between_fields_never_drops_a_
sentence_another_reader_just_moved_in`.

    python3 pipeline/fix_two_readers_one_field_2026_09_21.py
    python3 pipeline/fix_two_readers_one_field_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

CARD = "g1f098415"
LOST = "Об интересе «Черноголовки» к бизнесу Kellogg стало известно в декабре 2022 года."
KEEP = ("«Келлогг Рус» была ключевой производственной площадкой Kellogg в России. "
        "На заводе выпускают печенье и готовые завтраки.")


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    card = next((d for d in data["deals"] if d["id"] == CARD), None)
    if card is None:
        print("карточки %s нет" % CARD)
        return 1

    eco = card.setdefault("eco", {})
    ctx = str(eco.get("context") or "").strip()
    if LOST in ctx:
        print("Уже на месте.")
        return 0

    new = (LOST + " " + ctx) if ctx and ctx != "—" else LOST
    if ctx == KEEP:
        # Хронология вперёд, описание завода следом: сначала «когда стало
        # известно», потом «что за завод».
        new = LOST + " " + KEEP
    print("   %s: в «Контекст» возвращено предложение, потерянное при переносе" % CARD)
    print("      было:  %s" % (ctx or "(пусто)"))
    print("      стало: %s" % new)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    eco["context"] = new
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
