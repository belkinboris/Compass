"""g51fa80ce («Голдрупп», аукцион на участок россыпного золота): два
механических дефекта, пойманных pytest при публикации решения владельца
(8 октября 2026).

1. `ind` стоял как «Металлургия и добыча» — такой строки нет в списке
   `INDUSTRIES` на сайте (канонично — «ГМК и добыча»,
   test_data.py::test_industries_are_from_the_known_list). Текст поста
   (`post_override`/`post_preview`) — решение владельца, его не трогаю;
   `ind` — структурное поле для фильтра на сайте, поправил на канон.
2. `eco.sum` стоял заглушкой «—», хотя `sum` несёт итоговый платёж аукциона
   («213,5 млн ₽») — тот же класс, что у g37e971b1, ge1b2eba1 и g955d2c6b:
   `eco.sum` зеркалит `sum` буквально.
   test_audit_queue.py::test_the_sum_on_the_overview_is_the_sum_in_the_economist
"""
import json

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    changed = 0
    for d in data["deals"]:
        if d["id"] != "g51fa80ce":
            continue
        if d.get("ind") == "Металлургия и добыча":
            d["ind"] = "ГМК и добыча"
            changed += 1
        if d.get("eco", {}).get("sum") == "—" and d.get("sum"):
            d["eco"]["sum"] = d["sum"]
            changed += 1
    assert changed == 2, f"ожидали поправить 2 поля, поправили {changed}"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"поправлено полей: {changed}")


if __name__ == "__main__":
    main()
