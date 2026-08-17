# -*- coding: utf-8 -*-
"""Профиль компании g9690c72a («Опора Телеком» и «Дача на связи») — лот из
двух юрлиц, но не нёс признака `lot` — найдено ночной вычиткой 40 карточек
(17-18 августа 2026). Источник (kommersant.ru/doc/5748009) прямо описывает
их как ДВЕ отдельные компании с РАЗНЫМ составом собственников («Опора
Телеком» — Любомир Прокопенко 31,5% и АО «Сетьинвест» 68,5%; ООО
«Дачанасвязи» — «Сетьинвест» 50%, Ольга Путьмакова 41,5%, Татьяна Кочнова
8,75%), проданные ГК «Сервис-Телеком» одной сделкой. Тот же класс, что уже
описан в CLAUDE.md («Имя компании — не место для доли» / признак `lot`):
профиль без флага показывает читателю единую компанию там, где юрлиц два.

Продавца-ФИО в карточку НЕ добавляем: источник называет не одного продавца,
а пять совладельцев на два разных юрлица (уже перенесены дословно в
eco.context) — свести это к одному полю `seller` значило бы выбрать одно
имя произвольно, ровно то, чего лот и призван избегать.

Запуск:
    python3 pipeline/fix_servistelekom_target_lot_flag.py            # сухой прогон
    python3 pipeline/fix_servistelekom_target_lot_flag.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
COMPANY_ID = "g9690c72a"


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    company = base["companies"].get(COMPANY_ID)
    assert company is not None, f"компания {COMPANY_ID} не найдена"
    assert company["name"] == "«Опора Телеком» и «Дача на связи»", \
        "имя компании уже другое — уже правили?"
    assert "lot" not in company, "lot уже стоит — уже правили?"
    company["lot"] = True

    print(f"{COMPANY_ID}: добавлен признак lot (два юрлица одним профилем)")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
