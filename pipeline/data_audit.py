# -*- coding: utf-8 -*-
"""Проверка качества карточек сделок и профилей компаний.

Скрипт читает и автоматическую, и кураторскую часть каталога. Он ничего не
склеивает сам: результатом являются отчёт и очередь редакционной проверки.

Проверяются:
- отсутствующие или конфликтующие роли сторон;
- ссылки на несуществующие профили с учётом алиасов объединённых компаний;
- статус, заголовок, источники и хронология этапов;
- вероятные дубли жизненного цикла и отдельные связанные транзакции;
- возможное смешение разных активов в одном профиле компании.

Результат: ``DATA_AUDIT.md`` и ``data/audit/deal_audit.json``.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
CURATED_DEALS = ROOT / "static" / "data" / "curated_deals.json"
CURATED_COMPANIES = ROOT / "static" / "data" / "curated_companies.json"
OUT_JSON = ROOT / "data" / "audit" / "deal_audit.json"
OUT_MD = ROOT / "DATA_AUDIT.md"

OPEN = {"Обсуждается", "Подписана", "Согласование получено"}
TERMINAL = {"Закрыта", "Не состоялась"}
M_AND_A = {"M&A", "Продажа недвижимости", "Выкуп доли"}
PRESENT = re.compile(r"\b(?:покупает|приобретает|прода[её]т|выкупает|получает|созда[её]т)\b", re.I)
CANCEL_WORDS = re.compile(r"не\s+состоял|сорвал|прекращен|прекращён|отказал.*сделк", re.I)
CLOSED_WORDS = re.compile(r"приобр[её]л|купил|продал|завершил|закрыл", re.I)
HOME_PATHS = {"", "/", "/ru", "/ru/", "/index.html"}
GENERIC_NAMES = re.compile(r"^(?:компания|группа|структура|владельцы|акционеры|инвесторы|не раскрыт)$", re.I)
STOP = {
    "компания", "группа", "сделка", "бизнес", "акции", "доля", "долей", "покупка",
    "продажа", "приобрел", "приобрела", "купил", "купила", "получил", "получила",
    "российский", "российские", "россии", "структура", "структуры", "активы", "актива",
}


@dataclass
class Issue:
    severity: str
    code: str
    deal_id: str
    title: str
    detail: str


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def combined_payload() -> dict:
    """Единый каталог для аудита без изменения исходных JSON."""
    promoted = read_json(DATA, {})
    result = {
        **promoted,
        "companies": dict(promoted.get("companies") or {}),
        "deals": list(promoted.get("deals") or []),
    }
    result["companies"].update(read_json(CURATED_COMPANIES, {}))
    by_id = {str(d.get("id")): d for d in result["deals"] if isinstance(d, dict) and d.get("id")}
    for deal in read_json(CURATED_DEALS, []):
        if isinstance(deal, dict) and deal.get("id"):
            by_id[str(deal["id"])] = deal
    result["deals"] = list(by_id.values())
    return result


def norm(value: object) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = re.sub(r"\b(?:ооо|ао|пао|зао|оао|гк|ук|мкао|мкпао|ltd|llc|inc|plc|group|holding)\b", " ", text)
    text = re.sub(r"[^a-zа-я0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_words(value: object) -> set[str]:
    return {w for w in norm(value).split() if len(w) >= 4 and w not in STOP}


def days(a: str | None, b: str | None) -> int:
    try:
        return abs((date.fromisoformat(str(a)[:10]) - date.fromisoformat(str(b)[:10])).days)
    except Exception:
        return 99999


def source_urls(deal: dict) -> list[str]:
    return [str(x[1]) for x in deal.get("src") or [] if isinstance(x, list) and len(x) > 1 and x[1]]


def source_is_homepage(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return True
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return True
    path = parsed.path or "/"
    return path.lower() in HOME_PATHS 


def resolve_company(payload: dict, cid: str | None) -> str | None:
    if not cid:
        return None
    aliases = payload.get("merged_companies") or {}
    seen: set[str] = set()
    current = str(cid)
    while current in aliases and current not in seen:
        seen.add(current)
        current = str(aliases[current])
    return current


def company_name(payload: dict, cid: str | None) -> str:
    resolved = resolve_company(payload, cid)
    if not resolved:
        return ""
    row = payload.get("companies", {}).get(resolved) or {}
    return str(row.get("name") or resolved)


def role_value(payload: dict, deal: dict, field: str, fallback: str) -> str:
    cid = resolve_company(payload, deal.get(field))
    return str(cid or norm(deal.get(fallback)) or "")


def party_signature(payload: dict, deal: dict) -> tuple[str, str]:
    buyer = role_value(payload, deal, "buyer", "buyer_name")
    target = resolve_company(payload, deal.get("target") or deal.get("asset_id")) or norm(deal.get("asset"))
    return str(buyer or ""), str(target or "")


def validate_deal(payload: dict, deal: dict) -> list[Issue]:
    issues: list[Issue] = []
    did, title = str(deal.get("id") or "?"), str(deal.get("title") or "")
    companies = payload.get("companies", {})

    for field in ("buyer", "seller_id", "target", "asset_id"):
        cid = deal.get(field)
        resolved = resolve_company(payload, cid)
        if cid and resolved not in companies:
            issues.append(Issue("error", "unknown_company_ref", did, title, f"{field} ссылается на отсутствующий профиль {cid}"))

    ids = [resolve_company(payload, deal.get(x)) for x in ("buyer", "seller_id", "target", "asset_id") if deal.get(x)]
    ids = [x for x in ids if x]
    if len(ids) != len(set(ids)):
        issues.append(Issue("error", "same_entity_multiple_roles", did, title, "Один профиль занимает несколько ролей в одной карточке"))

    if deal.get("type") in M_AND_A:
        if not (deal.get("buyer") or deal.get("buyer_name")):
            issues.append(Issue("warning", "missing_buyer", did, title, "Не указан покупатель"))
        if not (deal.get("target") or deal.get("asset_id") or deal.get("asset")):
            issues.append(Issue("warning", "missing_target", did, title, "Не указан предмет сделки"))
        if deal.get("status") in TERMINAL and not (deal.get("seller_id") or deal.get("seller")):
            issues.append(Issue("warning", "missing_seller", did, title, "Продавец не указан; нужно проверить источник или отметить, что он не раскрыт"))

    if deal.get("status") == "Закрыта" and PRESENT.search(title):
        issues.append(Issue("warning", "closed_title_present_tense", did, title, "Закрытая сделка названа настоящим временем"))
    if deal.get("status") == "Не состоялась" and not CANCEL_WORDS.search(title + " " + str(deal.get("extra") or "")):
        issues.append(Issue("info", "cancelled_without_marker", did, title, "Статус сообщает о срыве, но это неясно из заголовка"))
    if deal.get("status") in OPEN and CLOSED_WORDS.search(title):
        issues.append(Issue("warning", "open_status_closed_title", did, title, "Заголовок звучит как закрытие, а статус остаётся открытым"))

    urls = source_urls(deal)
    if not urls:
        issues.append(Issue("error", "missing_source", did, title, "Нет рабочей ссылки на источник"))
    elif all(source_is_homepage(x) for x in urls):
        issues.append(Issue("warning", "homepage_only_sources", did, title, "Все источники ведут на главную страницу, а не на публикацию"))

    if deal.get("seller") and GENERIC_NAMES.match(norm(deal.get("seller"))):
        issues.append(Issue("warning", "generic_seller", did, title, f"В поле продавца стоит общее обозначение: {deal.get('seller')}"))

    events = deal.get("events") or []
    if events:
        dates = [str(e.get("date") or "") for e in events if isinstance(e, dict)]
        if dates != sorted(dates):
            issues.append(Issue("warning", "events_not_sorted", did, title, "Этапы сделки записаны не по хронологии"))
        event_keys = [(e.get("kind"), e.get("date")) for e in events if isinstance(e, dict) and e.get("kind")]
        duplicates = [f"{k} ({dt})" for (k, dt), n in Counter(event_keys).items() if n > 1]
        if duplicates:
            issues.append(Issue("info", "duplicate_events", did, title, "Повторяются одинаковые этапы: " + ", ".join(duplicates)))

    return issues


def duplicate_candidates(payload: dict) -> tuple[list[dict], list[dict]]:
    """Вернуть (вероятные дубли/этапы, просто связанные карточки)."""
    deals = payload.get("deals", [])
    candidates: list[dict] = []
    related: list[dict] = []
    by_pair: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_url: dict[str, list[dict]] = defaultdict(list)
    for deal in deals:
        pair = party_signature(payload, deal)
        if all(pair):
            by_pair[pair].append(deal)
        for url in source_urls(deal):
            if not source_is_homepage(url):
                by_url[url].append(deal)

    seen: set[tuple[str, str]] = set()
    for pair, rows in by_pair.items():
        if len(rows) < 2:
            continue
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                key = tuple(sorted((str(a["id"]), str(b["id"]))))
                if key in seen:
                    continue
                if a.get("separate_transaction_reviewed") or b.get("separate_transaction_reviewed"):
                    related.append({
                        "deal_a": a["id"], "deal_b": b["id"], "classification": "reviewed_separate",
                        "reason": "редакционно подтверждены как отдельные связанные транзакции",
                        "gap_days": days(a.get("date"), b.get("date")), "title_similarity": 0,
                        "title_a": a.get("title"), "title_b": b.get("title"),
                    })
                    seen.add(key)
                    continue
                gap = days(a.get("date"), b.get("date"))
                common = len(title_words(a.get("title")) & title_words(b.get("title")))
                similarity = SequenceMatcher(None, norm(a.get("title")), norm(b.get("title"))).ratio()
                lifecycle = ((a.get("status") in OPEN and b.get("status") in TERMINAL) or
                             (b.get("status") in OPEN and a.get("status") in TERMINAL))
                same_terminal = a.get("status") in TERMINAL and b.get("status") in TERMINAL
                if lifecycle and gap <= 1500:
                    candidates.append({
                        "deal_a": a["id"], "deal_b": b["id"], "classification": "lifecycle",
                        "reason": "одни покупатель и предмет; открытая и конечная стадии одного процесса",
                        "gap_days": gap, "title_similarity": round(similarity, 3),
                        "title_a": a.get("title"), "title_b": b.get("title"),
                    })
                    seen.add(key)
                elif gap <= 120 and (common >= 2 or similarity >= 0.62):
                    target = candidates if same_terminal and similarity >= 0.52 else related
                    target.append({
                        "deal_a": a["id"], "deal_b": b["id"],
                        "classification": "probable_duplicate" if target is candidates else "related_transaction",
                        "reason": "одни стороны и близкие заголовки" if target is candidates else "одни стороны, но это могут быть разные пакеты или раунды",
                        "gap_days": gap, "title_similarity": round(similarity, 3),
                        "title_a": a.get("title"), "title_b": b.get("title"),
                    })
                    seen.add(key)

    for url, rows in by_url.items():
        if len(rows) < 2:
            continue
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                key = tuple(sorted((str(a["id"]), str(b["id"]))))
                if key in seen:
                    continue
                similarity = SequenceMatcher(None, norm(a.get("title")), norm(b.get("title"))).ratio()
                same_pair = party_signature(payload, a) == party_signature(payload, b) and all(party_signature(payload, a))
                row = {
                    "deal_a": a["id"], "deal_b": b["id"], "source": url,
                    "title_similarity": round(similarity, 3),
                    "title_a": a.get("title"), "title_b": b.get("title"),
                }
                if same_pair or similarity >= 0.68:
                    row.update(classification="probable_duplicate", reason="одна публикация и совпадающие стороны или заголовки")
                    candidates.append(row)
                else:
                    row.update(classification="source_reuse", reason="одна публикация используется как контекст для разных карточек")
                    related.append(row)
                seen.add(key)
    return (sorted(candidates, key=lambda x: (-x.get("title_similarity", 0), str(x["deal_a"]))),
            sorted(related, key=lambda x: (-x.get("title_similarity", 0), str(x["deal_a"]))))


def profile_collision_candidates(payload: dict) -> list[dict]:
    """Только сильные сигналы: один target связан с несовместимыми asset-полями."""
    companies = payload.get("companies", {})
    assets: dict[str, set[str]] = defaultdict(set)
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    for deal in payload.get("deals", []):
        cid = resolve_company(payload, deal.get("target") or deal.get("asset_id"))
        asset = norm(deal.get("asset"))
        if not cid or not asset or len(asset) < 5:
            continue
        assets[cid].add(asset)
        examples[(cid, asset)].append(str(deal.get("id")))

    result = []
    for cid, values in assets.items():
        if len(values) < 2:
            continue
        vals = sorted(values)
        incompatible = []
        for i, a in enumerate(vals):
            for b in vals[i + 1:]:
                if SequenceMatcher(None, a, b).ratio() < 0.25 and not (title_words(a) & title_words(b)):
                    incompatible.extend([a, b])
        incompatible = sorted(set(incompatible))
        if len(incompatible) >= 2:
            result.append({
                "company_id": cid,
                "company": (companies.get(cid) or {}).get("name"),
                "asset_names": incompatible[:8],
                "deal_examples": {x: examples[(cid, x)][:3] for x in incompatible[:8]},
            })
    return result


def write_report(payload: dict, issues: list[Issue], duplicates: list[dict], related: list[dict], collisions: list[dict]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    stats = Counter(x.code for x in issues)
    document = {
        "generated_for_deals": len(payload.get("deals", [])),
        "issues": [asdict(x) for x in issues],
        "duplicate_candidates": duplicates,
        "related_candidates": related,
        "profile_collision_candidates": collisions,
        "counts": dict(stats),
    }
    OUT_JSON.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Аудит данных «Компаса»", "",
        f"Проверено карточек: **{len(payload.get('deals', []))}** (основная и кураторская части).", "",
        "Автоматическая проверка не склеивает карточки. Она отделяет вероятные дубли жизненного цикла от самостоятельных транзакций с теми же сторонами.", "",
        "## Сводка", "",
    ]
    for code, count in stats.most_common():
        lines.append(f"- `{code}` — {count}")
    lines += ["", f"Кандидатов на объединение или связывание этапов: **{len(duplicates)}**.",
              f"Связанных карточек, которые нельзя склеивать автоматически: **{len(related)}**.",
              f"Сильных подозрений на смешение профилей компаний: **{len(collisions)}**.", ""]

    lines += ["## Основные сигналы для редакционной проверки", ""]
    priority = [x for x in issues if x.severity in {"error", "warning"}]
    for issue in priority[:120]:
        lines.append(f"- **{issue.deal_id}** — {issue.detail}. {issue.title}")
    if len(priority) > 120:
        lines.append(f"- …ещё {len(priority)-120}; полный список находится в `data/audit/deal_audit.json`.")

    lines += ["", "## Кандидаты на объединение или редакционную связь", ""]
    for row in duplicates[:80]:
        lines.append(f"- **{row['deal_a']} ↔ {row['deal_b']}** — {row['reason']}. «{row['title_a']}» / «{row['title_b']}»")
    if len(duplicates) > 80:
        lines.append(f"- …ещё {len(duplicates)-80} в JSON-отчёте.")

    lines += ["", "## Похожие, но потенциально самостоятельные транзакции", ""]
    for row in related[:50]:
        lines.append(f"- **{row['deal_a']} ↔ {row['deal_b']}** — {row['reason']}. «{row['title_a']}» / «{row['title_b']}»")

    lines += ["", "## Правила публикации", "",
              "1. Одна карточка описывает один жизненный цикл сделки; переговоры, подписание, согласование, закрытие или срыв добавляются в `events`.",
              "2. Последовательные покупки разных пакетов, раунды финансирования и обратные продажи не склеиваются автоматически.",
              "3. Покупатель, продавец и предмет хранятся раздельно; каждое автоматически добавленное значение получает `party_evidence` со ссылкой на источник.",
              "4. Заполненное редакционное поле не перезаписывается эвристикой. Расхождение попадает в очередь проверки.",
              "5. Домашняя страница сайта не считается достаточным источником сделки.",
              "6. Новая M&A-карточка без покупателя или предмета сделки не публикуется автоматически.",
              "7. Старые адреса объединённых карточек должны вести на соответствующий исторический этап.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = combined_payload()
    issues = [issue for deal in payload.get("deals", []) for issue in validate_deal(payload, deal)]
    duplicates, related = duplicate_candidates(payload)
    collisions = profile_collision_candidates(payload)
    write_report(payload, issues, duplicates, related, collisions)
    print(f"Карточек: {len(payload.get('deals', []))}")
    print(f"Сигналов для проверки: {len(issues)}")
    print(f"Кандидатов на дубль/этап: {len(duplicates)}")
    print(f"Связанных карточек: {len(related)}")
    print(f"Подозрений на смешение профилей: {len(collisions)}")
    for code, count in Counter(x.code for x in issues).most_common():
        print(f"  {code}: {count}")
    print("Отчёты:", OUT_MD.relative_to(ROOT), "и", OUT_JSON.relative_to(ROOT))


if __name__ == "__main__":
    main()
