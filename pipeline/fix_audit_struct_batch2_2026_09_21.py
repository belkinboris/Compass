# -*- coding: utf-8 -*-
"""«Как устроена сделка» (law.struct) несёт историю торгов, опровержения,
чужую биографию и условия сделки — вторая партия по law.struct (аудит
13 сентября, первая партия — `fix_audit_struct_context_2026_09_20.py`).
Из 18 находок, свободных от чтения по источнику, 9 упираются в занятое
назначение (eco.context/eco.share/eco.val/law.terms/law.appr решены
читателем — почти все это ровно те 4 карточки из первой партии, что уже
были заблокированы тогда). Ещё одна (`gfcfba8c9`) не тронута: текст поля
с 13 сентября успел разойтись с цитатой аудита сильнее, чем сверкой можно
доверять без перечитывания источника. `gefb52584` тоже не тронута:
перенос требует правки ПРОФИЛЯ покупателя (companies), а не только
карточки сделки — вне механизма `decided_by_a_reader()`, нужна отдельная
проверка.

Здесь — оставшиеся 7: 4 через apply_move (перенос до границ предложения),
одна в обратную сторону (eco.context→law.struct), одна — точный частичный
перенос (цитата аудита не совпадает с границей предложения, взят кусок по
факту), и одна чистая — удаление дубля.

    python3 pipeline/fix_audit_struct_batch2_2026_09_21.py
    python3 pipeline/fix_audit_struct_batch2_2026_09_21.py --write
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
    # (id, поле-источник, цитата, поле-назначение)
    ("g79f683bc", "law.struct",
     "«Фонбет» опроверг информацию о покупке бизнес-центра «Stone "
     "Курская» в центре Москвы: по словам Голованова, компания "
     "занимается только букмекерской деятельностью, никогда не "
     "рассматривала инвестиции в коммерческую недвижимость или иной род "
     "занятий, а её текущий офис полностью отвечает её потребностям. "
     "В Stone заявили, что переговоры ведутся с группой частных "
     "инвесторов; участие «Фонбета» в сделке там не подтвердили.",
     "eco.context"),
    ("geb8edd5c", "law.struct",
     "Конечный бенефициар холдинга «Империя» — Андрей Фоменко. По "
     "данным Wikipedia, в 2001 году холдинг открыл в Санкт-Петербурге "
     "первый бизнес-центр «Сенатор», а к 2015 году сеть бизнес-центров "
     "«Сенатор» насчитывала 26 объектов общей площадью 310 000 "
     "квадратных метров.",
     "eco.context"),
    ("gca6c1eff", "law.struct",
     "В январе 2025 года выяснилось, что часть расчёта прошла не "
     "деньгами: 5% долей в структуре Unitile ООО «Плитэксперт» стали "
     "частью сделки по продаже бизнеса Quadro Decor, заключённой осенью "
     "2024 года. Продавец, Proxima Capital Group, получил встречную "
     "долю в самом Unitile Holding.",
     "eco.fin"),
    ("g930db872", "law.struct",
     "Соглашение предусматривает опцион на обратный выкуп доли прежними "
     "владельцами.",
     "law.terms"),
    # обратное направление: контекст → механика.
    ("g139d522a", "eco.context",
     "ВЭБ.РФ вошла в капитал на паритетных началах, 50 на 50, с Фондом "
     "«Сколково».",
     "law.struct"),
]

# gbf6f6432: цитата аудита — только доля владения ПОСЛЕ сделки, без
# сопутствующего факта о переименовании юрлица (он остаётся в law.struct,
# это законная механика).
POLEKS_ID = "gbf6f6432"
POLEKS_FULL_SENTENCE = ("ООО «Полекс Урал» переименовано в ООО «Пегас»: "
                        "15% принадлежит «Строме» Михаила Беккера и Вагана "
                        "Храняна, 85% — инвестиционному товариществу.")
POLEKS_KEEP_IN_STRUCT = "ООО «Полекс Урал» переименовано в ООО «Пегас»:"
POLEKS_MOVE_TO_SHARE = ("15% принадлежит «Строме» Михаила Беккера и Вагана "
                        "Храняна, 85% — инвестиционному товариществу.")

# g57b3b93c: CMS как юрконсультант — чистый дубль уже подробной записи в
# law.adv (роль, цитата на немецком, источник), удаляется без переноса.
CMS_ID = "g57b3b93c"
CMS_OLD = "CMS консультировала MM Packaging по всем юридическим вопросам на протяжении всей сделки."


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    log: list = []

    for cid, src, quote, dst in MOVES:
        card = cards[cid]
        apply_move(card, src, quote, dst, write, decided, cid, log)

    poleks = cards[POLEKS_ID]
    cur = get_field(poleks, "law.struct") or ""
    if POLEKS_FULL_SENTENCE not in cur:
        log.append("%s: цитата не найдена дословно — пропущено" % POLEKS_ID)
    elif (POLEKS_ID, "law.struct") in decided or (POLEKS_ID, "eco.share") in decided:
        log.append("%s: law.struct или eco.share решены читателем — пропущено" % POLEKS_ID)
    else:
        share = get_field(poleks, "eco.share") or ""
        new_share = POLEKS_MOVE_TO_SHARE if not share or share in ("—", "-") \
            else share + " " + POLEKS_MOVE_TO_SHARE
        new_struct = cur.replace(POLEKS_FULL_SENTENCE, POLEKS_KEEP_IN_STRUCT).strip()
        log.append("%s: law.struct → eco.share (доля 15%%/85%%, факт о переименовании остаётся)" % POLEKS_ID)
        if write:
            set_field(poleks, "eco.share", new_share)
            set_field(poleks, "law.struct", new_struct)

    cms = cards[CMS_ID]
    cur_struct = get_field(cms, "law.struct")
    if cur_struct != CMS_OLD:
        log.append("%s: law.struct не совпало — пропущено" % CMS_ID)
    elif (CMS_ID, "law.struct") in decided:
        log.append("%s: law.struct решено читателем — пропущено" % CMS_ID)
    else:
        log.append("%s: law.struct удалён (дубль law.adv)" % CMS_ID)
        if write:
            set_field(cms, "law.struct", "—")

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
