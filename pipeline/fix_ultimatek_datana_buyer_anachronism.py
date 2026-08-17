# -*- coding: utf-8 -*-
"""ga1f2b443 (УльтимаТек/Датана и Датабриз, июль 2023) указывала покупателем
профиль `g8fdefffc` — «ООО «Экспанта» (ГК «Ультиматек»)». Это АНАХРОНИЗМ:
источник карточки (comnews.ru, июль 2023) называет покупателем только
«УльтимаТек»/«ГК «Ультиматек»» — слова «Экспанта» в статье нет вовсе,
проверено самостоятельно (fetch_article_texts.py, 17.08.2026, поиск
подстроки «Экспанта» в полном тексте — 0 совпадений).

TAdviser сообщал 11 декабря 2024 года, что ГК «Ультиматек» ТОЛЬКО ТОГДА
выделила бизнес продуктовой разработки в отдельную компанию «Экспанта»
(WebSearch, rusprofile.ru/tadviser.ru) — на 17 месяцев позже сделки с
Датаной и Датабризом. Профиль `g8fdefffc` верно используется как покупатель
у `g339dfcc8` (Экспанта/«Алгоритм1», январь 2026 — уже ПОСЛЕ выделения), но
не должен использоваться для сделки 2023 года, когда «Экспанты» как
инвестподразделения ещё не существовало.

Заведён отдельный профиль «ГК «Ультиматек»» (сама группа, как она названа в
источнике), `buyer` карточки ga1f2b443 переключен на него.

Запуск:
    python3 pipeline/fix_ultimatek_datana_buyer_anachronism.py            # сухой прогон
    python3 pipeline/fix_ultimatek_datana_buyer_anachronism.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
ID = "ga1f2b443"
OLD_BUYER = "g8fdefffc"
NEW_BUYER_ID = "gultimatekgroup01"

NEW_COMPANY = {
    "name": "ГК «Ультиматек»",
    "ind": "ИТ и интернет",
    "desc": ("Интегратор индустриальных цифровых решений; в 2024 году "
             "выделила инвестиционное подразделение «Экспанта» в отдельную "
             "компанию."),
    "kpi": ["Профиль", "Автоматический"],
}


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    d = by_id.get(ID)
    assert d is not None, f"{ID} не найдена"

    assert d["buyer"] == OLD_BUYER, "buyer уже другой — уже правили?"
    assert NEW_BUYER_ID not in base["companies"], "профиль уже существует"
    base["companies"][NEW_BUYER_ID] = dict(NEW_COMPANY)
    d["buyer"] = NEW_BUYER_ID

    print(f"{ID}: buyer -> новый профиль «ГК «Ультиматек»» ({NEW_BUYER_ID}), "
          f"снят анахронизм («Экспанта» появилась только в декабре 2024)")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
