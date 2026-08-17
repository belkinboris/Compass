# -*- coding: utf-8 -*-
"""Три карточки об ОДНОЙ и ТОЙ ЖЕ сделке — продаже бывшего офиса банка
«Открытие» (БЦ Vivaldi Plaza, Летниковская ул., 24,4 тыс. кв. м, у
Павелецкого вокзала) — стояли раздельно: `gmru-vtb-otkrytie-office-rwb`
(mergers.ru, 04.08.2026, покупатель «RWB»), `gd126ba45` (Коммерсантъ,
07.08.2026, покупатель «Wildberries») и `g8e2e28d5` (TAdviser, тот же день,
тот же покупатель). Партия REVISION_BRIEF 16 августа уже отметила в
комментарии FIXES это подозрение и намеренно НЕ внесла факт («в статье
встретился абзац про покупку RWB... повторный WebFetch не дал уверенно
подтвердить, что RWB это тот же покупатель, что и в заголовке») — вопрос
оставался открытым.

Прочитано заново (17-18 августа 2026, data/inbox/raw, fetch_article_texts.py):
сама карточка `gmru-vtb-otkrytie-office-rwb` уже несла точный ответ в своём
же `buyer_name` — «объединённая компания Wildberries и Russ (RWB)» — RWB не
альтернативный покупатель, а ОФИЦИАЛЬНОЕ название той же группы. Статья
Коммерсанта (07.08.2026, доказывающая закрытие сделки со слов самого ВТБ)
это подтверждает: «Весной РБК писал, что RWB ведет переговоры с ВТБ о
покупке этого актива. Но в самом RWB настаивали, что речь идет только о
возможной аренде объекта» — то есть RWB (= Wildberries & Russ) весной
ОТРИЦАЛА покупку, к августу сделка подтверждена. Не два покупателя, а одна
группа, чьё сообщение изменилось со временем.

Оставлена `gmru-vtb-otkrytie-office-rwb` — самая содержательная из трёх:
`eco.val` называет ДВЕ независимые экспертные оценки поимённо (IBC Real
Estate, Ricci), `eco.fin` — финансовые показатели покупателя, `eco.context`
— предысторию объекта. `gd126ba45` и `g8e2e28d5` дублируют её беднее
(структурные поля почти пустые); единственное, чего в оставшейся карточке
не было, — официальное подтверждение ВТБ агентству «Ъ» с точной датой
закрытия (07.08, не 04.08) — перенесено в `eco.context` и добавлено вторым
событием в `events`. `sum`/`eco.sum` расширены до объединённого диапазона
обеих оценок (7,7–13,5 млрд ₽), как и указывает сам Коммерсантъ. TAdviser
добавлен третьим источником.

Три записи `FIXES`, ссылавшиеся на `gd126ba45`, сняты вместе с карточкой
(см. урок CLAUDE.md «Слияние дублей обязано снять правки к удалённой
карточке вместе с ней») — grep по `pipeline/ingest/fixes/*.py` на оба
дропаемых id выполнен перед записью.

Запуск:
    python3 pipeline/merge_vtb_otkrytie_office_rwb_wildberries_dup.py            # сухой прогон
    python3 pipeline/merge_vtb_otkrytie_office_rwb_wildberries_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "gmru-vtb-otkrytie-office-rwb"
DROP = ["gd126ba45", "g8e2e28d5"]

OLD_TITLE = "RWB купила бывший офис банка «Открытие» у ВТБ"
NEW_TITLE = "Wildberries и Russ (RWB) выкупили офис «Открытия» у ВТБ"

OLD_DATE = "2026-08-04"
NEW_DATE = "2026-08-07"

OLD_SUM = "11–13,5 млрд ₽ (по оценке)"
NEW_SUM = "7,7–13,5 млрд ₽ (по оценке)"

OLD_CONTEXT = ("До интеграции «Открытия» в группу ВТБ здесь находился "
               "головной офис банка. После завершения сделки по покупке "
               "«Открытия» объект перешел под контроль ВТБ.")
NEW_CONTEXT = (OLD_CONTEXT + " Весной РБК писал, что RWB ведет переговоры "
               "с ВТБ о покупке этого актива, но в самой RWB тогда "
               "настаивали, что речь идет только о возможной аренде "
               "объекта. 7 августа в ВТБ подтвердили «Ъ», что дочерний "
               "БМ-банк завершил сделку по продаже.")

NEW_EVENT = {
    "kind": "closed",
    "date": "2026-08-07",
    "title": "Сделка завершена",
    "note": ("В ВТБ сообщили «Ъ», что дочерний БМ-банк завершил сделку по "
             "продаже бывшего офиса ФК «Открытие». Объект сделки — "
             "бизнес-центр площадью 24,4 тыс. кв. м на Летниковской улице "
             "возле Павелецкого вокзала в центре Москвы."),
    "source": ["Коммерсантъ", "https://www.kommersant.ru/doc/8864446"],
}

NEW_SOURCES = [
    ["Коммерсантъ", "https://www.kommersant.ru/doc/8864446"],
    ["TAdviser", "https://www.tadviser.ru/a/57663"],
]


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id[KEEP]
    for drop_id in DROP:
        assert drop_id in by_id, f"{drop_id} не найдена — уже слита?"

    assert keep["title"] == OLD_TITLE, "title уже другой — уже правили?"
    keep["title"] = NEW_TITLE

    assert keep["date"] == OLD_DATE, "date уже другая — уже правили?"
    keep["date"] = NEW_DATE

    assert keep["sum"] == OLD_SUM, "sum уже другой — уже правили?"
    keep["sum"] = NEW_SUM
    assert keep["eco"]["sum"] == OLD_SUM, "eco.sum уже другой — уже правили?"
    keep["eco"]["sum"] = NEW_SUM

    assert keep["eco"]["context"] == OLD_CONTEXT, \
        "eco.context уже другой — уже правили?"
    keep["eco"]["context"] = NEW_CONTEXT

    assert len(keep["events"]) == 1, "events уже не одно — уже правили?"
    keep["events"].append(NEW_EVENT)

    for src in NEW_SOURCES:
        if not any(s[1] == src[1] for s in keep["src"]):
            keep["src"].append(src)

    base["deals"] = [d for d in base["deals"] if d["id"] not in DROP]
    for drop_id in DROP:
        base.setdefault("merged", {})[drop_id] = KEEP

    print(f"Оставлена {KEEP}: title, date, sum/eco.sum, eco.context "
          f"обновлены; добавлено событие 07.08 и 2 источника.")
    print(f"Удалены и перенаправлены: {DROP}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
