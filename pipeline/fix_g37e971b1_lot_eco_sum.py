"""g37e971b1 (ФСК/ТРК Mari): `eco.sum` стоял заглушкой «—», хотя `sum`
несёт стартовую цену лота («3,5 млрд ₽ (стартовая цена)») — у трёх других
карточек лотов (gbbc6c73e, gbcf07c78, g6d711306) `eco.sum` зеркалит `sum`
буквально. test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist
поймал расхождение при первом попадании карточки в базу (6 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g37e971b1":
            continue
        if d.get("eco", {}).get("sum") == "—" and d.get("sum"):
            d["eco"]["sum"] = d["sum"]
            changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
