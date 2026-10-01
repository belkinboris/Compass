"""g1e37f107 (Fonte Capital сократил долю в «Самолете»): верхнеуровневое
`sum` несло «—» вместо принятой пометки «Не раскрыта» — единственная такая
карточка в базе (остальные 480 используют «Не раскрыта», 194 — пустую
строку). test_audit_queue.py::
test_the_sum_on_the_overview_is_the_sum_in_the_economist поймал это при
первом попадании карточки в базу (молчание 24 ч, 1 октября 2026) как
расхождение между «Обзором» и «Экономистом» — хотя сумма действительно не
раскрыта в обоих местах, просто верхний уровень использовал не ту
пометку. `eco.sum` уже несёт «—», это штатное пустое состояние для этого
поля — не трогаю."""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g1e37f107":
            continue
        if d.get("sum") == "—":
            d["sum"] = "Не раскрыта"
            changed += 1
    assert changed == 1, f"ожидали поправить 1 поле, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено полей: {changed}")


if __name__ == "__main__":
    main()
