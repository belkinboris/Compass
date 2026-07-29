#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Подготовка и синхронизация ЕГРЮЛ/БФО через API-ФНС.

После покупки доступа:
    export API_FNS_KEY='...'
    python pipeline/sync_fns.py --all --auto-confirm

Автоматическое подтверждение намеренно консервативно. Неоднозначные результаты
попадают в legal_entity_candidates и не публикуются до ручной проверки.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from company_catalog import load_company_catalog
from db.models import (
    Base, Company, CompanyAlias, FinancialReport, FnsSyncRun, LegalEntity,
    LegalEntityCandidate, LegalEntityMatchStatus, RegistryEvent,
)
from db.session import SessionLocal, engine
from fns_client import (
    ApiFnsClient, ApiFnsError, normalize_bo, normalize_changes, normalize_egr,
    normalize_search_results,
)

_OPF = re.compile(
    r"\b(ооо|ао|пао|оао|зао|нко|банк|акционерное общество|общество с ограниченной ответственностью|"
    r"автономная некоммерческая организация|фгбу|фгаоу|фгуп|муп|гуп)\b", re.I
)
_PUNCT = re.compile(r"[^0-9a-zа-яё]+", re.I)


def norm_name(value: str | None) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = _OPF.sub(" ", text)
    return " ".join(_PUNCT.sub(" ", text).split())


def _score(profile: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, list[str]]:
    source_names = [profile.get("name"), profile.get("legal_name"), *(profile.get("aliases") or [])]
    c_names = [candidate.get("legal_name"), candidate.get("short_name")]
    best = 0.0
    for left in source_names:
        for right in c_names:
            a, b = norm_name(left), norm_name(right)
            if not a or not b:
                continue
            ratio = SequenceMatcher(None, a, b).ratio()
            if a == b:
                ratio = 1.0
            elif a in b or b in a:
                ratio = max(ratio, 0.90)
            best = max(best, ratio)
    reasons = [f"совпадение названия {best:.0%}"]
    if candidate.get("status") and "действ" in str(candidate["status"]).lower():
        best += 0.02
        reasons.append("действующая организация")
    return min(best, 1.0), reasons


def seed_companies(db) -> int:
    catalog = load_company_catalog()
    changed = 0
    for company_id, item in catalog.items():
        row = db.get(Company, company_id)
        if not row:
            row = Company(id=company_id, name=item["name"])
            db.add(row)
        row.name = item["name"]
        row.legal_name = item.get("legal_name")
        row.industry = item.get("industry")
        row.description = item.get("description")
        row.kpi_label = item.get("kpi_label")
        row.kpi_value = item.get("kpi_value")
        row.auto_generated = bool(item.get("auto_generated"))
        db.flush()
        existing = {a.alias for a in row.aliases}
        aliases = {norm_name(item.get("name")), norm_name(item.get("legal_name"))}
        aliases.update(norm_name(x) for x in item.get("aliases") or [])
        for alias in sorted(x for x in aliases if x and x not in existing):
            # Один алиас не должен быть насильно отнят у другой компании.
            if not db.scalar(select(CompanyAlias).where(CompanyAlias.alias == alias)):
                db.add(CompanyAlias(company_id=company_id, alias=alias))
        changed += 1
    db.commit()
    return changed


def _upsert_candidate(db, company_id: str, row: dict[str, Any], score: float, reasons: list[str]) -> None:
    inn = str(row.get("inn") or "")
    if not inn:
        return
    candidate = db.scalar(select(LegalEntityCandidate).where(
        LegalEntityCandidate.company_id == company_id,
        LegalEntityCandidate.inn == inn,
    ))
    if not candidate:
        candidate = LegalEntityCandidate(company_id=company_id, inn=inn, legal_name=row.get("legal_name") or inn)
        db.add(candidate)
    candidate.ogrn = row.get("ogrn")
    candidate.legal_name = row.get("legal_name") or candidate.legal_name
    candidate.address = row.get("address")
    candidate.status = row.get("status")
    candidate.score = score
    candidate.reasons_json = json.dumps(reasons, ensure_ascii=False)
    candidate.raw_json = json.dumps(row.get("raw") or {}, ensure_ascii=False, default=str)


