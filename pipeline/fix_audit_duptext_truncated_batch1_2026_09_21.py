# -*- coding: utf-8 -*-
"""Очередь аудита: DUPLICATE_TEXT (обе оставшиеся находки) и TRUNCATED
(5 из 7 — у двух надёжной границы предложения для обрезки нет, они не
трогаются, дообогащение из первоисточника не входит в этот перенос).

DUPLICATE_TEXT: eco.rationale в обеих карточках — пересказ фактов, уже
верно стоящих в eco.share/extra/law.appr, без единого слова о мотиве.
Очищено до «—» (пустое поле честнее переизложения чужого факта под
неверной подписью).

TRUNCATED: events[].note обрывается многоточием на середине предложения.
Обрезано до последнего целого предложения; у g3ecb7b86 вдобавок снят
служебный повтор заголовка и подзаголовок источника («Об объекте сделки»)
перед первым предложением. Два случая без единого целого предложения в
поле (gb0f1f736 events[0], gda6baa02 events[1]) не тронуты — обрезка
оставила бы пустую строку, а дозабор текста без первоисточника был бы
досочинением.

    python3 pipeline/fix_audit_duptext_truncated_batch1_2026_09_21.py
    python3 pipeline/fix_audit_duptext_truncated_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402

# card_id -> новый текст eco.rationale
CLEAR_RATIONALE = {
    "g0f9ca0a0": "—",
    "ge6f1e0ae": "—",
}

# card_id -> {event_index: new_note}
TRIM_EVENTS = {
    "g3ecb7b86": {
        0: ("Группа « ДОМ.РФ » приобрела у S8 Capital лифтовый бизнес, включающий "
            "Meteor Lift и АО «Лифт Коннект» — бывшие российские активы американской "
            "Otis и финской KONE."),
    },
    "g45a72968": {
        0: ("«Группа Моторика» приобрела 50,1% акционерного капитала АО «ГК Лимб», "
            "одного из заметных игроков российского рынка протезирования, сообщили "
            "Russian Business в компании."),
        1: ("Покупка позволит «Моторике» расширить присутствие в сегменте протезов "
            "нижних конечностей и усилить собственную сеть центров восстановления "
            "мобильности."),
    },
    "g6bf41023": {
        1: ("По словам одного из источников на фондовом рынке, сделка прошла "
            "недавно. «Алор» приобрел среднего брокера, название компании "
            "неизвестно. Второй источник пояснил, что покупка брокера поможет "
            "«Алору» заполучить новую депозитарную лицензию."),
    },
    "gb0f1f736": {
        1: ("В сентябре 2026 года «Альфа-Банк» объявил о приобретении платформы "
            "WhoIsBlogger (юрлицо - «Даблюайби»), специализирующейся на аналитике "
            "и подборе блогеров."),
    },
}

# Дословные ожидаемые ИСХОДНЫЕ тексты — правим, только если совпадает точно
# (иначе карточку с тех пор поправили другим путём — пропустить).
EXPECTED_OLD = {
    ("g3ecb7b86", 0): (
        "« ДОМ.РФ » приобрел лифтовый бизнес S8 Capital Об объекте сделки Группа "
        "« ДОМ.РФ » приобрела у S8 Capital лифтовый бизнес, включающий Meteor Lift "
        "и АО «Лифт Коннект» — бывшие российские активы американской Otis и "
        "финской KONE. Meteor Lift создан на базе…"
    ),
    ("g45a72968", 0): (
        "«Группа Моторика» приобрела 50,1% акционерного капитала АО «ГК Лимб», "
        "одного из заметных игроков российского рынка протезирования, сообщили "
        "Russian Business в компании. Три протезно-ортопедических центра «Лимба» "
        "в Москве, Санкт-Петербурге и Ростове-на-Дону…"
    ),
    ("g45a72968", 1): (
        "Покупка позволит «Моторике» расширить присутствие в сегменте протезов "
        "нижних конечностей и усилить собственную сеть центров восстановления "
        "мобильности. В частности, в продуктовую линейку группы должен войти "
        "гидравлический коленный модуль с микропроцессорным…"
    ),
    ("g6bf41023", 1): (
        "По словам одного из источников на фондовом рынке, сделка прошла недавно. "
        "«Алор» приобрел среднего брокера, название компании неизвестно. Второй "
        "источник пояснил, что покупка брокера поможет «Алору» заполучить новую "
        "депозитарную лицензию. «Алор» — одна из…"
    ),
    ("gb0f1f736", 1): (
        "В сентябре 2026 года «Альфа-Банк» объявил о приобретении платформы "
        "WhoIsBlogger (юрлицо - «Даблюайби»), специализирующейся на аналитике и "
        "подборе блогеров. Сделка была закрыта в рамках стратегии развития…"
    ),
}


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []
    applied = 0
    skipped = 0

    for cid, new_val in CLEAR_RATIONALE.items():
        card = cards.get(cid)
        if card is None:
            skipped += 1
            continue
        if (cid, "eco.rationale") in decided:
            log.append("%s: eco.rationale решено читателем — пропущено" % cid)
            skipped += 1
            continue
        cur = (card.get("eco") or {}).get("rationale")
        log.append("%s: eco.rationale очищено (дубль фактов, не мотив)" % cid)
        applied += 1
        if write:
            card.setdefault("eco", {})["rationale"] = new_val

    for cid, idx_map in TRIM_EVENTS.items():
        card = cards.get(cid)
        if card is None:
            skipped += 1
            continue
        events = card.get("events") or []
        for idx, new_note in idx_map.items():
            if idx >= len(events):
                log.append("%s: events[%d] отсутствует — пропущено" % (cid, idx))
                skipped += 1
                continue
            expected_old = EXPECTED_OLD.get((cid, idx))
            cur = events[idx].get("note")
            if expected_old is not None and cur != expected_old:
                log.append("%s: events[%d].note не совпадает с ожидаемым — пропущено" % (cid, idx))
                skipped += 1
                continue
            log.append("%s: events[%d].note обрезано до целого предложения" % (cid, idx))
            applied += 1
            if write:
                events[idx]["note"] = new_note

    print("Применено: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
