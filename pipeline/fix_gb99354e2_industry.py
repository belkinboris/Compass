"""gb99354e2 (аукцион автосалонов в ХМАО): ind стояло «Авто» — такой
метки нет в INDUSTRIES на сайте (там «Автопром»), test_industries_are_
from_the_known_list поймал при публикации (10 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "gb99354e2":
            continue
        assert d["ind"] == "Авто", "ind уже не «Авто»: %r" % d["ind"]
        d["ind"] = "Автопром"
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
