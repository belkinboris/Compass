# -*- coding: utf-8 -*-
"""Слияние дубля: g076a2f4e / c299076c8 — одна и та же продажа девелоперских
проектов ГК «Жилкапинвест» группе GloraX (2 июня 2025) под двумя id: обе
карточки цитируют дословно два общих источника (level-legal.com, glorax.com)
и совпадают по дате, покупателю и продавцу. Найдено ночной вычиткой 40
карточек (17-18 августа 2026).

Оставлена g076a2f4e (структурные ссылки на покупателя и продавца уже стоят
профилями — `buyer`/`seller_id`, у дубля стороны только текстом; источников
больше; согласование ФАС сформулировано конкретнее — «пять застройщиков в
Приморском крае»).

Перенесено из дубля то, чего в оставшейся карточке не было вовсе:

- `eco.context`: у дубля продавец назван поимённо — «Коробов Д. В.,
  Румянцев Н. Н.» (конечные бенефициары «Жилкапинвест» из рэнкинга «Ъ —
  Сделки года») — у оставшейся карточки этого нет ни в одном поле, только
  групповое название через `seller_id`;
- `eco.sum`/`sum`: у оставшейся — честный прочерк «Не раскрыта», у дубля —
  атрибутированная оценка «возможная сумма сделки — 3 млрд руб.» из того
  же рэнкинга «Ъ» — не факт, а рыночная оценка, поэтому с пометкой
  «(по оценке)»;
- источник дубля kommersant.ru/doc/8077927 («Сделки года») и
  interfax.ru/business/1029088 — оба отсутствовали в списке оставшейся
  карточки, добавлены.

Три записи FIXES на дубль (pipeline/ingest/fixes/batch_a_2025.py,
batch_chatgpt_deep_2025_b.py, batch_digest_r1_B100_auto.py — восемь
отдельных записей суммарно) сняты ДО записи слияния.

Запуск:
    python3 pipeline/merge_glorax_zhilkapinvest_dup.py            # сухой прогон
    python3 pipeline/merge_glorax_zhilkapinvest_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "g076a2f4e"
DROP = "c299076c8"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("date") == drop.get("date") == "2025-06-02", \
        "дата разошлась — это не тот дубль, что ожидали"

    context_add = ('Конечные бенефициары продавца — Коробов Д. В. и '
                   'Румянцев Н. Н.')
    assert keep["eco"]["context"] == "—", "eco.context уже заполнен — уже правили?"
    keep["eco"]["context"] = context_add

    assert keep["eco"]["sum"] == "Не раскрыта" and keep["sum"] == "Не раскрыта", \
        "sum уже другой — уже правили?"
    est = "3 млрд ₽ (по оценке)"
    keep["eco"]["sum"] = est
    keep["sum"] = est

    src_urls = {u for _, u in keep["src"]}
    new_sources = [
        ("Коммерсантъ — «Сделки года»", "https://www.kommersant.ru/doc/8077927"),
        ("Interfax", "https://www.interfax.ru/business/1029088"),
    ]
    for name, url in new_sources:
        if url not in src_urls:
            keep["src"].append([name, url])

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: eco.context, sum/eco.sum, src дополнены")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять записи FIXES на c299076c8 в трёх "
              "файлах pipeline/ingest/fixes/ (batch_a_2025.py, "
              "batch_chatgpt_deep_2025_b.py, batch_digest_r1_B100_auto.py) "
              "ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
