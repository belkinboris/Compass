"""g5850b57f («Яндекс»/VK, объединение корпоративных ИТ-направлений):
`sum` стоял как «—», а не «Не раскрыта» — единственная такая карточка в
базе (486 других правильно несут «Не раскрыта», docs/card_money.md:
«цена, которую стороны не раскрывают — „Не раскрыта", а не „—" и не
пусто»). «—» в `sum` сбивал
test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist
— тест читает любой `sum`, кроме «» и «Не раскрыта», как раскрытую цену
и требует её же в `eco.sum`, а здесь нет цифры для зеркалирования: сделка
без заявленной суммы вовсе. Правка — не мирить `eco.sum`, а привести
`sum` к канону (8 октября 2026)."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g5850b57f":
            continue
        assert d.get("sum") == "—", "sum уже другой: %r" % d.get("sum")
        d["sum"] = "Не раскрыта"
        changed += 1
    assert changed == 1, f"ожидали поправить 1 карточку, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено карточек: {changed}")


if __name__ == "__main__":
    main()
