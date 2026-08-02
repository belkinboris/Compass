# -*- coding: utf-8 -*-
"""Новые функции запуска: ФНС, алерты, экспорт, вебинары и mobile UI."""
from datetime import date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from db.models import (
    Company, FinancialReport, LegalEntity, LegalEntityMatchStatus,
    Notification, OwnershipSnapshot, OwnershipStake, RegistryEvent, User, UserTier, Webinar,
)
from db.session import get_session
from notification_service import create_notification

_TEST_PASSWORD = "надёжный-тестовый-пароль"


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def _login(client: TestClient, email: str) -> User:
    response = client.post("/api/auth/register", json={"email": email, "password": _TEST_PASSWORD})
    assert response.status_code == 200
    db = get_session()
    try:
        user = db.query(User).filter_by(email=email.lower()).one()
        db.expunge(user)
        return user
    finally:
        db.close()


def _seed_fns_company(company_id: str = "launch-fns-company") -> int:
    db = get_session()
    try:
        company = db.get(Company, company_id)
        if not company:
            company = Company(id=company_id, name="Тестовая компания", legal_name='ООО "Тестовая компания"')
            db.add(company)
            db.flush()
        entity = db.query(LegalEntity).filter_by(inn="7700000099").first()
        if not entity:
            entity = LegalEntity(
                company_id=company_id,
                legal_name='Общество с ограниченной ответственностью "Тестовая компания"',
                short_name='ООО "Тестовая компания"',
                inn="7700000099", ogrn="1027700000099", kpp="770001001",
                status="Действующая", registration_date=date(2018, 3, 12),
                address="г. Москва", okved_code="62.01", okved_name="Разработка ПО",
                director_name="Иванов Иван Иванович",
                match_status=LegalEntityMatchStatus.confirmed,
                manually_verified=True, is_primary=True,
                fetched_at=datetime.utcnow(), source_updated_at=datetime.utcnow(),
            )
            db.add(entity)
            db.flush()
        else:
            entity.company_id = company_id
            entity.match_status = LegalEntityMatchStatus.confirmed
        for year, revenue, profit in ((2025, 1_500_000_000, 210_000_000), (2024, 1_200_000_000, 160_000_000)):
            row = db.query(FinancialReport).filter_by(legal_entity_id=entity.id, year=year).first()
            if not row:
                db.add(FinancialReport(
                    legal_entity_id=entity.id, year=year,
                    revenue_rub=revenue, net_profit_rub=profit,
                    assets_rub=2_300_000_000, equity_rub=900_000_000,
                ))
        if not db.query(RegistryEvent).filter_by(legal_entity_id=entity.id).first():
            for idx in range(4):
                db.add(RegistryEvent(
                    legal_entity_id=entity.id,
                    event_date=date(2026, 7, 20 - idx),
                    event_type="Изменение сведений",
                    text=f"Тестовое изменение {idx + 1}",
                ))
        if not db.query(OwnershipSnapshot).filter_by(legal_entity_id=entity.id).first():
            old_snapshot = OwnershipSnapshot(
                legal_entity_id=entity.id, snapshot_date=date(2024, 1, 1),
                source_kind="changes", is_complete=True,
                source_text="Изменение состава участников",
            )
            db.add(old_snapshot); db.flush()
            db.add(OwnershipStake(
                snapshot_id=old_snapshot.id, owner_key="7700000011",
                owner_name='ООО "Первый участник"', owner_type="Российское юридическое лицо",
                inn="7700000011", share_percent=100,
            ))
            current_snapshot = OwnershipSnapshot(
                legal_entity_id=entity.id, snapshot_date=date(2026, 2, 18),
                source_kind="current", is_complete=True,
                source_text="Текущий состав участников по ЕГРЮЛ",
            )
            db.add(current_snapshot); db.flush()
            db.add(OwnershipStake(
                snapshot_id=current_snapshot.id, owner_key="7700000022",
                owner_name='ООО "Новый участник"', owner_type="Российское юридическое лицо",
                inn="7700000022", share_percent=100,
            ))
        db.commit()
        return entity.id
    finally:
        db.close()


