# -*- coding: utf-8 -*-
"""Слияние дубля: domodedovo-aukcion / g7cab373d — g7cab373d («Продажа 100%
долей аэропорта Домодедово») это ОБЪЯВЛЕНИЕ о старте торгов (13 января
2026, источник — объявление на Авито, статус «Обсуждается», без покупателя),
а domodedovo-aukcion — РЕЗУЛЬТАТ тех же торгов (29 января, покупатель —
Шереметьево, статус «Закрыта»). Найдено ночной вычиткой 40 карточек
(17-18 августа 2026); тот же класс, что уже описан в README/CLAUDE.md
принцип «переговоры и закрытие сделки объединяются в одну каноническую
карточку», просто для аукциона, а не для двусторонних переговоров.

Оставлена domodedovo-aukcion — она и есть каноническая карточка сделки:
стартовая цена (132,2 млрд ₽) там УЖЕ документирована в `eco.val`, продавец
(ПСБ/Росимущество) — в `eco.finadv`. Единственное, чего не хватало: точная
дата и основание судебного решения об изъятии актива в госсобственность,
которое domodedovo-aukcion называло короче. У g7cab373d была более точная
формулировка того же факта (дата, суд, юрлицо-ответчик, имя Каменщика) —
дополнена в `law.appr` (историческая запись FIXES партии 7,
pipeline/ingest/fixes/batch_deep_2026_r7.py, слита с новым значением по
уже устоявшемуся за эту ночь приёму «СЛИТО»).

Единственный источник g7cab373d — объявление на Авито (не редакционная
статья, ничего не подтверждает сверх уже известного) — не переносится.

Одна запись FIXES на дубль (pipeline/ingest/fixes/batch_d_n08.py) снята ДО
записи слияния.

Запуск:
    python3 pipeline/merge_domodedovo_announcement_dup.py            # сухой прогон
    python3 pipeline/merge_domodedovo_announcement_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "domodedovo-aukcion"
DROP = "g7cab373d"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("target") == drop.get("target") == "domodedovo", \
        "предмет разошёлся — это не тот дубль, что ожидали"

    precise_appr = ('В июне 2025 года первая инстанция (Арбитражный суд '
                     'Московской области, решение от 17 июня 2025 года) '
                     'удовлетворила требование Генпрокуратуры изъять в '
                     'доход государства 100% долей подконтрольного '
                     'предпринимателю Дмитрию Каменщику ООО «ДМЕ Холдинг», '
                     'с 2024 года владевшего активами аэропорта '
                     '«Домодедово». Апелляция и кассация оставили решение '
                     'без изменения.')
    assert keep["law"]["appr"] != precise_appr, "уже дописано"
    keep["law"]["appr"] = precise_appr

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: law.appr уточнён (дата суда, юрлицо, имя Каменщика)")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять запись FIXES на g7cab373d в "
              "pipeline/ingest/fixes/batch_d_n08.py и слить историческую "
              "запись domodedovo-aukcion.law.appr в batch_deep_2026_r7.py "
              "ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
