"""ge1b2eba1 (Москва/Рижский рынок, лот): `eco.sum` стоял заглушкой «—»,
хотя `sum` несёт стартовую цену лота («155,4 млн ₽ (стартовая цена)») — та
же карточка лота, что уже встречалась у g37e971b1 и других: `eco.sum`
зеркалит `sum` буквально. test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist
поймал расхождение при первом попадании карточки в базу (7 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "ge1b2eba1":
            continue
        if d.get("eco", {}).get("sum") == "—" and d.get("sum"):
            d["eco"]["sum"] = d["sum"]
            changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
