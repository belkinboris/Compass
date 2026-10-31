"""g87583786 (право на КРТ в Западном Бирюлеве): sum и eco.sum начинались
со строчной «около» — test_sums_start_with_a_capital_letter_and_do_not_hedge
поймал при публикации (12 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g87583786":
            continue
        assert d["sum"] == "около 2,2 млрд ₽", "sum уже другой: %r" % d["sum"]
        assert d["eco"]["sum"] == "около 2,2 млрд ₽", "eco.sum уже другой: %r" % d["eco"]["sum"]
        d["sum"] = "Около 2,2 млрд ₽"
        d["eco"]["sum"] = "Около 2,2 млрд ₽"
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
