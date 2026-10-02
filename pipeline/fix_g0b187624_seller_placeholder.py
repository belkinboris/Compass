"""g0b187624 (Северсталь/«Дмитровский металлоцентр»): поле `seller` несло
literal-строку «Не раскрыт» вместо пустого значения — единственная такая
карточка (остальные 3 карточки с нераскрытым продавцом используют `None`).
test_data.py::test_seller_is_not_a_placeholder поймал это при первом
попадании карточки в базу (молчание 24 ч, 2 октября 2026): «Продавец: не
раскрыт» — это пустое поле, а не имя стороны, отображение пометки —
дело рендера, не данных. `seller_src` уже `None` — не трогаю."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g0b187624":
            continue
        if d.get("seller") == "Не раскрыт":
            d["seller"] = None
            changed += 1
    assert changed == 1, f"ожидали поправить 1 поле, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено полей: {changed}")


if __name__ == "__main__":
    main()
