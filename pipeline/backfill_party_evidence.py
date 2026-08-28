# -*- coding: utf-8 -*-
"""Консервативно восстановить роли сторон из заголовков уже проверенных карточек.

Скрипт заполняет только пустые поля и не заменяет редакционные значения. Имя
берётся из явной конструкции заголовка («X купил Y у Z», «X продал Y»). Если
имя однозначно совпадает с профилем компании, сохраняется id; иначе остаётся
строкой. Для каждого добавленного значения сохраняется ссылка на источник.

Запуск:
    python3 pipeline/backfill_party_evidence.py
    python3 pipeline/backfill_party_evidence.py --write
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
import draft  # noqa: E402

LEGAL = re.compile(r"\b(?:ооо|ао|пао|зао|оао|гк|ук|мкао|мкпао|ltd|llc|inc|plc|group|holding)\b", re.I)
JUNK = re.compile(
    r"^(?:долю|доли|акции|пакет|контроль|бизнес|активы|российский бизнес|российские активы|"
    r"не раскрыт|неизвестный покупатель|компания|структура)$", re.I
)


def norm(value: str | None) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = LEGAL.sub(" ", text)
    text = re.sub(r"[«»\"'`().,:;/\\—–-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def aliases(payload: dict) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for cid, company in payload.get("companies", {}).items():
        values = [company.get("name")]
        values += payload.get("match_keys", {}).get(cid, []) or []
        for value in values:
            key = norm(value)
            if key and cid not in index[key]:
                index[key].append(cid)
    return index


def resolve(name: str | None, index: dict[str, list[str]], *, leading: bool = False) -> str | None:
    """Однозначное точное либо вложенное совпадение с профилем.

    Вложенное совпадение нужно для формулировок вроде «100% АО „Р7“
    (разработчик офисного ПО)». Берём только самый длинный ключ, не короче
    четырёх знаков, и только если все лучшие совпадения ведут в один профиль.
    """
    key = norm(name)
    ids = index.get(key, [])
    if len(ids) == 1:
        return ids[0]
    if not key:
        return None
    raw = str(name or "").lower()
    if any(mark in raw for mark in (",", ";", " и ")) or re.search(r"\b(?:инвесторов|акционеров|владельцев|консорциум)\b", raw):
        return None
    padded = f" {key} "
    candidates: list[tuple[int, str]] = []
    for alias, alias_ids in index.items():
        if len(alias) < 4 or len(alias_ids) != 1:
            continue
        if f" {alias} " not in padded:
            continue
        if leading and not key.startswith(alias):
            # В названии стороны основной субъект стоит первым. Это не даёт
            # принять владельца из хвоста «Fortiana Владислава Свиблова» за
            # саму компанию-покупателя.
            continue
        candidates.append((len(alias), alias_ids[0]))
    if not candidates:
        return None
    longest = max(length for length, _ in candidates)
    winners = {cid for length, cid in candidates if length == longest}
    return next(iter(winners)) if len(winners) == 1 else None


def useful(name: str | None) -> bool:
    text = str(name or "").strip()
    return 2 < len(text) <= 100 and not JUNK.match(norm(text))


def first_url(deal: dict) -> str | None:
    for row in deal.get("src") or []:
        if isinstance(row, list) and len(row) > 1 and str(row[1]).startswith("http"):
            return row[1]
    return None


def add_evidence(deal: dict, role: str, value: str, field: str) -> None:
    rows = deal.setdefault("party_evidence", {}).setdefault(role, [])
    url = first_url(deal)
    item = {"value": value, "field": field, "method": "explicit_title"}
    if url:
        item["url"] = url
    if item not in rows:
        rows.append(item)


def migrate(payload: dict) -> tuple[dict, list[tuple[str, str, str, str]]]:
    index = aliases(payload)
    changes: list[tuple[str, str, str, str]] = []
    for deal in payload.get("deals", []):
        buyer, asset, seller, _ = draft.guess_parties(deal.get("title"))

        # Автоматически связываем только однозначное точное совпадение с уже
        # существующим профилем. Свободный текст вроде «российские активы ...»
        # слишком легко захватывает следующую сторону предложения.
        if not (deal.get("buyer") or deal.get("buyer_name")) and useful(buyer):
            cid = resolve(buyer, index, leading=True)
            if cid and cid not in {deal.get("target"), deal.get("asset_id"), deal.get("seller_id")}:
                deal["buyer"] = cid
                add_evidence(deal, "buyer", buyer, "buyer")
                changes.append((deal["id"], "покупатель", buyer, "buyer"))

        if not (deal.get("target") or deal.get("asset_id") or deal.get("asset")) and useful(asset):
            cid = resolve(asset, index)
            if cid and cid not in {deal.get("buyer"), deal.get("seller_id")}:
                deal["target"] = cid
                add_evidence(deal, "target", asset, "target")
                changes.append((deal["id"], "предмет", asset, "target"))

        if not (deal.get("seller_id") or deal.get("seller")) and useful(seller):
            cid = resolve(seller, index, leading=True)
            if cid and cid not in {deal.get("buyer"), deal.get("target"), deal.get("asset_id")}:
                deal["seller_id"] = cid
                add_evidence(deal, "seller", seller, "seller_id")
                changes.append((deal["id"], "продавец", seller, "seller_id"))
    return payload, changes


def main(write: bool) -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    payload, changes = migrate(payload)
    print(f"Найдено безопасных дополнений: {len(changes)}")
    for deal_id, role, value, field in changes[:40]:
        print(f"  {deal_id}: {role} = {value!r} ({field})")
    if len(changes) > 40:
        print(f"  ... ещё {len(changes)-40}")
    if write and changes:
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Записано.")
    elif not write:
        print("Сухой прогон. Добавьте --write.")


if __name__ == "__main__":
    main("--write" in sys.argv)
