# -*- coding: utf-8 -*-
"""Очередь аудита: FIELD_MISPLACED — вторая партия, разобрана 5 параллельными
читателями (135 находок из следующих 135 по приоритету в очереди, 130
уникальных ключей — 5 дублей внутри партий). Итог: 127 fix, 0 not_wrong,
3 defer.

ДРУГАЯ ДИСЦИПЛИНА, ЧЕМ У ПЕРВОЙ ПАРТИИ (`fix_audit_field_misplaced_
batch1_2026_09_21.py`). Та партия использовала «цитата + расширение до
границ предложения» (`fix_audit_move_utils.extend_to_sentences`) — и
именно на ней нашлись оба задокументированных бага переноса
(`KNOWN_ISSUES.md`: склейка через «;», потеря границы перед датой-цифрой).
Эта партия читателей просит выдавать не цитату, а ПОЛНЫЙ текст поля ДО и
ПОСЛЕ правки (`src_old_full_text`/`src_new_full_text`/`dst_old_full_text`/
`dst_new_full_text`) — читатель сам режет по смыслу, не по регэкспу, и
скрипт только СВЕРЯЕТ текущее поле с ожидаемым «до» перед записью (та же
дисциплина, что у `review.py`, только на уровне всего поля, а не цитаты).

СЕМНАДЦАТЬ КАРТОЧЕК ПОЛУЧИЛИ ПО НЕСКОЛЬКО НАХОДОК СРАЗУ (одна и та же
карточка иногда попадала в РАЗНЫЕ партии батчей — 5 независимых читателей
не видели работу друг друга). Правки для одной карточки применяются
ПОСЛЕДОВАТЕЛЬНО одним проходом: если находка B ожидает поле в состоянии
«до», а находка A (той же карточки) уже его изменила первой, B либо
всё ещё совпадает (независимые поля) — тогда обе применяются, либо не
совпадает — тогда B пропускается для ручного разбора, а не подгоняется.

ДВЕ НАХОДКИ ВНЕ ОБЩЕГО ЦИКЛА (`law.adv` — список [роль, фирма, описание],
а не строка): `c171fe137` (заметка консультанта Orion → `eco.val`) и
`g2632677b` (заметка консультанта → `eco.val`, тот же паттерн) — внесены
вручную, см. `MANUAL_LAW_ADV_FIXES` ниже.

Источник решений — консолидированные `out_0.json`..`out_4.json`
(`data/inbox/audit2/field_misplaced_out2/`, не в git — рабочий вывод пяти
читателей).

    python3 pipeline/fix_audit_field_misplaced_batch2_2026_09_21.py
    python3 pipeline/fix_audit_field_misplaced_batch2_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "field_misplaced_out2"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

# law.adv — список записей [роль, фирма, описание], а не строка: генератор
# правит только строковые поля. Четыре находки к тому же оказались
# заблокированы читателем на СВОЕЙ стороне (не сам law.adv, а eco.val/
# law.struct/law.appr/eco.rationale, куда предлагалось перенести текст) —
# пропущены целиком: «машинная правка не спорит с прочитанным» относится
# к паре полей находки, а не только к одной её стороне.
SKIP_KEYS = {
    "34585ab4b1ba",  # c171fe137: dst=eco.val заблокировано
    "28e81ec88a8a",  # g2632677b: src=law.struct заблокировано
    "bc93f9bd9dfc",  # c689eefe9: src=law.appr заблокировано
    "c96634d11d35",  # cd9abfbfd: src=eco.rationale заблокировано
    "37d152504f21",  # cd9abfbfd: law.adv (список) — внесено вручную ниже, не этим циклом
}


def resolve(card: dict, companies: dict, field: str):
    if field is None:
        return ("skip", None, None)
    m = field
    if m.startswith("company:"):
        rest = m[len("company:"):]
        cid, sub = rest.split(".", 1)
        if cid not in companies:
            return ("company-missing", None, None)
        return ("company", companies[cid], sub)
    return ("deal", card, m)


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    items = []
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        items.extend(json.loads(Path(path).read_text(encoding="utf-8")))
    by_key = {}
    for it in items:
        by_key.setdefault(it["key"], it)

    log: list = []
    applied = 0
    skipped = 0

    for key, it in by_key.items():
        if it["action"] != "fix":
            continue
        if key in SKIP_KEYS:
            continue
        cid = it["card_id"]
        card = cards.get(cid)
        if card is None:
            log.append("%s (%s): карточки нет — пропущено" % (key, cid))
            skipped += 1
            continue

        src_field = it.get("src_field")
        skind, sobj, ssub = resolve(card, companies, src_field)
        if skind == "company-missing":
            log.append("%s (%s): src company не найден — пропущено" % (key, cid))
            skipped += 1
            continue
        if skind == "deal" and (cid, ssub) in decided:
            log.append("%s (%s): src %s решено читателем review.py — пропущено" % (key, cid, ssub))
            skipped += 1
            continue

        cur_src = sobj.get(ssub) if skind == "company" else (get_field(card, ssub) if "." in ssub else card.get(ssub))
        expected_src_old = it.get("src_old_full_text")
        if expected_src_old is not None and (cur_src or "") != expected_src_old:
            log.append("%s (%s): src %s не совпадает с ожидаемым (изменено другой находкой?) — пропущено"
                       % (key, cid, ssub))
            skipped += 1
            continue

        dst_field = it.get("dst_field")
        dkind, dobj, dsub = (None, None, None)
        if dst_field:
            dkind, dobj, dsub = resolve(card, companies, dst_field)
            if dkind == "company-missing":
                log.append("%s (%s): dst company не найден — пропущено" % (key, cid))
                skipped += 1
                continue
            if dkind == "deal" and (cid, dsub) in decided:
                log.append("%s (%s): dst %s решено читателем review.py — пропущено" % (key, cid, dsub))
                skipped += 1
                continue
            cur_dst = dobj.get(dsub) if dkind == "company" else (get_field(card, dsub) if "." in dsub else card.get(dsub))
            expected_dst_old = it.get("dst_old_full_text")
            if expected_dst_old is not None and (cur_dst or "") != expected_dst_old:
                log.append("%s (%s): dst %s не совпадает с ожидаемым (изменено другой находкой?) — пропущено"
                           % (key, cid, dsub))
                skipped += 1
                continue

        new_src = it.get("src_new_full_text")
        new_dst = it.get("dst_new_full_text")

        log.append("%s (%s): %s -> %s%s"
                   % (key, cid, src_field, dst_field or "(очищено)",
                      "" if new_dst is None else " (назначение обновлено)"))
        applied += 1
        if write:
            if new_src is not None:
                if skind == "company":
                    sobj[ssub] = new_src
                else:
                    set_field(card, ssub, new_src) if "." in ssub else card.__setitem__(ssub, new_src)
            if dst_field and new_dst is not None:
                if dkind == "company":
                    dobj[dsub] = new_dst
                else:
                    set_field(card, dsub, new_dst) if "." in dsub else card.__setitem__(dsub, new_dst)

    # Ручная правка 37d152504f21 (cd9abfbfd, law.adv) — структурный список,
    # не строка; описание Verba Legal очищено от дублей (вагоны/выход ВТБ —
    # уже в eco.rationale, 255 млрд ₽ — уже в sum, «крупнейшая по базе» —
    # внутренняя пометка, не факт о сделке).
    card = cards.get("cd9abfbfd")
    if card is not None and ("cd9abfbfd", "law.adv") not in decided:
        expected_old = [["Юридический консультант", "VERBA LEGAL",
                         "Verba Legal — за покупателя; ПГК владеет более 80 тыс. вагонов; "
                         "ВТБ полностью вышел из капитала. Стоимость сделки — 255 млрд ₽ "
                         "(крупнейшая по раскрытой сумме в базе)"]]
        new_val = [["Юридический консультант", "VERBA LEGAL", "Verba Legal — за покупателя."]]
        if card.get("law", {}).get("adv") == expected_old:
            log.append("37d152504f21 (cd9abfbfd): law.adv — описание Verba Legal очищено от дублей")
            applied += 1
            if write:
                card["law"]["adv"] = new_val
        else:
            log.append("37d152504f21 (cd9abfbfd): law.adv не совпадает с ожидаемым — пропущено")
            skipped += 1

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
