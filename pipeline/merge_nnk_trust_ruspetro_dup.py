# -*- coding: utf-8 -*-
"""Слияние дубля: gf9ab3267 / gc80f7910 — одна и та же сделка (ННК купила
у банка «Траст» на аукционе нефтедобывающие структуры АО «Инга» и АО
«Транс-Ойл», бывшие активы Ruspetro, за 20 млрд ₽) под двумя id — найдено
ночной вычиткой 40 карточек (17-18 августа 2026).

Оставлена gf9ab3267 (добавлена раньше, у неё 8 источников против 4, и —
что важнее — ПРАВИЛЬНАЯ атрибуция президентского распоряжения: «Сделка
стала возможной после того, как в марте 2023 года президент Путин подписал
распоряжение о праве «Траста» выкупить 100% акций... В ХОДЕ БАНКРОТСТВА
ГРУППЫ RUSPETRO» — это распоряжение разрешало «Трасту» получить активы ОТ
Ruspetro, более ранний шаг цепочки собственности, а не согласовывало именно
продажу «Траста» -> ННК. У дубля (gc80f7910) та же цитата стояла в law.appr
БЕЗ этого уточнения и читалась как согласование сделки ННК — фактическая
ошибка атрибуции (родня уже записанного урока «Заголовок говорит об этой
сделке, текст — обо всей истории актива»).

При этом у дубля были структурные ссылки, которых не было у оставшейся
карточки:

- `buyer` -> g41bf9d28 (ННК) — у gf9ab3267 покупатель был только текстом
  (`buyer_name`), профиля не было; `buyer_name` снимается, чтобы не
  дублировать роль (правило проекта: профиль ИЛИ текст, не оба разом);
- `target` -> g0be4d8aa — ссылки на профиль предмета не было вовсе;
- `eco.share`: у дубля — важная структурная деталь (данные СБИС о том, что
  «Нефтегаз Югра» и ликвидированная «Инга» имеют один и тот же ИНН и
  адрес — то есть это буквально одно и то же юрлицо под новым именем),
  у оставшейся карточки поле было короче и этой детали не несло —
  дописано;
- источники дубля (1prime.ru, ura.news) — оба отсутствовали в списке
  оставшейся карточки, добавлены.

Десять записей FIXES на дубль (6 в pipeline/ingest/fixes/batch_c_2023.py,
1 в batch_c_rev05.py, 3 в batch_d_rev08.py) сняты ДО записи слияния —
включая ту самую запись с ошибочной атрибуцией law.appr, которую больше
некуда применять.

Запуск:
    python3 pipeline/merge_nnk_trust_ruspetro_dup.py            # сухой прогон
    python3 pipeline/merge_nnk_trust_ruspetro_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "gf9ab3267"
DROP = "gc80f7910"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("sum") == drop.get("sum") == "20 млрд ₽", \
        "сумма разошлась — это не тот дубль, что ожидали"

    assert keep.get("buyer") is None and keep.get("buyer_name") == "ННК", \
        "buyer/buyer_name уже другие — уже правили?"
    keep["buyer"] = "g41bf9d28"
    del keep["buyer_name"]

    assert keep.get("target") is None, "target уже заполнен — уже правили?"
    keep["target"] = "g0be4d8aa"

    share_add = ('«Максим Колпаков — генеральный директор „Транс-Ойл“ с '
                 'февраля 2024 года и „Нефтегаз Югра“ с 28 декабря 2023 '
                 'года. Учредитель ООО „Нефтегаз Югра“ — ООО „ННК-Ойл“ '
                 'является владельцем с 18 декабря 2023 года», — указано '
                 'в системе СБИС. У «Нефтегаз Югра» и ликвидированной '
                 'компании «Инга», проданной банком «Траст», полностью '
                 'совпадает ИНН и адрес регистрации.')
    assert share_add not in keep["eco"]["share"], "уже дописано"
    keep["eco"]["share"] = keep["eco"]["share"] + " " + share_add

    src_urls = {u for _, u in keep["src"]}
    new_sources = [
        ("ПРАЙМ", "https://1prime.ru/Stocks/20230322/840159272.html"),
        ("URA.RU", "https://ura.news/news/1052733442"),
    ]
    for name, url in new_sources:
        if url not in src_urls:
            keep["src"].append([name, url])

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: buyer, target, eco.share, src дополнены; buyer_name снят")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять 10 записей FIXES на gc80f7910 в трёх "
              "файлах pipeline/ingest/fixes/ (batch_c_2023.py, "
              "batch_c_rev05.py, batch_d_rev08.py) ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