def _confirm_entity(db, company_id: str, candidate: dict[str, Any], score: float, *, manual: bool = False) -> LegalEntity:
    inn = str(candidate.get("inn") or "")
    entity = db.scalar(select(LegalEntity).where(LegalEntity.inn == inn)) if inn else None
    if not entity:
        entity = LegalEntity(company_id=company_id, legal_name=candidate.get("legal_name") or candidate.get("short_name") or inn)
        db.add(entity)
    entity.company_id = company_id
    entity.legal_name = candidate.get("legal_name") or entity.legal_name
    entity.short_name = candidate.get("short_name")
    entity.inn = inn or None
    entity.ogrn = candidate.get("ogrn")
    entity.status = candidate.get("status")
    entity.address = candidate.get("address")
    entity.match_status = LegalEntityMatchStatus.confirmed
    entity.match_confidence = score
    entity.manually_verified = manual
    entity.is_primary = not bool(db.scalar(select(LegalEntity.id).where(
        LegalEntity.company_id == company_id,
        LegalEntity.is_primary.is_(True),
        LegalEntity.id != (entity.id or -1),
    )))
    return entity


def match_companies(db, client: ApiFnsClient, *, auto_confirm: bool, limit: int | None = None,
                    company_id: str | None = None, dry_run: bool = False) -> tuple[int, int, int]:
    catalog = load_company_catalog()
    ids = [company_id] if company_id else list(catalog)
    if limit:
        ids = ids[:limit]
    matched = candidates = errors = 0
    for cid in ids:
        profile = catalog.get(cid)
        if not profile or not profile.get("name"):
            continue
        # Подтверждённое сопоставление не перетираем поиском.
        if db.scalar(select(LegalEntity.id).where(
            LegalEntity.company_id == cid,
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
        )):
            continue
        try:
            rows = normalize_search_results(client.search(profile["name"]))
        except ApiFnsError as exc:
            print(f"[FNS] {cid}: {exc}", file=sys.stderr)
            errors += 1
            continue
        scored = sorted(((*_score(profile, row), row) for row in rows), key=lambda x: x[0], reverse=True)
        for score, reasons, row in scored[:10]:
            if not dry_run:
                _upsert_candidate(db, cid, row, score, reasons)
            candidates += 1
        # Автопубликация только при почти точном уникальном совпадении и заметном
        # отрыве от второго кандидата. Все остальные остаются редакционной очередью.
        if auto_confirm and scored:
            top_score, _reasons, top = scored[0]
            second = scored[1][0] if len(scored) > 1 else 0
            strict = top_score >= 0.965 and (top_score - second >= 0.08 or second < 0.80)
            if strict:
                if not dry_run:
                    _confirm_entity(db, cid, top, top_score)
                matched += 1
        if not dry_run:
            db.commit()
    return matched, candidates, errors


def sync_entity(db, client: ApiFnsClient, entity: LegalEntity) -> None:
    req = entity.inn or entity.ogrn
    if not req:
        return
    raw_egr = client.egr(req)
    egr = normalize_egr(raw_egr)
    if egr:
        for field in (
            "inn", "ogrn", "kpp", "short_name", "legal_name", "legal_form", "status",
            "registration_date", "termination_date", "address", "region_code", "okved_code",
            "okved_name", "charter_capital_rub", "director_name", "director_title", "director_since",
        ):
            if egr.get(field) is not None:
                setattr(entity, field, egr[field])
        source_date = egr.get("source_updated_at")
        entity.source_updated_at = datetime.combine(source_date, datetime.min.time()) if source_date else None
        entity.raw_egr_json = json.dumps(raw_egr, ensure_ascii=False, default=str)
    entity.fetched_at = datetime.utcnow()

    try:
        bo_raw = client.bo(req)
        reports = normalize_bo(bo_raw, req)
    except ApiFnsError:
        reports = []
    for report in reports:
        row = db.scalar(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id,
            FinancialReport.year == report["year"],
        ))
        if not row:
            row = FinancialReport(legal_entity_id=entity.id, year=report["year"])
            db.add(row)
        for field, value in report.items():
            if field in {"year", "raw_lines"}:
                continue
            setattr(row, field, value)
        row.raw_lines_json = json.dumps(report.get("raw_lines") or {}, ensure_ascii=False, default=str)
        row.fetched_at = datetime.utcnow()

    try:
        changes_raw = client.changes(req)
        changes = normalize_changes(changes_raw)
    except ApiFnsError:
        changes = []
    # История маленькая; полная замена исключает накопление дублей при каждом sync.
    db.query(RegistryEvent).filter_by(legal_entity_id=entity.id).delete()
    for event in changes:
        db.add(RegistryEvent(
            legal_entity_id=entity.id,
            event_date=event.get("event_date"),
            event_type=event.get("event_type"),
            text=event.get("text") or "Изменение в ЕГРЮЛ",
            raw_json=json.dumps(event.get("raw") or {}, ensure_ascii=False, default=str),
        ))
    db.commit()


