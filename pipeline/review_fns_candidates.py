#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Редакционная очередь сопоставления профиля «Компаса» с юрлицом из ЕГРЮЛ.

ЧТО ЭТО. `sync_fns.py --match` подтверждает автоматически только строгие
уникальные совпадения. Всё сомнительное складывается в `legal_entity_candidates`
и пользователю не показывается. Этот скрипт выгружает очередь в CSV для Excel и
принимает решения человека обратно.

ПОЧЕМУ CSV, А НЕ АДМИНКА. Сопоставление «бренд → ИНН» решается глазами по
названию, адресу и виду деятельности; редактору нужен список, сортировка и
фильтр, а не отдельный экран на каждую строку. Админка появится вместе с
остальным редакционным контуром (LAUNCH_AUDIT.md, блок P0).

ГРАНИЦА ПРАВКИ. Скрипт не выдумывает совпадений: подтверждается ровно тот ИНН,
который уже лежит в очереди, и только если в колонке `approved` стоит «да».
Пустая колонка не значит «нет» — строка остаётся в очереди до следующего раза,
иначе одна невнимательная выгрузка молча закрыла бы всю очередь.

Запуск:
    python3 pipeline/review_fns_candidates.py --export fns-review.csv
    # поставить yes в колонке approved у правильных строк
    python3 pipeline/review_fns_candidates.py --import-file fns-review.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from db.models import Base, Company, LegalEntityCandidate
from db.session import SessionLocal, engine
from pipeline.sync_fns import _confirm_entity

FIELDS = ["company_id", "company_name", "inn", "ogrn", "legal_name", "address",
          "status", "score", "reasons", "approved"]

YES = {"yes", "y", "да", "д", "1", "true", "+"}
NO = {"no", "n", "нет", "0", "false", "-"}


def _reasons(candidate: LegalEntityCandidate) -> str:
    try:
        return "; ".join(json.loads(candidate.reasons_json or "[]"))
    except (ValueError, TypeError):
        return ""


def export_queue(path) -> int:
    """Выгружает непроверенные строки очереди в CSV. Возвращает число строк."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        rows = db.scalars(
            select(LegalEntityCandidate)
            .where(LegalEntityCandidate.review_status == "new")
            .order_by(LegalEntityCandidate.company_id, LegalEntityCandidate.score.desc())
        ).all()
        names = {c.id: c.name for c in db.scalars(select(Company)).all()}
        # utf-8-sig: без BOM Excel открывает кириллицу как «ÐžÐžÐž».
        with Path(path).open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            for c in rows:
                writer.writerow({
                    "company_id": c.company_id,
                    "company_name": names.get(c.company_id, ""),
                    "inn": c.inn,
                    "ogrn": c.ogrn or "",
                    "legal_name": c.legal_name,
                    "address": c.address or "",
                    "status": c.status or "",
                    "score": "%.2f" % float(c.score or 0),
                    "reasons": _reasons(c),
                    "approved": "",
                })
        return len(rows)


def import_approvals(path) -> int:
    """Принимает решения из CSV. Возвращает число подтверждённых юрлиц."""
    Base.metadata.create_all(engine)
    approved = 0
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    with SessionLocal() as db:
        for row in rows:
            mark = (row.get("approved") or "").strip().lower()
            if mark not in YES and mark not in NO:
                continue  # пусто — решения не было, строка остаётся в очереди
            company_id, inn = (row.get("company_id") or "").strip(), (row.get("inn") or "").strip()
            candidate = db.scalar(select(LegalEntityCandidate).where(
                LegalEntityCandidate.company_id == company_id,
                LegalEntityCandidate.inn == inn,
            ))
            assert candidate is not None, "нет такой строки в очереди: %s / %s" % (company_id, inn)
            if mark in NO:
                candidate.review_status = "rejected"
                continue
            _confirm_entity(db, company_id, {
                "inn": candidate.inn,
                "ogrn": candidate.ogrn,
                "legal_name": candidate.legal_name,
                "address": candidate.address,
                "status": candidate.status,
            }, float(candidate.score or 0), manual=True)
            candidate.review_status = "approved"
            approved += 1
        db.commit()
    return approved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", metavar="ФАЙЛ", help="выгрузить очередь в CSV")
    parser.add_argument("--import-file", metavar="ФАЙЛ", dest="import_file",
                        help="принять решения редактора из CSV")
    args = parser.parse_args()
    if not args.export and not args.import_file:
        parser.error("укажите --export или --import-file")
    if args.export:
        print("Выгружено строк очереди: %d -> %s" % (export_queue(args.export), args.export))
    if args.import_file:
        print("Подтверждено юрлиц: %d" % import_approvals(args.import_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
