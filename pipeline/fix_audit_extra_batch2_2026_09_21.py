# -*- coding: utf-8 -*-
"""«Дополнительная информация» (extra) — вторая партия (первая —
`fix_audit_extra_batch_2026_09_20.py`). При первом проходе 6 карточек
были ошибочно сочтены заблокированными занятым назначением — перепроверка
показала, что (id, поле) в `decided_by_a_reader()` не совпадали с тем,
что действительно проверялось (проверялась не та пара поле/карточка);
5 из них свободны по обеим сторонам и разбираются здесь. Двум карточкам
(`g1fc3fe9e`, `gca198c27`) нужен не перенос предложения целиком, а
разбор — в одном предложении смешаны факт не по адресу и законное
содержимое той же цитаты.

    python3 pipeline/fix_audit_extra_batch2_2026_09_21.py
    python3 pipeline/fix_audit_extra_batch2_2026_09_21.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import apply_move, get_field, set_field  # noqa: E402

MOVES = [
    ("gcef5a371",
     "В июле 2026 года VK продала уже 100% этого актива генеральному "
     "директору ООО «Много приложений» Дмитрию Панкрушеву; к 2025 году "
     "выручка компании выросла до 1,4 млрд ₽, сумма продажи не раскрыта. "
     "Сам red_mad_robot продолжает работать самостоятельно и развивает "
     "направление искусственного интеллекта — в январе 2026 года он "
     "создал совместное предприятие с «Билайном».",
     "eco.context"),
    ("g8a8ae3f7",
     "По неофициальным данным, смена совладельцев могла быть частью "
     "реструктуризации бизнеса, а не рыночной сделкой.",
     "law.struct"),
    ("gf5101b05",
     "ООО «ПАРОК» (теплоизоляция из каменной ваты, выручка 2020 — 1,9 "
     "млрд ₽) и АО «ОС СТЕКЛОВОЛОКНО» (около 40% российского рынка "
     "стекловолокна, выручка 2020 — 4,2 млрд ₽)",
     "eco.target_fin"),
]

# g1fc3fe9e: "финансировал её ПСБ" — факт о форме расчётов внутри
# предложения, не отвечающего целиком за это (остальное — про саму
# сделку). Разбито на два предложения по тем же фактам.
FIN_ID = "g1fc3fe9e"
FIN_OLD = "Завершённая сделка по продаже 100% акционерного капитала «Сибантрацита»; финансировал её ПСБ."
FIN_KEEP_EXTRA = "Завершённая сделка по продаже 100% акционерного капитала «Сибантрацита»."
FIN_MOVE = "Сделку финансировал ПСБ."

# gca198c27: мотив покупателя смешан в одном предложении со списком
# юрлиц группы (в состав группы входят...) — разбито на два.
RAT_ID = "gca198c27"
RAT_OLD = ("Цель приобретения — ускорить собственную цифровизацию "
           "Росатома и консолидировать ИТ-компетенции без внешних "
           "подрядчиков; в состав группы входят 15 юридических лиц, "
           "включая «Р.Тех», «Философия.ИТ», «Тектус.ИТ» и «Инлексис».")
RAT_MOVE = ("Цель приобретения — ускорить собственную цифровизацию "
            "Росатома и консолидировать ИТ-компетенции без внешних "
            "подрядчиков.")
RAT_KEEP_EXTRA = ("В состав группы входят 15 юридических лиц, включая "
                  "«Р.Тех», «Философия.ИТ», «Тектус.ИТ» и «Инлексис».")


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, quote, dst in MOVES:
        card = cards[cid]
        apply_move(card, "extra", quote, dst, write, decided, cid, log)

    fin = cards[FIN_ID]
    extra = get_field(fin, "extra") or ""
    if FIN_OLD not in extra:
        log.append("%s: цитата не найдена дословно — пропущено" % FIN_ID)
    elif (FIN_ID, "extra") in decided or (FIN_ID, "eco.fin") in decided:
        log.append("%s: extra или eco.fin решены читателем — пропущено" % FIN_ID)
    else:
        eco_fin = get_field(fin, "eco.fin") or ""
        new_fin = FIN_MOVE if not eco_fin or eco_fin in ("—", "-") else eco_fin + " " + FIN_MOVE
        new_extra = extra.replace(FIN_OLD, FIN_KEEP_EXTRA)
        log.append("%s: extra → eco.fin («Сделку финансировал ПСБ»)" % FIN_ID)
        if write:
            set_field(fin, "eco.fin", new_fin)
            set_field(fin, "extra", new_extra)

    rat = cards[RAT_ID]
    extra = get_field(rat, "extra") or ""
    if RAT_OLD not in extra:
        log.append("%s: цитата не найдена дословно — пропущено" % RAT_ID)
    elif (RAT_ID, "extra") in decided or (RAT_ID, "eco.rationale") in decided:
        log.append("%s: extra или eco.rationale решены читателем — пропущено" % RAT_ID)
    else:
        rationale = get_field(rat, "eco.rationale") or ""
        new_rationale = RAT_MOVE if not rationale or rationale in ("—", "-") else rationale + " " + RAT_MOVE
        new_extra = extra.replace(RAT_OLD, RAT_KEEP_EXTRA)
        log.append("%s: extra → eco.rationale (мотив цифровизации)" % RAT_ID)
        if write:
            set_field(rat, "eco.rationale", new_rationale)
            set_field(rat, "extra", new_extra)

    print("Записей: %d" % len(log))
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
