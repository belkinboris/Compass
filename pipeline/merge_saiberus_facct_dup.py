# -*- coding: utf-8 -*-
"""Слияние дубля: g4feb42fc / c19d1104d — одна и та же сделка (фонд «Сайберус»
приобрёл активы F.A.C.C.T. для новой ИБ-компании) под двумя id, найдено по
жалобе владельца (скриншот ленты сделок, 17 августа 2026): обе карточки
называют одного и того же покупателя (компания g5fccf12e — «Сайберус»),
цитируют слово в слово ту же оценку («Softline Venture Partners и Kama Flow
оценивают в 5 млрд руб.»), тех же юридических консультантов (Better Chance /
Никольская Консалтинг), а `law.struct` дубля прямо называет дату закрытия
именно этой сделки — «закрыта 31 января 2025 г.», которая совпадает с планом
«завершение в I квартале 2025 года» у оставшейся карточки.

Оставлена g4feb42fc (добавлена в базу раньше, богаче источниками и разбором).
В неё перенесено то, чего там не было:

- `seller` — «Акционеры группы F.A.C.C.T.» (у дубля был назван прямо в
  рэнкинге «Ъ — Сделки года», у оставшейся стороны продавца не было вовсе);
- `eco.rationale` — цель сделки (ключа не было в словаре eco вовсе);
- `law.struct` — дата закрытия сделки (была прочерком);
- `eco.context` дубля — про фонд «Сайберус» (покупатель): у оставшейся
  карточки контекст был про F.A.C.C.T. (продавца), это не повтор, а вторая
  половина факта — дописана второй строкой;
- третий консультант в `law.adv` — Seven Hills Legal, по интеллектуальной
  собственности (у оставшейся были только Better Chance и «Никольская
  Консалтинг»);
- два источника дубля, которых не было у оставшейся: Ъ — «Сделки года»
  (kommersant.ru/doc/8077927) и Ведомости от 17.02.2025 о закрытии сделки.

Восемь записей `FIXES` в трёх файлах `pipeline/ingest/fixes/`, ссылавшихся на
удаляемую карточку, сняты ДО записи слияния (grep по всем `fixes/*.py` —
обязательный шаг, см. уже записанный урок про Ростелеком/«Рабочие Руки»).

Запуск:
    python3 pipeline/merge_saiberus_facct_dup.py            # сухой прогон
    python3 pipeline/merge_saiberus_facct_dup.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
KEEP = "g4feb42fc"
DROP = "c19d1104d"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    keep = by_id.get(KEEP)
    drop = by_id.get(DROP)
    assert keep is not None, f"{KEEP} не найдена — уже слито?"
    assert drop is not None, f"{DROP} не найдена — уже слито?"
    assert keep.get("buyer") == drop.get("buyer") == "g5fccf12e", \
        "покупатель разошёлся — это не тот дубль, что ожидали"

    assert keep.get("seller") is None, "seller уже заполнен — уже правили?"
    keep["seller"] = "Акционеры группы F.A.C.C.T."

    assert "rationale" not in keep["eco"], "eco.rationale уже есть — уже правили?"
    keep["eco"]["rationale"] = (
        "Консультирование фонда «Сайберус» в связи c приобретением до 100% "
        "разработчика в сфере кибербезопасности F.A.C.C.T. для создания "
        "новой ИБ-компании. Инвесторы формируют ИБ-компанию нового "
        "поколения, которая будет образована на базе активов, технологий и "
        "кадров F.A.C.C.T. Новая компания сфокусируется на разработке новой "
        "линейки технологий предотвращения и расследования "
        "киберпреступлений, в том числе путем внедрения решений и сервисов, "
        "приобретаемых у группы F.A.C.C.T."
    )

    assert keep["law"]["struct"] == "—", "law.struct уже заполнен — уже правили?"
    keep["law"]["struct"] = "Представитель F6 уточнил, что сделка была закрыта 31 января 2025 г."

    # eco.context дубля — про ФОНД «Сайберус» (покупатель), у оставшейся
    # карточки eco.context — про F.A.C.C.T. (продавца/предмет): разные
    # факты об одной сделке, не повтор, дописываем второй строкой.
    fund_context = (
        "Фонд «Сайберус» инвестирует в решения в сфере ИБ. Он создан в "
        "2022 г. основным владельцем Positive Technologies Юрием "
        "Максимовым. Фондом владеют участники рынка (государство, "
        "корпорации, граждане), указано на его сайте."
    )
    assert fund_context not in keep["eco"]["context"], "уже дописано"
    keep["eco"]["context"] = keep["eco"]["context"] + " " + fund_context

    adv_names = {a[1] for a in keep["law"]["adv"]}
    assert "Seven Hills Legal" not in adv_names, "Seven Hills Legal уже в списке"
    keep["law"]["adv"].append([
        "Консультант по интеллектуальной собственности",
        "Seven Hills Legal",
        "«Никольская Консалтинг» — за продавца, Better Chance — за "
        "покупателя, Seven Hills Legal — консультант по интеллектуальной "
        "собственности; до 100% активов. Источник: рэнкинг «Ъ — Сделки года».",
    ])

    src_urls = {u for _, u in keep["src"]}
    new_sources = [
        ("Коммерсантъ — «Сделки года»", "https://www.kommersant.ru/doc/8077927"),
        ("Ведомости", "https://www.vedomosti.ru/technology/articles/2025/02/17/1092702-saiberus-zakril-group-ib"),
    ]
    for name, url in new_sources:
        if url not in src_urls:
            keep["src"].append([name, url])

    base["deals"] = [d for d in base["deals"] if d["id"] != DROP]
    base.setdefault("merged", {})[DROP] = KEEP

    print(f"{KEEP}: seller, eco.rationale, law.struct, law.adv (+1), "
          f"src (+{len([n for n,u in new_sources if u not in src_urls])}) дополнены")
    print(f"{DROP}: удалена, merged[{DROP!r}] = {KEEP!r}")
    print(f"Карточек было: {len(by_id)}, станет: {len(base['deals'])}")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")
        print("НЕ ЗАБУДЬТЕ: снять 8 записей FIXES на c19d1104d в трёх файлах "
              "pipeline/ingest/fixes/ (batch_agents100_r2.py, "
              "batch_digest_r1_auto.py, batch_a_2025.py) ДО --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
