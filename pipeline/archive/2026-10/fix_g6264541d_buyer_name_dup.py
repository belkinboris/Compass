"""g6264541d (Шишкарев/«Дело»): карточка несла и профиль покупателя (`buyer`
= g4f522aee, «Сергей Шишкарев»), и то же имя текстом в `buyer_name` — та же
сторона дважды, разными путями записи. test_data.py::test_buyer_is_named_once
поймал это при первом попадании карточки в базу (решение владельца в
консоли, 7 октября 2026). Снимаю текстовый дубль — профиль уже называет
сторону."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g6264541d":
            continue
        if d.get("buyer") and d.get("buyer_name") == "Сергей Шишкарев":
            del d["buyer_name"]
            changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