def test_fns_company_dossier_free_and_paid_access(client):
    _seed_fns_company()
    anonymous = client.get("/api/companies/launch-fns-company/fns")
    assert anonymous.status_code == 200
    body = anonymous.json()
    assert body["available"] is True
    assert body["access"]["paid"] is False
    assert len(body["entities"][0]["reports"]) == 1
    assert body["entities"][0]["has_more_reports"] is True
    assert len(body["entities"][0]["events"]) == 3
    ownership = body["entities"][0]["ownership"]
    assert ownership["available"] is True
    assert ownership["current"][0]["name"] == 'ООО "Новый участник"'
    assert {row["kind"] for row in ownership["history"]} >= {"joined", "left"}
    historical = client.get("/api/companies/launch-fns-company/fns?as_of_year=2025").json()
    assert historical["entities"][0]["reports"][0]["year"] == 2024

    _login(client, "paid-fns@firm.ru")
    db = get_session()
    try:
        user = db.query(User).filter_by(email="paid-fns@firm.ru").one()
        user.tier = UserTier.paid
        db.commit()
    finally:
        db.close()
    paid = client.get("/api/companies/launch-fns-company/fns").json()
    assert paid["access"]["full_history"] is True
    assert len(paid["entities"][0]["reports"]) >= 2
    assert len(paid["entities"][0]["events"]) >= 4


def test_deal_watch_round_trip_and_default_preferences(client):
    assert client.post("/api/deals/g1d36d186/watch").status_code == 401
    _login(client, "watch-launch@firm.ru")
    assert client.get("/api/deals/g1d36d186/watch").json()["watching"] is False
    assert client.post("/api/deals/g1d36d186/watch").json() == {"watching": True}
    assert client.get("/api/deals/g1d36d186/watch").json()["watching"] is True
    listed = client.get("/api/deal-watches").json()
    assert any(row["deal_id"] == "g1d36d186" for row in listed)
    prefs = client.get("/api/notification-preferences").json()
    assert prefs["in_app_enabled"] is True and prefs["weekly_digest"] is True
    assert client.delete("/api/deals/g1d36d186/watch").json() == {"watching": False}


def test_notification_preference_hides_in_app_feed(client):
    user = _login(client, "notify-launch@firm.ru")
    assert client.patch("/api/notification-preferences", json={"in_app_enabled": True}).status_code == 200
    db = get_session()
    try:
        user_db = db.get(User, user.id)
        create_notification(db, user_db, title="Сделка обновлена", body="Получено согласование")
    finally:
        db.close()
    assert any(x["title"] == "Сделка обновлена" for x in client.get("/api/notifications").json())
    assert client.patch("/api/notification-preferences", json={"in_app_enabled": False}).status_code == 200
    assert client.get("/api/notifications").json() == []


