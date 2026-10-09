"""gcd8d2664 (ЗПИФ «Инвестпроф»/ТЦ «Сказка»): `eco.sum` нёс прозу на 200
знаков — цену и две именованные независимые оценки (NF Group,
Commonwealth Partnership). Короткое поле суммы, кто и как оценивал — в
«Оценке и дисконте» (`eco.val`), docs/card_money.md: «Пометка
недостоверности — только «(по оценке)», без имени оценщика... кто и как
оценивал — в eco.val». test_data.py::test_sum_and_share_fields_stay_short
поймал превышение потолка (27 вместо 26) при публикации решения
владельца (9 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"
OLD_SUM = (
    "Цена сделки не раскрывается. Независимые оценки рыночной стоимости "
    "объекта расходятся: Марина Малахатько (NF Group) — 1,7 млрд ₽ без "
    "НДС; в Commonwealth Partnership считают цену выше — 2,5–3,5 млрд ₽."
)
NEW_SUM = "Не раскрыта (по оценке)"
NEW_VAL = (
    "Независимые оценки рыночной стоимости объекта расходятся: Марина "
    "Малахатько (NF Group) — 1,7 млрд ₽ без НДС; в Commonwealth "
    "Partnership считают цену выше — 2,5–3,5 млрд ₽."
)


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "gcd8d2664":
            continue
        eco = d.get("eco", {})
        assert eco.get("sum") == OLD_SUM, "eco.sum уже другой: %r" % eco.get("sum")
        assert eco.get("val") == "—", "eco.val уже занят: %r" % eco.get("val")
        eco["sum"] = NEW_SUM
        eco["val"] = NEW_VAL
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
