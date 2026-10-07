"""gafde5488 (Сбербанк/«НМ-Тех»): у покупателя не было профиля, только текст
`buyer_name` — `_party_detail()` в format_post.py падал на эвристику-запасной
вариант (первое предложение `eco.context`, упоминающее сторону) и подбирал
предложение про методику оценки суммы сделки, а не про саму структуру
(дефект данных, не шаблона — routines/publication.md, «Шаги 6, 7 и 12»,
6 октября 2026: пост gafde5488 уже уходил подписчикам с этой фразой по
ошибке). Заводит профиль «Интегральные системы» (проект «Объединённая
микроэлектронная компания», источник — CNews) — после этого `_party_detail`
берёт предложение из `desc`, а не из `eco.context`, и дефект не повторится
при следующей автоправке поста (поле `target_fin` обновилось — правка
стоит в очереди на этот же прогон)."""
import json
import sys

sys.path.insert(0, "pipeline/ingest")
import accept_card  # noqa: E402

PATH = "static/data/deals_promoted.json"


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    card = next(d for d in data["deals"] if d["id"] == "gafde5488")
    assert card.get("buyer") is None, "покупатель уже привязан к профилю"
    answer = {
        "id": "gafde5488",
        "profiles": [{
            "role": "buyer",
            "name": "«Интегральные системы»",
            "ind": "Холдинги",
            "desc": ("Структура Сбербанка для консолидации активов микроэлектронной "
                     "отрасли — проект «Объединённая микроэлектронная компания» (ОМК). "
                     "В январе и мае 2026 года купила 49,8% производителя микроэлектроники "
                     "«Элемент»."),
        }],
    }
    lines, _ = accept_card.apply_answer(answer, card, data)
    for line in lines:
        print(line)
    assert card.get("buyer"), "привязка покупателя не применилась"
    assert card.get("buyer_name") is None, "старый текст покупателя не снялся"
    json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
