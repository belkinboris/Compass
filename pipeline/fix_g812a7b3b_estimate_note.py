"""g812a7b3b (Arzamas Capital/NGR Softlab): sum/eco.sum несли «(оценка
аналитика)» вместо единообразной пометки «(по оценке)» — test_data.py::
test_estimate_note_is_short поймал это при первом попадании карточки в базу
(молчание 24 ч, 30 сентября 2026). Значение суммы не меняется, меняется
только формулировка пометки на принятую конвенцию."""
import json

PATH = "static/data/deals_promoted.json"
OLD = "≈800 млн ₽ (оценка аналитика)"
NEW = "≈800 млн ₽ (по оценке)"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g812a7b3b":
            continue
        if d.get("sum") == OLD:
            d["sum"] = NEW
            changed += 1
        if d.get("eco", {}).get("sum") == OLD:
            d["eco"]["sum"] = NEW
            changed += 1
    assert changed == 2, f"ожидали поправить 2 поля, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено полей: {changed}")


if __name__ == "__main__":
    main()