def test_email_notifications_unavailable_without_smtp(client, monkeypatch):
    """Без SMTP_HOST на сервере переключатели «почта»/«недельная сводка» не
    должны выглядеть включаемыми — иначе пользователь ставит галочку, а
    письмо никогда не уйдёт, и никто об этом не узнает (см. CLAUDE.md про
    честную деградацию вместо тихой имитации успеха)."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    _login(client, "no-smtp-launch@firm.ru")
    prefs = client.get("/api/notification-preferences").json()
    assert prefs["email_available"] is False
    r = client.patch("/api/notification-preferences", json={"email_enabled": True})
    assert r.status_code == 400
    r = client.patch("/api/notification-preferences", json={"weekly_digest": True})
    assert r.status_code == 400


def test_saved_assistant_thread(client, monkeypatch):
    _login(client, "assistant-launch@firm.ru")
    monkeypatch.setenv("YANDEX_API_KEY", "key")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "folder")
    monkeypatch.setattr(main, "call_llm", lambda system, user, max_tokens: "Ответ по карточке")
    response = client.post("/api/ask", json={
        "question": "Что важно в этой сделке?", "context": "{}", "mode": "base",
        "context_type": "deal", "context_id": "g1d36d186", "save_thread": True,
    })
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    thread = client.get(f"/api/assistant/threads/{thread_id}").json()
    assert thread["context_type"] == "deal" and thread["context_id"] == "g1d36d186"
    assert [m["role"] for m in thread["messages"]] == ["user", "assistant"]


def test_pdf_export_is_paid_and_branded(client):
    _login(client, "export-free@firm.ru")
    assert client.post("/api/deals/g1d36d186/export", json={}).status_code == 403

    paid_client = TestClient(main.app)
    _login(paid_client, "export-paid@firm.ru")
    db = get_session()
    try:
        user = db.query(User).filter_by(email="export-paid@firm.ru").one()
        user.tier = UserTier.paid
        db.commit()
    finally:
        db.close()
    response = paid_client.post("/api/deals/g1d36d186/export", json={})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_webinars_endpoint_only_returns_published(client):
    db = get_session()
    try:
        if not db.query(Webinar).filter_by(title="Разбор M&A").first():
            db.add(Webinar(title="Разбор M&A", summary="Практический вебинар", published=True))
            db.add(Webinar(title="Черновик", published=False))
            db.commit()
    finally:
        db.close()
    rows = client.get("/api/webinars").json()
    assert any(x["title"] == "Разбор M&A" for x in rows)
    assert all(x["title"] != "Черновик" for x in rows)


def test_launch_ui_contains_requested_changes():
    html = Path("static/index.html").read_text(encoding="utf-8")
    assert "если возможно" in html.lower()
    assert "если уместно" not in html.lower()
    assert "у 180 сделок известно" not in html
    assert "#/materials" in html and "Материалы" in html
    assert 'page==="materials"||page==="webinars"' in html  # старая ссылка #/webinars не должна биться
    assert 'id="selagroup"' in html and "категория консультанта" in html
    assert "advisor-card" in html and "@media(max-width:760px)" in html
    assert "Подписаться на обновления" in html
    assert "Скачать PDF" in html and "Скопировать ссылку" in html
    assert "navigator.share" in html
    assert "fnsChart" in html and "as_of_year" in html
    assert 'data-fnstab="ownership"' in html and "ownershipHtml" in html
    assert "Связи по сделкам" not in html and "companyRelationshipHtml" not in html
    assert "Другие сделки с участием" in html and "openCompanyDealsDialog" in html
    assert "Подробные карточки" not in html and "Также упомина" not in html
    assert "Сравнение компаний" in html and "Добавить к сравнению" in html
    assert "#/compare" in html and "compare-grid" in html and "data-co-compare" in html
    assert 'id="savefeed"' in html and "Подборка сохранена" in html
    assert "Сделки на российском рынке" in html
    assert "Российский рынок сделок" not in html
    assert "Инвестиции и рынок ЦБ" not in html
    assert "Искусственный интеллект" in html
    assert "Показываем этапы сделки, подтверждённые публичными источниками." in html
    assert '<span class="chev">⌄</span>' not in html and '<svg class="chev"' in html
    assert "https://300.pravo.ru/" not in html
    assert "Право-300" not in html
    assert "saveThread:true" in html
    assert "КОМПАС.</span>" not in html
    assert html.count('data-r="advisors"') == 1


def test_fns_normalizers_convert_source_units_and_fields():
    from fns_client import normalize_bo, normalize_egr, normalize_search_results

    search = normalize_search_results({"items": [{"ЮЛ": {
        "ИНН": "7700000001", "ОГРН": "1027700000001",
        "НаимСокрЮЛ": 'ООО "Альфа"', "НаимПолнЮЛ": 'Общество с ограниченной ответственностью "Альфа"',
        "Статус": "Действующая", "АдресПолн": "Москва",
    }}]})
    assert search[0]["inn"] == "7700000001" and search[0]["legal_name"].startswith("Общество")

    egr = normalize_egr({"items": [{"ЮЛ": {
        "ИНН": "7700000001", "ОГРН": "1027700000001", "КПП": "770001001",
        "НаимСокрЮЛ": 'ООО "Альфа"', "Статус": "Действующая",
        "ОснВидДеят": {"Код": "62.01", "Текст": "Разработка программного обеспечения"},
    }}]})
    assert egr["kpp"] == "770001001" and egr["okved_code"] == "62.01"

    reports = normalize_bo({"7700000001": {"2025": {
        "2110": "1500000", "2400": "210000", "1600": "2300000",
        "1300": "900000", "1410": "100000", "1510": "50000",
    }}}, "7700000001")
    assert reports[0]["revenue_rub"] == 1_500_000_000
    assert reports[0]["borrowings_rub"] == 150_000_000


def test_fns_seed_dry_run_does_not_write():
    from pipeline.sync_fns import seed_companies
    db = get_session()
    try:
        before = db.query(Company).count()
        expected = seed_companies(db, dry_run=True)
        after = db.query(Company).count()
        assert expected > 1800
        assert before == after
    finally:
        db.close()


def test_fns_candidate_csv_review_round_trip(tmp_path):
    import csv
    from db.models import LegalEntityCandidate
    from pipeline.review_fns_candidates import export_queue, import_approvals

    db = get_session()
    try:
        company_id = "review-fns-company"
        if not db.get(Company, company_id):
            db.add(Company(id=company_id, name="Компания для проверки"))
            db.flush()
        row = db.query(LegalEntityCandidate).filter_by(company_id=company_id, inn="7700000088").first()
        if not row:
            row = LegalEntityCandidate(
                company_id=company_id, inn="7700000088", ogrn="1027700000088",
                legal_name='ООО "Компания для проверки"', score=0.94,
            )
            db.add(row)
        else:
            row.review_status = "new"
        db.commit()
    finally:
        db.close()

    path = tmp_path / "review.csv"
    assert export_queue(path) >= 1
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for item in rows:
        if item["company_id"] == "review-fns-company" and item["inn"] == "7700000088":
            item["approved"] = "yes"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    assert import_approvals(path) >= 1
    db = get_session()
    try:
        entity = db.query(LegalEntity).filter_by(company_id="review-fns-company", inn="7700000088").one()
        assert entity.match_status == LegalEntityMatchStatus.confirmed
        assert entity.manually_verified is True
    finally:
        db.close()


def test_fns_ownership_normalizer_builds_current_and_historical_snapshots():
    from fns_client import normalize_ownership

    current = {"items": [{"ЮЛ": {
        "ДатаВып": "2026-02-18",
        "Учредители": [{
            "УчрЮЛ": {"НаимСокрЮЛ": 'ООО "Новый участник"', "ИНН": "7700000022"},
            "Доля": {"Процент": "100", "НоминСтоим": "10000"},
        }, {
            "УчрФЛ": {"ФИОПолн": "Бывший Участник", "ИННФЛ": "7700000099"},
            "Доля": {"Процент": "10", "НоминСтоим": "1000"},
            "ДатаОконч": "2023-12-31",
        }],
    }}]}
    changes = {"items": [{"ЮЛ": {"Изменения": {
        "2024-01-01": {"СПВЗ": "Изменение состава участников", "Учредители": [{
            "УчрЮЛ": {"НаимСокрЮЛ": 'ООО "Первый участник"', "ИНН": "7700000011"},
            "Доля": {"Процент": "100", "НоминСтоим": "10000"},
        }]}
    }}}]}
    rows = normalize_ownership(current, changes)
    assert [row["source_kind"] for row in rows] == ["changes", "current"]
    assert rows[0]["owners"][0]["owner_name"] == 'ООО "Первый участник"'
    assert rows[1]["owners"][0]["share_percent"] == 100
    assert len(rows[1]["owners"]) == 1
    assert rows[1]["owners"][0]["owner_name"] != "Бывший Участник"
    assert rows[1]["is_complete"] is True


def test_taxonomy_is_consistent_in_generation_pipeline():
    sources = [
        Path("pipeline/enrich_deals.py"),
        Path("pipeline/collect_deals.py"),
        Path("pipeline/promote_2026.py"),
        Path("pipeline/promote_all.py"),
        Path("pipeline/to_minideals.py"),
        Path("static/data/curated_companies.json"),
    ]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert "Инвестиции и рынок ЦБ" not in text, path
        assert "Фарма и медицина" not in text, path
    assert "Искусственный интеллект" in Path("pipeline/enrich_deals.py").read_text(encoding="utf-8")
    assert "Не определена" in Path("pipeline/promote_2026.py").read_text(encoding="utf-8")


def test_fns_ownership_normalizer_accepts_direct_api_fns_shape():
    """API-ФНС documents УчрЮЛ/УчрФЛ directly inside egr/changes records."""
    from fns_client import normalize_ownership

    current = {"items": [{"ЮЛ": {
        "ДатаВып": "2026-07-29",
        "УчрЮЛ": [{
            "НаимСокрЮЛ": 'ООО "Текущий участник"',
            "ИНН": "7700000033",
            "Процент": "75",
            "СуммаУК": "7500",
        }],
        "УчрФЛ": [{
            "ФИОПолн": "Иванов Иван Иванович",
            "ИННФЛ": "7700000044",
            "Доля": {"Процент": "25", "НоминСтоим": "2500"},
        }],
    }}]}
    changes = {"items": [{"ЮЛ": {"Изменения": {
        "2024-03-01": {
            "УчрЮЛ": {"НаимСокрЮЛ": 'ООО "Исторический участник"', "ИНН": "7700000055"},
            "Процент": "100",
            "СуммаУК": "10000",
            "СПВЗ": "Изменение состава участников",
        }
    }}}]}

    rows = normalize_ownership(current, changes)
    assert len(rows) == 2
    assert rows[0]["owners"][0]["owner_name"] == 'ООО "Исторический участник"'
    assert rows[0]["owners"][0]["share_percent"] == 100
    assert rows[0]["is_complete"] is False
    assert {owner["owner_name"] for owner in rows[1]["owners"]} == {
        'ООО "Текущий участник"', "Иванов Иван Иванович",
    }
    assert sorted(owner["share_percent"] for owner in rows[1]["owners"]) == [25, 75]


def test_company_page_uses_one_compact_deal_section():
    """Карточка компании не возвращается к трём дублирующим огромным блокам."""
    html = Path("static/index.html").read_text(encoding="utf-8")
    assert "companyDealsCompactHtml" in html
    assert "openCompanyDealsDialog" in html
    assert "Другие сделки с участием ${esc(c?c.name" in html
    assert "Упоминания в источниках" in html
    assert "Связи по сделкам" not in html
    assert "Подробные карточки" not in html
    assert "Также упоминается" not in html
