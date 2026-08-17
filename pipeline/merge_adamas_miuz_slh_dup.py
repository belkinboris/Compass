# -*- coding: utf-8 -*-
"""Слияние дубля: gcdec4f24 / adamas-slh — одна и та же продажа сети
«Адамас», найдено по тому же скриншоту ленты, что и слияние Сайберус/
F.A.C.C.T. (17 августа 2026). Обе карточки называют один день закрытия
(26-28 января 2026), одного продавца (Михаил Несветайло / связанное с ним
АО «Форум Капитал»), тот же предмет (профиль `adamas`) и одну и ту же
оценку (Юрий Левицкий, BGP Capital: сеть 4-5 млрд + завод 1,2-1,5 млрд =
до 6,5 млрд).

Собственный текст оставляемой карточки (`law.struct`, `eco.rationale`)
прямо называет РЕАЛЬНОГО покупателя — не MIUZ Diamonds, а SLH Group
(гонконгская структура, созданная сыном Льва Леваева именно для того,
чтобы ОТДЕЛИТЬ актив от MIUZ Diamonds: «создание специальной новой
структуры, SLH Group, отделяет активы «Адамаса» от MIUZ Diamonds, что
может снизить потенциальные риски для бизнеса семьи Леваевых»). Заголовок
«MIUZ Diamonds может приобрести…» и ссылка `buyer` на профиль MIUZ Diamonds
(g9b8c7f5a) — оба следствие раннего слуха (декабрь 2025, до закрытия),
который сама же карточка цитирует и опровергает в своём тексте. Это не
стилистическая правка (которую CLAUDE.md запрещает для старых карточек),
а фактическая: плашка сторон называла не ту компанию, хотя текст карточки
уже содержал верное имя, — родня уже записанного урока про испорченную
ссылку `seller_id` у ВТБ/«Открытие»/RWB.

Правки в оставляемой карточке:

- `buyer`: g9b8c7f5a (MIUZ Diamonds) -> slhgroup (SLH Group Limited) —
  сама карточка называет SLH Group реальным покупателем;
- `title`: снят прогноз «может приобрести» с именем перекупщика, чьё имя
  сама карточка опровергает; принят точный заголовок дубля (закрытая
  сделка, верный покупатель) — он уже прошёл всю ту же проверку фактов;
- `law.struct`: дописана деталь дубля — юрлицо продавца (АО «Форум
  Капитал») и зарубежные «дочки» предмета (Киргизия, Казахстан), которых
  не было у оставшейся карточки.

Единственный источник дубля — общий телеграм-агрегатор (@dealsma),
уже не добавляет ничего к четырём именным источникам оставшейся карточки
(Ъ ×2, Sostav, «Компания») — не переносится.

Две записи FIXES на adamas-slh (пpaртия 7 REVISION_BRIEF) сняты в
pipeline/ingest/fixes/batch_deep_2026_r7.py ДО записи слияния.

Запуск:
    python3 pipeline/merge_adamas_miuz_slh_dup.py            # сухой прогон
    python3 pipeline/merge_adamas_miuz_slh_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "gcdec4f24"
DROP = "adamas-slh"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("target") == drop.get("target") == "adamas", \
        "предмет разошёлся — это не тот дубль, что ожидали"

    assert keep["buyer"] == "g9b8c7f5a", "buyer уже не MIUZ Diamonds — уже правили?"
    keep["buyer"] = "slhgroup"

    assert keep["title"] == "MIUZ Diamonds может приобрести ювелирную сеть «Адамас»", \
        "заголовок уже другой — уже правили?"
    keep["title"] = "Гонконгская SLH Group Limited приобрела ювелирное производство и сеть «Адамас»"

    addition = ("Продавец — АО «Форум Капитал» (связано с М. Несветайло и "
                "партнёрами); в периметр сделки входит ООО «АДАМАС АЙПИ» с "
                "дочерними компаниями в России, Киргизии и Казахстане.")
    assert addition not in keep["law"]["struct"], "уже дописано"
    keep["law"]["struct"] = keep["law"]["struct"] + " " + addition

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: buyer -> slhgroup, title исправлен, law.struct дополнен")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять 2 записи FIXES на adamas-slh в "
              "pipeline/ingest/fixes/batch_deep_2026_r7.py ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
