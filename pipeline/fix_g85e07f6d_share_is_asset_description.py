"""g85e07f6d («Дом.РФ»/ЦНТИ в Челябинске): `eco.share` нёс не долю в
сделке, а физическое описание помещения (площадь, этажи, кадастровый
номер) — не та величина для этого поля
(docs/card_money.md#Коротко и без механики: доля до 160 знаков, этот
текст — 225). Содержательно это фон про актив, тот же класс, что уже
лежит в `eco.context` этой карточки (история здания) — переношу туда,
`eco.share` — заглушка. test_data.py::test_sum_and_share_fields_stay_short
поймал при публикации решения владельца (8 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"
SHARE_TEXT = (
    "На торги выставлена недвижимость площадью 2488 квадратных метров "
    "в здании в форме буквы «П» на улице Труда, 157. Помещения "
    "расположены на трёх этажах, а также на цокольном и техническом, "
    "объединены единым кадастровым номером."
)


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g85e07f6d":
            continue
        eco = d.get("eco", {})
        assert eco.get("share") == SHARE_TEXT, "eco.share уже другой: %r" % eco.get("share")
        eco["context"] = eco["context"] + " " + SHARE_TEXT
        eco["share"] = "—"
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