def sync_confirmed(db, client: ApiFnsClient, *, limit: int | None = None,
                   company_id: str | None = None) -> tuple[int, int]:
    query = select(LegalEntity).where(LegalEntity.match_status == LegalEntityMatchStatus.confirmed)
    if company_id:
        query = query.where(LegalEntity.company_id == company_id)
    rows = list(db.scalars(query.order_by(LegalEntity.id)).all())
    if limit:
        rows = rows[:limit]
    ok = errors = 0
    for entity in rows:
        try:
            sync_entity(db, client, entity)
            ok += 1
        except ApiFnsError as exc:
            print(f"[FNS] {entity.company_id}/{entity.inn}: {exc}", file=sys.stderr)
            db.rollback()
            errors += 1
    return ok, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="перенести справочник компаний из JSON в SQL")
    parser.add_argument("--match", action="store_true", help="найти кандидатов в ЕГРЮЛ")
    parser.add_argument("--sync", action="store_true", help="загрузить ЕГРЮЛ, БФО и изменения подтверждённых юрлиц")
    parser.add_argument("--all", action="store_true", help="seed + match + sync")
    parser.add_argument("--auto-confirm", action="store_true", help="подтверждать только строгие уникальные совпадения")
    parser.add_argument("--company-id")
    parser.add_argument("--inn", help="вручную подтвердить ИНН для --company-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not any((args.seed, args.match, args.sync, args.all, args.inn)):
        parser.error("укажите --seed, --match, --sync, --all или --inn")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        run = FnsSyncRun(mode="all" if args.all else "manual")
        db.add(run); db.commit()
        details: dict[str, Any] = {}
        try:
            if args.seed or args.all:
                details["seeded"] = seed_companies(db)
            if args.inn:
                if not args.company_id:
                    parser.error("для --inn нужен --company-id")
                with ApiFnsClient() as client:
                    rows = normalize_search_results(client.search(args.inn, active_only=False))
                    row = next((x for x in rows if str(x.get("inn")) == args.inn), None)
                    if not row:
                        egr = normalize_egr(client.egr(args.inn))
                        row = egr
                    if not row:
                        raise ApiFnsError(f"юрлицо {args.inn} не найдено")
                    _confirm_entity(db, args.company_id, row, 1.0, manual=True)
                    db.commit()
            if args.match or args.all:
                with ApiFnsClient() as client:
                    m, c, e = match_companies(db, client, auto_confirm=args.auto_confirm,
                                              limit=args.limit, company_id=args.company_id,
                                              dry_run=args.dry_run)
                run.matched += m; run.candidates += c; run.errors += e
                details["match"] = {"confirmed": m, "candidates": c, "errors": e}
            if args.sync or args.all:
                with ApiFnsClient() as client:
                    ok, e = sync_confirmed(db, client, limit=args.limit, company_id=args.company_id)
                run.matched += ok; run.errors += e
                details["sync"] = {"synced": ok, "errors": e}
        finally:
            run.finished_at = datetime.utcnow()
            run.details_json = json.dumps(details, ensure_ascii=False)
            db.commit()
        print(json.dumps(details, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
