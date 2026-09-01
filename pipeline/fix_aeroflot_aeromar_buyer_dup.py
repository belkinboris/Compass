"""Убирает дублирующее текстовое имя покупателя у карточки g2c27516d.

Что сломано: карточка «Аэрофлот»/«Аэромар» (2026-09-01) пришла из притока с
`buyer_name: "«Аэрофлот»"` (текстовое имя, записанное draft.py по методу
explicit_news_title) — а последующий шаг сопоставления/дочитывания ДОПОЛНИЛ
её ещё и `buyer: "gf3ed02a1"`, реальным профилем ПАО «Аэрофлот», не убрав
текстовое поле. `test_buyer_is_named_once` (test_data.py) как раз и проверяет,
что заполнено ровно одно из двух: у покупателя либо профиль, либо имя текстом,
никогда оба сразу — иначе на экране и в выжимке может показаться разное имя,
если профиль когда-нибудь переименуют.

Почему чинится удалением `buyer_name`, а не `buyer`: профиль `gf3ed02a1`
(«ПАО «Аэрофлот»») существует, верно называет ту же компанию и уже связан —
именно профиль, а не текст, предпочтителен, когда он есть (текстовая форма
вводилась для инвестраундов, где профилей у фондов почти нет).

Запуск: без аргументов — сухой прогон; `--write` — запись.
"""
import json
import sys

PATH = "static/data/deals_promoted.json"


def main():
    write = "--write" in sys.argv
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)

    deals = data["deals"]
    deal = deals["g2c27516d"] if isinstance(deals, dict) else next(
        d for d in deals if d["id"] == "g2c27516d"
    )

    assert deal.get("buyer") == "gf3ed02a1", "профиль покупателя изменился — проверьте карточку заново"
    assert deal.get("buyer_name") == "«Аэрофлот»", "текстовое имя изменилось — проверьте карточку заново"

    print("До:", {"buyer": deal.get("buyer"), "buyer_name": deal.get("buyer_name")})

    if write:
        del deal["buyer_name"]
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Записано: buyer_name удалено, buyer остался", deal["buyer"])
    else:
        print("Сухой прогон — ничего не записано. Для записи: --write")


if __name__ == "__main__":
    main()
