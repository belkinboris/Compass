"""g87583786 (право на КРТ в Западном Бирюлеве): post_preview — снимок
поста, одобренный владельцем кнопкой до правки sum/eco.sum на заглавную
«Около» (fix_g87583786_sum_capital.py) — унёс старую строчную «около» в
«Начальная цена лота». Мехнический дефект формата, не решение владельца
о смысле текста; правится вслед за sum (12 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"
OLD = "<b>Начальная цена лота:</b> около 2,2 млрд ₽"
NEW = "<b>Начальная цена лота:</b> Около 2,2 млрд ₽"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g87583786":
            continue
        preview = d.get("post_preview") or ""
        assert OLD in preview, "старой строки больше нет в post_preview"
        d["post_preview"] = preview.replace(OLD, NEW)
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
