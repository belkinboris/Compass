# -*- coding: utf-8 -*-
"""Удалить вручную подтверждённые дубли карточек и исправить роли сторон.

В отличие от ``data_audit.py`` этот скрипт содержит только просмотренные
редактором случаи. Старые адреса сохраняются в ``merged``.

Запуск:
    python3 pipeline/reconcile_duplicate_cards.py
    python3 pipeline/reconcile_duplicate_cards.py --write
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "static" / "data" / "deals_promoted.json"
CURATED = ROOT / "static" / "data" / "curated_deals.json"

FORALAB_ID = "g0b6a8c17"


def merge_sources(*groups):
    out, seen = [], set()
    for group in groups:
        for row in group or []:
            if not isinstance(row, list) or len(row) < 2 or not row[1] or row[1] in seen:
                continue
            seen.add(row[1])
            out.append(row)
    return out


def evidence(value, url, method="manual_source_review"):
    return [{"value": value, "method": method, "url": url}]


def apply(promoted: dict, curated: list[dict]) -> list[str]:
    changes: list[str] = []
    deals = promoted.get("deals") or []
    by_id = {d.get("id"): d for d in deals}
    curated_by_id = {d.get("id"): d for d in curated}

    # Профиль «ФораЛаб» отсутствовал, из-за чего «ЛабКвест» одновременно стоял
    # покупателем и предметом сделки.
    if FORALAB_ID not in promoted.setdefault("companies", {}):
        promoted["companies"][FORALAB_ID] = {
            "name": "ФораЛаб",
            "legal_name": "ООО «ФораЛаб»",
            "ind": "Здравоохранение",
            "desc": "Централизованная медицинская лаборатория в Санкт-Петербурге.",
            "kpi": ["Профиль", "Данные уточняются"],
        }
        promoted.setdefault("match_keys", {})[FORALAB_ID] = ["форалаб", "fora lab"]
        changes.append("создан профиль ФораЛаб")

    specs = [
        {
            "keep": "g676504a3", "drop": "gadce1d9c",
            "fields": {
                "date": "2026-05-19",
                "title": "KAMA FLOW подписала соглашение об инвестиции 500 млн ₽ в ROBO",
                "buyer": "g330b6e10", "target": "gd09d2e9d",
                "status": "Подписана", "type": "Инвестиция", "kind": "acquisition",
                "asset": "Платформа автономных роботов ROBO",
                "events": [{
                    "id": "signed-2026-05-19", "kind": "signed", "date": "2026-05-19",
                    "title": "Подписано инвестиционное соглашение",
                    "historicalTitle": "KAMA FLOW подписала соглашение об инвестиции 500 млн ₽ в ROBO",
                    "note": "Соглашение о раунде финансирования подписано на конференции ЦИПР. Размер доли инвестора не раскрывался.",
                    "facts": [["Инвестор", "KAMA FLOW"], ["Компания", "ROBO"], ["Сумма", "500 млн ₽"]],
                    "sources": [["Forbes", "https://www.forbes.ru/tekhnologii/561064-kama-flow-investiruet-500-mln-rublej-v-platformu-servisnoj-robototehniki-robo"]],
                }],
                "party_evidence": {
                    "buyer": evidence("KAMA FLOW", "https://www.forbes.ru/tekhnologii/561064-kama-flow-investiruet-500-mln-rublej-v-platformu-servisnoj-robototehniki-robo"),
                    "target": evidence("ROBO", "https://www.forbes.ru/tekhnologii/561064-kama-flow-investiruet-500-mln-rublej-v-platformu-servisnoj-robototehniki-robo"),
                },
            },
        },
        {
            "keep": "g40477661", "drop": "g68297df0",
            "fields": {
                "date": "2023-06-01",
                "title": "«ЛабКвест» приобрёл 90% «ФораЛаб» и её лабораторный комплекс в Санкт-Петербурге",
                "buyer": "g67ef3e91", "target": FORALAB_ID,
                "seller": "Александр и Рашида Марковы",
                "status": "Закрыта", "type": "M&A", "kind": "acquisition",
                "asset": "90% ООО «ФораЛаб» и централизованная лаборатория в Санкт-Петербурге",
                "events": [{
                    "id": "closed-2023-05", "kind": "closed", "date": "2023-05-01",
                    "title": "Сделка завершена",
                    "historicalTitle": "«ЛабКвест» приобрёл 90% «ФораЛаб»",
                    "note": "К маю 2023 года 90% ООО «ФораЛаб» перешли основателю «ЛабКвест» Дарье Пикалюк. Сделка включала готовый лабораторный комплекс.",
                    "facts": [["Покупатель", "ГК «ЛабКвест»"], ["Предмет", "90% ООО «ФораЛаб»"], ["Сумма", "50 млн ₽"]],
                    "sources": [["Vademecum", "https://vademec.ru/news/2023/06/01/labkvest-investirovala-50-mln-rubley-v-tsentralizovannuyu-laboratoriyu-v-sankt-peterburge/"]],
                }],
                "party_evidence": {
                    "buyer": evidence("ЛабКвест", "https://vademec.ru/news/2023/06/01/labkvest-investirovala-50-mln-rubley-v-tsentralizovannuyu-laboratoriyu-v-sankt-peterburge/"),
                    "target": evidence("ФораЛаб", "https://vademec.ru/news/2023/06/01/labkvest-investirovala-50-mln-rubley-v-tsentralizovannuyu-laboratoriyu-v-sankt-peterburge/"),
                    "seller": evidence("Александр и Рашида Марковы", "https://www.kommersant.ru/doc/6029977"),
                },
            },
        },
        {
            "keep": "g324faec6", "drop": "g8fe01e40",
            "fields": {
                "date": "2023-12-21",
                "title": "«Северсталь» приобрела «Венталл Стальные Решения» и производственные площадки в Обнинске и Щёкине",
                "buyer": "g4e2d0a88", "target": "gad05203e",
                "seller": "Холдинг «Венталл»",
                "status": "Закрыта", "type": "M&A", "kind": "acquisition",
                "asset": "100% «Венталл Стальные Решения» и две производственные площадки",
                "events": [{
                    "id": "closed-2023-12-21", "kind": "closed", "date": "2023-12-21",
                    "title": "Сделка завершена",
                    "historicalTitle": "«Северсталь» приобрела активы холдинга «Венталл»",
                    "note": "«Северсталь» стала владельцем «Венталл Стальные Решения» и площадок в Обнинске и Щёкине. О сделке публично сообщили в январе 2024 года.",
                    "facts": [["Покупатель", "«Северсталь»"], ["Предмет", "«Венталл Стальные Решения»"], ["Сумма", "4,7 млрд ₽"]],
                    "sources": [["Интерфакс", "https://www.interfax.ru/business/944209"], ["Ведомости", "https://www.vedomosti.ru/business/articles/2024/01/10/1014461-severstal-kupila-aktivi-ventall-po-vipusku-metallokonstruktsii"]],
                }],
                "party_evidence": {
                    "buyer": evidence("Северсталь", "https://www.interfax.ru/business/944209"),
                    "target": evidence("Венталл Стальные Решения", "https://www.vedomosti.ru/business/articles/2024/01/10/1014461-severstal-kupila-aktivi-ventall-po-vipusku-metallokonstruktsii"),
                    "seller": evidence("Холдинг Венталл", "https://www.vedomosti.ru/business/articles/2024/01/10/1014461-severstal-kupila-aktivi-ventall-po-vipusku-metallokonstruktsii"),
                },
            },
        },
    ]

    removed: set[str] = set()
    for spec in specs:
        keep, drop = spec["keep"], spec["drop"]
        card, legacy = by_id.get(keep), by_id.get(drop)
        if not card:
            continue
        before = copy.deepcopy(card)
        card.update(copy.deepcopy(spec["fields"]))
        card.pop("target_was_buyer", None)
        card["src"] = merge_sources(card.get("src"), legacy.get("src") if legacy else [])
        card["duplicate_reviewed"] = True
        if card != before:
            changes.append(f"исправлена карточка {keep}")
        if legacy:
            removed.add(drop)
            changes.append(f"удалён дубль {drop}")
        promoted.setdefault("merged", {})[drop] = keep

    # Уточняем профиль, который теперь используется как предмет сделки.
    ventall = promoted.get("companies", {}).get("gad05203e")
    if ventall and ventall.get("name") != "Венталл Стальные Решения":
        ventall["name"] = "Венталл Стальные Решения"
        ventall["legal_name"] = "ООО «Венталл Стальные Решения»"
        ventall["desc"] = "Производитель металлоконструкций с площадками в Обнинске и Щёкине."
        promoted.setdefault("match_keys", {})["gad05203e"] = ["венталл", "венталл стальные решения"]
        changes.append("уточнён профиль Венталл Стальные Решения")

    # Дубли кураторских карточек: оставляем более полную кураторскую запись.
    curated_duplicates = {
        "g0ca2ebf0": "baltika",
        "gb1f65e04": "hugoboss",
        "gb1866587": "berizaryad",
    }
    for drop, keep in curated_duplicates.items():
        legacy = by_id.get(drop)
        canonical = curated_by_id.get(keep)
        if not legacy or not canonical:
            continue
        canonical["src"] = merge_sources(canonical.get("src"), legacy.get("src"))
        removed.add(drop)
        promoted.setdefault("merged", {})[drop] = keep
        changes.append(f"удалён дубль кураторской карточки {drop} → {keep}")

    # Выкуп собственных акций: эмитент не должен одновременно быть target.
    buyback = by_id.get("g75837e8b")
    if buyback:
        before_buyback = copy.deepcopy(buyback)
        buyback.pop("target", None)
        buyback["asset"] = "До 25% собственных акций ЛУКОЙЛ у нерезидентов"
        buyback["seller"] = "Нерезиденты — владельцы акций"
        if buyback != before_buyback:
            changes.append("исправлены роли в карточке выкупа собственных акций ЛУКОЙЛ")

    # Две разные покупки долей 3S Group: не склеиваем, но исправляем даты и
    # связываем как последовательные транзакции.
    first, second = by_id.get("geda130b6"), by_id.get("gdd85a5b9")
    if first and second:
        before_first, before_second = copy.deepcopy(first), copy.deepcopy(second)
        first.update({
            "date": "2023-12-28",
            "title": "Артём Чайка приобрёл 49% основного юрлица 3S Group",
            "seller": "Руслан Сеюков",
            "related_deal_ids": ["gdd85a5b9"],
            "separate_transaction_reviewed": True,
        })
        second.update({
            "date": "2024-06-04",
            "title": "Артём Чайка приобрёл ещё 50% 3S Group у Руслана Сеюкова",
            "seller": "Руслан Сеюков",
            "related_deal_ids": ["geda130b6"],
            "separate_transaction_reviewed": True,
            "src": merge_sources(second.get("src"), [["Коммерсантъ", "https://www.kommersant.ru/doc/6712251"]]),
        })
        if first != before_first or second != before_second:
            changes.append("исправлены и связаны две последовательные сделки 3S Group")

    # Покупки 83,4% и 16,6% Тишинки — самостоятельные транши, а не этапы одной
    # карточки. Явная связь не даст будущему аудиту склеить их автоматически.
    a, b = by_id.get("g3875e8f5"), by_id.get("g4444b396")
    if a and b:
        before_a, before_b = copy.deepcopy(a), copy.deepcopy(b)
        a["related_deal_ids"] = sorted(set((a.get("related_deal_ids") or []) + ["g4444b396"]))
        b["related_deal_ids"] = sorted(set((b.get("related_deal_ids") or []) + ["g3875e8f5"]))
        a["separate_transaction_reviewed"] = True
        b["separate_transaction_reviewed"] = True
        if a != before_a or b != before_b:
            changes.append("покупки долей Тишинки отмечены как отдельные связанные транши")

    if removed:
        promoted["deals"] = [d for d in deals if d.get("id") not in removed]
    return changes


def main(write: bool) -> None:
    promoted = json.loads(PROMOTED.read_text(encoding="utf-8"))
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    changes = apply(promoted, curated)
    if not changes:
        print("Изменений нет.")
        return
    print("\n".join("- " + x for x in changes))
    if not write:
        print("Сухой прогон. Добавьте --write.")
        return
    PROMOTED.write_text(json.dumps(promoted, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CURATED.write_text(json.dumps(curated, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Записано.")


if __name__ == "__main__":
    main("--write" in sys.argv)
