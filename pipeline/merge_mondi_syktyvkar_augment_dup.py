# -*- coding: utf-8 -*-
"""Слияние дубля: g5c0f70c6 / g4e5d24db — одна и та же несостоявшаяся сделка
(Mondi объявила о продаже «Монди Сыктывкарский ЛПК» структуре Виктора
Харитонина, Augment Investments, 12 августа 2022; сделка сорвалась, о выходе
объявлено 5 июня 2023) под двумя id — найдено ночной вычиткой 40 карточек
(17-18 августа 2026, группа «Проверить экономиста и юриста на дословность и
логику», аналог партий REVISION_BRIEF).

Оставлена g5c0f70c6 (добавлена раньше, богаче источниками, и `extra` уже
рассказывает всю сагу целиком — включая последующую сделку с «Сезар Инвест»,
которой посвящена другая карточка). У неё не было ссылки на профиль
покупателя вовсе (`buyer: null`) — хотя провалившаяся сделка всё равно имеет
сторону.

Перенесено из дубля:

- `buyer` -> slhgroup... нет, `g0b9343f2` (Augment Investments Limited) —
  ссылки на покупателя не было вовсе;
- `ind`: «ГМК и добыча» -> «Лесопром» — предмет сделки (`gd2b0b67e`,
  целлюлозно-бумажный комбинат) уже размечен «Лесопром» в родственной
  карточке того же актива (ge9d2a3e6, продажа «Сезар Инвест»); та же правка
  уже стояла в FIXES для дубля;
- `eco.target_fin`: у дубля были финансы актива за 2022 год (78 млрд ₽
  выручки), у оставшейся — только за 2021 (в евро) — не повтор, дописано
  второй строкой;
- `eco.context`: у дубля — факт о параллельной покупке Харитониным другого
  актива в той же отрасли (пермский «Кама», февраль 2023) — не повтор
  контекста оставшейся карточки (про сотрудников и теплоснабжение), дописано;
- источник дубля (interfax.ru/amp/904837) — другой материал того же
  издания, не дублирует уже стоящую ссылку interfax.ru/business/921255.

Четыре записи FIXES на дубль (в pipeline/ingest/fixes/batch_c_2023.py) сняты
ДО записи слияния.

Запуск:
    python3 pipeline/merge_mondi_syktyvkar_augment_dup.py            # сухой прогон
    python3 pipeline/merge_mondi_syktyvkar_augment_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "g5c0f70c6"
DROP = "g4e5d24db"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("target") == drop.get("target") == "gd2b0b67e", \
        "предмет разошёлся — это не тот дубль, что ожидали"

    assert keep.get("buyer") is None, "buyer уже заполнен — уже правили?"
    keep["buyer"] = "g0b9343f2"

    assert keep.get("ind") == "ГМК и добыча", "ind уже другая — уже правили?"
    keep["ind"] = "Лесопром"

    target_fin_add = ('По итогам 2022 года "Монди Сыктывкарский ЛПК" '
                       'получила выручку в размере 78 млрд рублей (рост на '
                       '9% г/г), чистую прибыль - 22,5 млрд рублей (рост на '
                       '18% г/г)')
    assert target_fin_add not in keep["eco"]["target_fin"], "уже дописано"
    keep["eco"]["target_fin"] = keep["eco"]["target_fin"] + " " + target_fin_add

    context_add = ('У бизнесмена уже есть активы в этой сфере: в феврале '
                   '2023 года зарегистрированная в Калининграде '
                   'международная компания (МКООО) «Огмент Инвестментс '
                   'Лимитед» стала владельцем 100% уставного капитала ООО '
                   '«Кама», пермского производителя мелованного картона и '
                   'бумаги. Ориентировочная сумма сделки — 14 млрд рублей.')
    assert context_add not in keep["eco"]["context"], "уже дописано"
    keep["eco"]["context"] = keep["eco"]["context"] + " " + context_add

    src_urls = {u for _, u in keep["src"]}
    new_source = ("Интерфакс", "https://www.interfax.ru/amp/904837")
    if new_source[1] not in src_urls:
        keep["src"].append(list(new_source))

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: buyer, ind, eco.target_fin, eco.context, src дополнены")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять 4 записи FIXES на g4e5d24db в "
              "pipeline/ingest/fixes/batch_c_2023.py ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
