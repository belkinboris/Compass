#!/usr/bin/env python3
"""Нормализует отрасли сделок и компаний.

Разделяет тип сделки (IPO/M&A/финансирование) и отрасль актива. Старую
категорию «Инвестиции и рынок ЦБ» удаляет полностью. Для межотраслевых сделок
сохраняет основной сектор в ``ind`` и полный список в ``industries``.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data"
FILES = [
    DATA / "deals_promoted.json",
    DATA / "deals_2026.json",
    DATA / "curated_deals.json",
    DATA / "bulk_deals.json",
]
COMPANY_FILES = [DATA / "curated_companies.json"]

OLD = "Инвестиции и рынок ЦБ"
AI = "Искусственный интеллект"

OLD_ID_MAP = {
    "gcf05509a": ("Гостиницы и туризм", ["Гостиницы и туризм", "Здравоохранение"]),
    "g089e507d": ("Финтех", None),
    "g12a761e4": ("Рынок ценных бумаг", None),
    "ga46c5b15": ("Финансовые услуги", None),
    "g8f41cdc6": ("Управление активами", None),
    "g3074f98b": ("Управление активами", None),
    "gaf184ebb": ("Холдинги", None),
    "gbaf3c565": ("Финансовые услуги", None),
    "g05b2cdb7": ("Управление активами", None),
    "g5badf73f": ("Рынок ценных бумаг", None),
    "gf14ff7aa": ("Управление активами", None),
    "g81d69138": ("Управление активами", None),
    "ga0a49202": ("Развлечения", None),
    "g0be691b7": ("ИТ и интернет", None),
    "g00a0318e": ("Финтех", None),
    "g3ed36abe": ("Финансовые услуги", None),
    "g572a4aca": ("Финансовые услуги", None),
    "g703c4f62": ("Холдинги", None),
    "g4fc7af86": ("Профессиональные услуги", None),
    "gd1f94881": ("Лесопром", None),
    "gdf93c62d": ("Ритейл", None),
    "g93724e30": ("Финтех", None),
    "g473685f6": ("Финансовые услуги", None),
    "g995f83cf": ("Рынок ценных бумаг", None),
    "gd58fa76a": ("Управление активами", None),
    "g2bef2143": ("Финансовые услуги", None),
    "g7c1d0893": ("Лесопром", None),
    "g42e42759": ("Транспорт и логистика", None),
    "g173f659d": ("ЖКХ и обращение с отходами", None),
    "g26b319ff": ("Машиностроение", None),
    "g139d522a": ("Управление активами", None),
    "geb645292": ("Финансовые услуги", None),
    "gc1a34417": ("Финансовые услуги", None),
    "g93f7b5d8": ("Рынок ценных бумаг", None),
    "g8368bb6c": ("Финансовые услуги", None),
    "ga3afca6c": ("Развлечения", None),
    "ga06c75e2": ("Рынок ценных бумаг", None),
    "g3b976e82": ("Рынок ценных бумаг", None),
    "g5d9d8e6c": ("Финтех", None),
    "g62698716": ("Финансовые услуги", None),
    "g020432e9": ("Финансовые услуги", None),
    "g50d455bb": ("Лесопром", None),
    "g7632fe9f": ("Образование", None),
}

AI_RX = re.compile(
    r"(?:\bии\b|искусственн\w*\s+интеллект|artificial\s+intelligence|"
    r"(?:^|[^a-z])ai(?:[^a-z]|$)|нейросет|генеративн\w+\s+(?:модел|ии)|\bllm\b|машинн\w+\s+обучен)",
    re.I,
)
PURE_AI_RX = re.compile(
    r"(?:ии[-\s]?(?:стартап|платформ|компани|разработчик|сервис|систем)|"
    r"стартап\w*\s+(?:в\s+сфере\s+)?ии|искусственн\w*\s+интеллект|"
    r"нейросет|just\s*ai|aib\b|архитех\s*ии|мультиагент)",
    re.I,
)

PHARMA_RX = re.compile(r"фарм|лекарств|препарат|вакцин|биотех|биофарм|фармацевт", re.I)
HEALTH_RX = re.compile(r"медси|клиник|больниц|медицин|здравоохран|диагност|стоматолог|лаборатор", re.I)
HOTEL_RX = re.compile(r"cosmos|hotel|отел|гостиниц|курорт|санатор", re.I)


def uniq(values):
    out = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


def all_text(deal: dict) -> str:
    chunks = [deal.get("title", ""), deal.get("asset", ""), deal.get("extra", "")]
    for key in ("eco", "law"):
        obj = deal.get(key) or {}
        if isinstance(obj, dict):
            chunks.extend(str(v) for v in obj.values() if isinstance(v, str))
    return " ".join(chunks)


def normalize_deal(deal: dict) -> bool:
    before = json.dumps(deal, ensure_ascii=False, sort_keys=True)
    text = all_text(deal)
    did = deal.get("id")

    if did in OLD_ID_MAP:
        primary, industries = OLD_ID_MAP[did]
        deal["ind"] = primary
        if industries:
            deal["industries"] = industries
        else:
            deal.pop("industries", None)
    elif deal.get("ind") == OLD:
        # Запасная классификация для новых записей, которые не вошли в ручную карту.
        t = text.lower()
        if re.search(r"бирж|ipo|spo|акци|брокер|депозитар|рын[оы]к\s+ценных\s+бумаг", t):
            deal["ind"] = "Рынок ценных бумаг"
        elif re.search(r"фонд|зпиф|управляющ|asset\s+management|инвестиционн\w+\s+платформ", t):
            deal["ind"] = "Управление активами"
        elif re.search(r"плат[её]ж|финтех|мфк|мкк|qiwi|микрофин", t):
            deal["ind"] = "Финтех"
        else:
            deal["ind"] = "Финансовые услуги"

    if deal.get("ind") == "Фарма и медицина":
        if PHARMA_RX.search(text) and not HEALTH_RX.search(text):
            deal["ind"] = "Фармацевтика"
        else:
            deal["ind"] = "Здравоохранение"

    # Отель может юридически быть недвижимостью, но для поиска сделки полезнее
    # отрасль операционного бизнеса. Смотрим только на заголовок и предмет,
    # чтобы случайное упоминание отеля в контексте не переклассифицировало ТЦ.
    hotel_subject = f"{deal.get('title', '')} {deal.get('asset', '')}"
    if HOTEL_RX.search(hotel_subject) and deal.get("ind") == "Недвижимость":
        deal["ind"] = "Гостиницы и туризм"
        deal["industries"] = uniq(["Гостиницы и туризм", "Недвижимость"] + list(deal.get("industries") or []))
    elif (deal.get("ind") == "Гостиницы и туризм"
          and deal.get("industries") == ["Гостиницы и туризм", "Недвижимость"]
          and not HOTEL_RX.search(hotel_subject)):
        deal["ind"] = "Недвижимость"
        deal.pop("industries", None)

    # Отдельная отрасль для компаний, чей продукт непосредственно основан на ИИ.
    # Для обычной компании, которая лишь использует ИИ, оставляем основной сектор
    # и добавляем тематический тег.
    if AI_RX.search(text):
        themes = deal.setdefault("themes", [])
        if AI not in themes:
            themes.append(AI)
        if PURE_AI_RX.search(text):
            previous = deal.get("ind")
            deal["ind"] = AI
            deal["industries"] = uniq([AI, previous] + list(deal.get("industries") or []))

    # Межотраслевая карточка Cosmos/«Медси»: IPO — тип, а не отрасль.
    if did == "gcf05509a":
        deal["type"] = "IPO"
        deal["ind"] = "Гостиницы и туризм"
        deal["industries"] = ["Гостиницы и туризм", "Здравоохранение"]

    industries = uniq(deal.get("industries") or [])
    if industries:
        if deal.get("ind") not in industries:
            industries.insert(0, deal.get("ind"))
        deal["industries"] = industries
    return before != json.dumps(deal, ensure_ascii=False, sort_keys=True)


def company_industry_from_text(company: dict) -> str | None:
    text = f"{company.get('name', '')} {company.get('desc', '')}"
    if PURE_AI_RX.search(text): return AI
    if HOTEL_RX.search(text): return "Гостиницы и туризм"
    if HEALTH_RX.search(text): return "Здравоохранение"
    if PHARMA_RX.search(text): return "Фармацевтика"
    if re.search(r"бирж|брокер|депозитар|ренессанс\s+капитал|инвестбанк", text, re.I): return "Рынок ценных бумаг"
    if re.search(r"зпиф|фонд|управляющ|asset\s+management", text, re.I): return "Управление активами"
    if re.search(r"плат[её]ж|финтех|микрофин|мфк|мкк|qiwi", text, re.I): return "Финтех"
    if re.search(r"лизинг|факторинг|ломбард|коллектор", text, re.I): return "Финансовые услуги"
    return None


def normalize_company_map(companies: dict, deals: list[dict]) -> int:
    linked: dict[str, Counter] = defaultdict(Counter)
    for d in deals:
        inds = d.get("industries") or [d.get("ind")]
        for cid in (d.get("buyer"), d.get("target"), d.get("seller_id"), d.get("asset_id")):
            if cid:
                linked[cid].update(x for x in inds if x)
    changed = 0
    for cid, company in companies.items():
        old = company.get("ind")
        new = old
        if old == OLD or old == "Фарма и медицина":
            explicit = company_industry_from_text(company)
            if explicit:
                new = explicit
            elif linked.get(cid):
                new = linked[cid].most_common(1)[0][0]
            elif old == "Фарма и медицина":
                new = "Здравоохранение"
            else:
                new = "Финансовые услуги"
        if new != old:
            company["ind"] = new
            changed += 1
    return changed


def process(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        deals = data.get("deals") or []
        companies = data.get("companies") or {}
    else:
        deals, companies = data, {}
    changed_deals = sum(normalize_deal(d) for d in deals)
    changed_companies = normalize_company_map(companies, deals) if companies else 0
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed_deals, changed_companies


def main() -> None:
    total_d = total_c = 0
    for path in FILES:
        if not path.exists():
            continue
        d, c = process(path)
        total_d += d; total_c += c
        print(f"{path.relative_to(ROOT)}: deals={d}, companies={c}")
    for path in COMPANY_FILES:
        if not path.exists():
            continue
        companies = json.loads(path.read_text(encoding="utf-8"))
        changed = normalize_company_map(companies, [])
        path.write_text(json.dumps(companies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total_c += changed
        print(f"{path.relative_to(ROOT)}: companies={changed}")
    print(f"Итого: сделок изменено {total_d}, компаний {total_c}")


if __name__ == "__main__":
    main()
