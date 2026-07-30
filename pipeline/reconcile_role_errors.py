# -*- coding: utf-8 -*-
"""Исправить вручную подтверждённые ошибки ролей сторон.

Автоматические правила могут предлагать кандидатов, но не должны менять уже
заполненные роли. Здесь перечислены только карточки, в которых заголовок и
первичные публикации однозначно показывают, что профиль попал не в ту колонку
или был потерян. Скрипт повторно запускаем и сохраняет ``party_evidence``.

Запуск:
    python3 pipeline/reconcile_role_errors.py
    python3 pipeline/reconcile_role_errors.py --write
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"


def evidence(value: str, url: str, note: str = "manual_source_review") -> list[dict]:
    return [{"value": value, "method": note, "url": url}]


def profile_id(name: str) -> str:
    return "g" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:9]


def ensure_profile(payload: dict, *, name: str, industry: str, aliases: list[str], desc: str) -> str:
    cid = profile_id(name)
    companies = payload.setdefault("companies", {})
    if cid not in companies:
        companies[cid] = {
            "name": name,
            "ind": industry,
            "desc": desc,
            "kpi": ["Профиль", "Редакционно подтверждён"],
        }
    keys = payload.setdefault("match_keys", {}).setdefault(cid, [])
    for alias in aliases:
        if alias not in keys:
            keys.append(alias)
    return cid


def apply(payload: dict) -> list[str]:
    changes: list[str] = []
    by_id = {d.get("id"): d for d in payload.get("deals", [])}

    hotel = ensure_profile(
        payload,
        name="Courtyard by Marriott Kazan Kremlin",
        industry="Гостиницы и туризм",
        aliases=["courtyard by marriott kazan kremlin", "courtyard kazan", "marriott kazan kremlin"],
        desc="Гостиница в центре Казани; в карточке профиля собраны сделки с самим объектом.",
    )
    vtorium = ensure_profile(
        payload,
        name="Вториум",
        industry="Финтех",
        aliases=["вториум", "vtorium"],
        desc="Финтех-сервис расчётов на рынке вторичного сырья.",
    )
    chzmk = ensure_profile(
        payload,
        name="Челябинский завод металлоконструкций (ЧЗМК)",
        industry="Металлургия",
        aliases=["челябинский завод металлоконструкций", "чзмк"],
        desc="Производитель строительных металлоконструкций в Челябинске.",
    )

    # card id -> fields and role evidence. Values are supported by the URLs in
    # the cards and were checked separately before inclusion in this migration.
    fixes = {
        "g90363dc7": {
            "fields": {"target": "g04181f17", "asset": "49% ООО «Полиматика Рус»"},
            "evidence": {"target": ("ООО «Полиматика Рус»", "https://www.interfax.ru/business/1067736")},
        },
        "g8bc7aacf": {
            "fields": {"target": "ge788d903", "asset": "100% ООО «Энгельс Электроинструменты»"},
            "evidence": {"target": ("ООО «Энгельс Электроинструменты»", "https://www.comnews.ru/content/244038/2026-03-02/2026-w10/1010/engels-elektroinstrumenty-voshel-sostav-aktivov-kholdinga-e1-grupp")},
        },
        "g55ac5f34": {
            "fields": {
                "target": "g9d2e4c88",
                "title": "RBE Group приобрела по 51% в ООО «ЕСК Системс» и ООО «Евростройконсалт»",
                "asset": "По 51% ООО «ЕСК Системс» и ООО «Евростройконсалт»",
            },
            "evidence": {"target": ("ГК «Евростройконсалт»", "https://www.kommersant.ru/doc/8480191")},
        },
        "g171f9461": {
            "fields": {"buyer": "gcafc31dc", "target": hotel, "asset": "Отель Courtyard by Marriott Kazan Kremlin"},
            "evidence": {
                "buyer": ("Группа ВТБ", "https://www.business-gazeta.ru/article/396973"),
                "target": ("Courtyard by Marriott Kazan Kremlin", "https://www.business-gazeta.ru/article/396973"),
            },
        },
        "gc2a1693a": {
            "fields": {"buyer": "gcafc31dc", "seller": "Банк России"},
            "evidence": {
                "buyer": ("ВТБ", "https://forbes-ru.turbopages.org/turbo/forbes.ru/s/finansy/483122-cb-soobsil-o-zakrytii-sdelki-po-prodaze-banka-otkrytie-vtb"),
                "seller": ("Банк России", "https://forbes-ru.turbopages.org/turbo/forbes.ru/s/finansy/483122-cb-soobsil-o-zakrytii-sdelki-po-prodaze-banka-otkrytie-vtb"),
            },
        },
        "gbb7e25e1": {
            "fields": {"target": "g2e85f5e5", "seller_id": "g7ffb3b7a", "seller": "«Севергрупп»"},
            "evidence": {
                "target": ("Fun&Sun", "https://iz.ru/1976420/denis-kuznetcov/goryachaya-putevka-wildberries-russ-kupila-turoperatora-fun-sun"),
                "seller": ("Севергрупп", "https://iz.ru/1976420/denis-kuznetcov/goryachaya-putevka-wildberries-russ-kupila-turoperatora-fun-sun"),
            },
        },
        "g97d0d2a2": {
            "fields": {"buyer": "g549ab474"},
            "evidence": {"buyer": ("ООО «РВБ» (Wildberries & Russ)", "https://www.interfax.ru/business/1048260")},
        },
        "ged395e90": {
            "fields": {"buyer": "g5ff0a3de"},
            "evidence": {"buyer": ("ГК «Черноголовка»", "https://t.me/dealsma/4833")},
        },
        "g92f41a2d": {
            "fields": {"target": "gc0e607dc", "asset": "45% сети «Глобус Гурмэ»"},
            "evidence": {"target": ("Сеть «Глобус Гурмэ»", "https://www.kommersant.ru/doc/5796344")},
        },
        "gff6e08fe": {
            "fields": {"target": "g5d077374", "asset": "9,99% «Евроонко»"},
            "evidence": {"target": ("Евроонко", "https://medvestnik.ru/content/news/Sberbank-priobrel-dolu-v-klinikah-Evroonko.html")},
        },
        "g5a9030d5": {
            "fields": {"target": vtorium, "asset": "Финтех-сервис «Вториум»", "seller": "«Транслом» (структура компании «Кронос»)"},
            "evidence": {
                "target": ("Вториум", "https://www.kommersant.ru/doc/8605576"),
                "seller": ("Транслом", "https://www.kommersant.ru/doc/8605576"),
            },
        },
        "g02a89309": {
            "fields": {"buyer": "gf1f56e08", "target": "g67b53b6a", "asset": "Бизнес-центр Art Plaza"},
            "evidence": {
                "buyer": ("Газпромбанк", "https://t.me/dealsma/6609"),
                "target": ("Бизнес-центр Art Plaza", "https://t.me/dealsma/6609"),
            },
        },
        "g18569a1c": {
            "fields": {"buyer": "gc9913f2a", "target": chzmk, "asset": "96% акций Челябинского завода металлоконструкций"},
            "evidence": {
                "buyer": ("Таймыр Инжиниринг", "https://www.interfax.ru/business/1063509"),
                "target": ("Челябинский завод металлоконструкций", "https://www.interfax.ru/business/1063509"),
            },
        },
    }

    for did, spec in fixes.items():
        deal = by_id.get(did)
        if not deal:
            continue
        before = copy.deepcopy(deal)
        deal.update(copy.deepcopy(spec["fields"]))
        # A previous wrong profile can leave role_hint artefacts; the card is
        # now authoritative and the audit will catch any remaining conflict.
        pe = deal.setdefault("party_evidence", {})
        for role, (value, url) in spec.get("evidence", {}).items():
            pe[role] = evidence(value, url)
        if deal != before:
            changes.append(f"{did}: исправлены роли сторон")

    profile_fixes = {
        "gcafc31dc": {"ind": "Банки", "desc": "Российская банковская группа."},
        "g549ab474": {"ind": "E-commerce", "desc": "Объединённая компания Wildberries и Russ."},
    }
    for cid, fields in profile_fixes.items():
        row = payload.get("companies", {}).get(cid)
        if row:
            before = copy.deepcopy(row)
            row.update(fields)
            if row != before:
                changes.append(f"{cid}: уточнён профиль компании")

    return changes


def main(write: bool) -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    changes = apply(payload)
    if not changes:
        print("Изменений нет.")
        return
    print("\n".join("- " + x for x in changes))
    if not write:
        print("Сухой прогон. Добавьте --write.")
        return
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Записано.")


if __name__ == "__main__":
    main("--write" in sys.argv)
