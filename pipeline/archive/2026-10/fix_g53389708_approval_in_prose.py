"""g53389708 (Уралбиофарм): `eco.context` называет факт согласования
(«Росимущество согласовало параметры продажи пакета ближе к концу
сентября 2026 года»), а `law.appr` стоял заглушкой «—» — на соседних
вкладках сайта это выглядело бы как «факт есть» и «согласований не
было» одновременно. test_data.py::test_approval_is_not_left_in_prose
поймал при публикации решения владельца (9 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"
NEW_APPR = "Росимущество согласовало параметры продажи пакета (конец сентября 2026 года)."


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g53389708":
            continue
        assert d["law"]["appr"] == "—", "law.appr уже занят: %r" % d["law"]["appr"]
        d["law"]["appr"] = NEW_APPR
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
