# -*- coding: utf-8 -*-
"""Правки следом за `fix_known_issues_2026_09_11_batch_new_cards.py`,
найденные полным прогоном pytest.

1. Три новые карточки несли дату «год-месяц» без дня (ЛСР/«Геометрия» —
   «2026-08», «Союз-ТТМ»/«Союз-М» — «2026-03», Сохацкий/Мамут — «2023-04») —
   `test_dates_are_parseable` требует `YYYY-MM-DD|YYYY|unknown`. Тот же
   класс, что уже описан в CLAUDE.md («поле date несёт ТОЛЬКО год, а месяц
   остаётся текстом») — день неизвестен ни одному источнику, значит в
   `date` остаётся год, а месяц уже назван текстом в собственных полях
   карточки (eco.share/title), ничего не теряется.

2. `g7a3a83d1` («Севергрупп» купила «Кордиант» у S8 Capital, заведена этим
   же прогоном) оказалась ДУБЛЕМ уже существующей, гораздо более полной
   карточки `g4a751f95` (та же сделка, тот же id профилей buyer/seller,
   проверена и вычитана ещё в августе — `deep_researched`/
   `followup_researched`/`proofread`) — обнаружено `test_no_company_twins`
   на профиле-дубле «ГК «Кордиант»» (`gkordiant2024`) против уже
   существовавшего «Cordiant» (`gb52f53eb`, target у g4a751f95). Скрипт
   `fix_add_severgroup_kordiant_card.py`, из которого родилась g7a3a83d1,
   был написан раньше, чем появилась g4a751f95, и не мог знать о ней —
   его собственные assert проверяли только СВОИ id, не совпадение по
   предмету. Дубль снимается, профиль-дубль удаляется, адрес
   перенаправляется в `merged`.

Запуск: сухой прогон без аргументов, запись — `--write`.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "static" / "data" / "deals_promoted.json"


def main(write=False):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    deals = {d["id"]: d for d in data["deals"]}
    comps = data["companies"]
    changes = []

    # 1. Даты год-месяц -> только год
    fixes = [
        ("gb2bed44c", "2026-08", "2026"),
        ("gb0d1c79e", "2026-03", "2026"),
        ("g76fb4663", "2023-04", "2023"),
    ]
    for cid, old, new in fixes:
        d = deals[cid]
        assert d["date"] == old, "%s: дата уже другая" % cid
        d["date"] = new
        changes.append("%s: date %s -> %s (день неизвестен, месяц — в тексте карточки)" % (cid, old, new))

    # 2. Дубль g7a3a83d1 / gkordiant2024 -> g4a751f95 / gb52f53eb
    assert "g7a3a83d1" in deals, "g7a3a83d1 не найдена"
    assert deals["g7a3a83d1"]["target"] == "gkordiant2024"
    assert "g4a751f95" in deals, "g4a751f95 (оставшаяся карточка) не найдена"
    assert comps.get("gb52f53eb", {}).get("name") == "Cordiant"
    data["deals"] = [d for d in data["deals"] if d["id"] != "g7a3a83d1"]
    del comps["gkordiant2024"]
    data.setdefault("merged", {})["g7a3a83d1"] = "g4a751f95"
    changes.append("g7a3a83d1 снята как дубль g4a751f95 (та же сделка "
                    "Севергрупп/Кордиант, уже полно описана и вычитана "
                    "в августе); профиль-дубль gkordiant2024 удалён")

    print("\n".join(changes))
    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Записано.")
    else:
        print("Сухой прогон. --write для записи.")


if __name__ == "__main__":
    main("--write" in sys.argv)
