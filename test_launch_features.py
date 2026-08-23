# -*- coding: utf-8 -*-
"""Новые функции запуска: ФНС, алерты, экспорт, вебинары и mobile UI."""
from datetime import date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from db.models import (
    Company, DealSeen, FinancialReport, LegalEntity, LegalEntityMatchStatus,
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
    response = client.post("/api/auth/register",
                            json={"email": email, "password": _TEST_PASSWORD, "full_name": "Тест Тестов"})
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


def test_fns_company_dossier_free_and_paid_access(client, monkeypatch):
    """Проверяет РЕАЛЬНУЮ границу платности — с выключенным FNS_ALL_FREE,
    как она устроена в коде на случай, когда владелец включит её обратно
    (pipeline/COMPANY_FINANCE_BRIEF.md, раздел П6). Сейчас флаг стоит True
    (см. test_fns_all_free_shows_full_history_to_anonymous_visitors ниже) —
    это не отменяет саму границу, она просто временно не применяется."""
    monkeypatch.setattr(main, "FNS_ALL_FREE", False)
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


def test_fns_all_free_shows_full_history_to_anonymous_visitors(client):
    """Текущее временное состояние (FNS_ALL_FREE=True, по просьбе владельца
    22 августа 2026: «давай сначала всё сделаем бесплатно, чтобы я видел как
    работает»). Анонимный посетитель видит ровно то же, что платный —
    полную историю отчётов и событий, без урезания."""
    assert main.FNS_ALL_FREE is True
    _seed_fns_company()
    anonymous = client.get("/api/companies/launch-fns-company/fns").json()
    assert anonymous["access"]["paid"] is True
    assert anonymous["access"]["full_history"] is True
    assert len(anonymous["entities"][0]["reports"]) >= 2
    assert anonymous["entities"][0]["has_more_reports"] is False
    assert len(anonymous["entities"][0]["events"]) >= 4


def test_fns_category_gives_an_honest_reason_instead_of_generic_placeholder(client, monkeypatch):
    """П5 (COMPANY_FINANCE_BRIEF.md): «нашли/не нашли» — не одно состояние.
    Профиль без сопоставленного юрлица, но с решением bank/foreign/state_org
    в реестре, получает СВОЮ причину, а не «ещё не сопоставлено» — та фраза
    подразумевает, что сопоставление ещё случится, а для банка/иностранца
    оно не случится никогда."""
    import main as main_module

    for decision, expected_snippet in (
        ("bank", "Кредитная организация"),
        ("foreign", "Иностранное юридическое лицо"),
        ("state_org", "Государственный орган"),
    ):
        monkeypatch.setattr(main_module, "fns_registry_by_company_id",
                            lambda d=decision: {"launch-fns-category-test": {"decision": d}})
        body = client.get("/api/companies/launch-fns-category-test/fns").json()
        assert body["available"] is False
        assert body["hidden"] is False
        assert body["category"] == decision
        assert expected_snippet in body["reason"], (decision, body["reason"])


def test_fns_person_and_lot_categories_are_hidden_not_empty(client, monkeypatch):
    """person/lot не бывают финансового блока вовсе — hidden=True, а не
    честное пустое состояние с текстом (родня правилу «вкладка без данных
    не рендерится», не «рендерится приглушённой»)."""
    import main as main_module

    for decision in ("person", "lot"):
        monkeypatch.setattr(main_module, "fns_registry_by_company_id",
                            lambda d=decision: {"launch-fns-hidden-test": {"decision": d}})
        body = client.get("/api/companies/launch-fns-hidden-test/fns").json()
        assert body["available"] is False
        assert body["hidden"] is True
        assert body["category"] == decision


def test_fns_profile_without_registry_entry_keeps_the_old_generic_reason(client):
    """Профиль, которого вообще нет в pipeline/fns_registry.py (подавляющее
    большинство базы), не должен внезапно получить category/hidden-эффект —
    старое честное «ещё не сопоставлено» остаётся как было."""
    body = client.get("/api/companies/launch-fns-no-registry-entry-at-all/fns").json()
    assert body["available"] is False
    assert body["hidden"] is False
    assert body["category"] is None
    assert body["reason"] == "Юридическое лицо ещё не сопоставлено с ЕГРЮЛ"


def test_fns_hides_reports_older_than_two_years_on_company_page(client):
    """«Компания сегодня» не должна выглядеть моложе своей отчётности на много
    лет — правило владельца от 18 августа 2026 после жалобы на устаревшие
    2020-2021 годы у банков/АФК «Система». as_of_year (карточка сделки) от
    этого правила не зависит: там нужен именно старый год того периода."""
    company_id = "launch-fns-stale-company"
    this_year = datetime.utcnow().year
    stale_year = this_year - 3  # заведомо старше порога в 2 года
    db = get_session()
    try:
        company = Company(id=company_id, name="Старая отчётность", legal_name='ООО "Старая отчётность"')
        db.add(company); db.flush()
        entity = LegalEntity(
            company_id=company_id, legal_name='ООО "Старая отчётность"', short_name='ООО "Старая отчётность"',
            inn="7700000098", ogrn="1027700000098", status="Действующая",
            match_status=LegalEntityMatchStatus.confirmed, manually_verified=True, is_primary=True,
            fetched_at=datetime.utcnow(), source_updated_at=datetime.utcnow(),
        )
        db.add(entity); db.flush()
        db.add(FinancialReport(legal_entity_id=entity.id, year=stale_year,
                                revenue_rub=500_000_000, net_profit_rub=40_000_000))
        db.commit()
        entity_id = entity.id
    finally:
        db.close()

    body = client.get(f"/api/companies/{company_id}/fns").json()
    entry = body["entities"][0]
    assert entry["reports"] == []
    assert entry["report_years"] == []
    assert entry["stale_latest_year"] == stale_year

    # as_of_year — контекст карточки сделки того же периода: старый год обязан
    # быть виден, правило свежести на историю не распространяется.
    historical = client.get(f"/api/companies/{company_id}/fns?as_of_year={stale_year + 1}").json()
    assert historical["entities"][0]["report_years"] == [stale_year]
    assert historical["entities"][0]["stale_latest_year"] is None

    # Смешанный случай: старый год скрыт, свежий остаётся и не помечен stale.
    db = get_session()
    try:
        db.add(FinancialReport(legal_entity_id=entity_id, year=this_year - 1,
                                revenue_rub=700_000_000, net_profit_rub=60_000_000))
        db.commit()
    finally:
        db.close()
    mixed = client.get(f"/api/companies/{company_id}/fns").json()
    mixed_entry = mixed["entities"][0]
    assert mixed_entry["report_years"] == [this_year - 1]
    assert mixed_entry["stale_latest_year"] is None


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
    monkeypatch.setattr(main, "call_llm", lambda system, user, max_tokens, deadline=None: "Ответ по карточке")
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
    # Фильтр по категории консультанта СНЯТ 4 августа вместе с самими
    # категориями: «С-hi», «К-hi», «mid» — внутренняя разметка, ничем не
    # подтверждённая, и фильтровать по признаку, которого нигде не видно,
    # нельзя. Проверяем обратное тому, что проверялось раньше, — иначе тест
    # держал бы вернувшийся селект.
    assert 'id="selagroup"' not in html, "селект категорий вернулся в разметку"
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


def test_fns_stat_summary_shows_only_purchased_methods_with_remaining_and_period():
    """23 августа 2026: /api/stat открыл, что лимиты тарифа ПО-МЕТОДНЫЕ, не
    общие «3000 на всё» — и что для bo/egr/changes/vyp тип лимита «по
    организациям» (повторный запрос той же организации в течение года
    бесплатен). Сводка должна называть каждый реально используемый метод
    (не весь список из ответа — там есть неиспользуемые check/fl_status и
    т.п.) и не показывать метод, которого нет в тарифе (Лимит=0, как
    bo_file — он и стал причиной сломанной кнопки на карточке компании)."""
    from fns_client import format_stat_summary

    stat = {
        "ДатаНач": "2026-08-17 00:00:00", "ДатаОконч": "2027-08-17 00:00:00",
        "Методы": {
            "search": {"Лимит": "3000", "ТипЛимита": "по запросам", "Истрачено": "482"},
            "bo": {"Лимит": "3000", "ТипЛимита": "по организациям", "Истрачено": "164"},
            "bo_file": {"Лимит": "0", "ТипЛимита": "по запросам", "Истрачено": "0"},
            "fl_status": {"Лимит": "0", "ТипЛимита": "по запросам", "Истрачено": "0"},
        },
    }
    line = format_stat_summary(stat)
    assert "search 482/3000" in line
    assert "bo 164/3000" in line
    assert "bo_file" not in line          # не куплен в тарифе — не показываем как остаток
    assert "fl_status" not in line        # не используется проектом — не шумим им
    assert "2027-08-17" in line


def test_company_finance_tab_never_links_to_the_unpurchased_bo_file_download():
    """23 августа 2026: кнопка «Скачать полную отчётность» вела на метод
    bo_file, которого нет в тарифе (Лимит=0 по /api/stat) — живой клик на
    любом из 150 подтверждённых профилей получал 403 и сырой JSON вместо
    файла. Кнопку сняли; выписка ЕГРЮЛ (метод vyp, он куплен и проверен
    живым запросом) остаётся."""
    src = Path("static/index.html").read_text(encoding="utf-8")
    assert "fns/bo/${" not in src, "ссылка на bo_file-скачивание не должна вернуться на карточку"
    assert "fns/extract?" in src, "рабочая выписка ЕГРЮЛ должна остаться"


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


def test_fns_catalog_exposes_lot_flag_and_deal_count_for_quota_priority():
    """Годовая квота ФНС — 3000 запросов на метод, профилей — почти 1900:
    `--limit` при первом прогоне обязан брать самые важные компании, а не
    первые по порядку файла, и не тратить запрос на `lot` (несколько юрлиц
    под одним именем сделки, ЕГРЮЛ по нему не найти)."""
    from company_catalog import load_company_catalog
    catalog = load_company_catalog()
    assert sum(1 for c in catalog.values() if c.get("lot")) > 10
    by_deals = sorted(catalog.values(), key=lambda c: c.get("deal_count", 0), reverse=True)
    assert by_deals[0]["deal_count"] >= by_deals[-1]["deal_count"]
    assert by_deals[0]["deal_count"] > 5, "самая частая сторона базы обязана иметь много сделок"


def test_fns_match_priority_skips_lots_and_orders_by_deal_count(monkeypatch):
    from pipeline import sync_fns

    fake_catalog = {
        "quiet": {"id": "quiet", "name": "Тихая компания", "lot": False, "deal_count": 1},
        "loud": {"id": "loud", "name": "Громкая компания", "lot": False, "deal_count": 9},
        "bundle": {"id": "bundle", "name": "Компания А и Компания Б", "lot": True, "deal_count": 4},
    }
    monkeypatch.setattr(sync_fns, "load_company_catalog", lambda: fake_catalog)

    seen_order = []

    class FakeClient:
        def search(self, name, **kw):
            seen_order.append(name)
            return {"items": []}

    db = get_session()
    try:
        sync_fns.match_companies(db, FakeClient(), auto_confirm=False, dry_run=True)
    finally:
        db.close()
    assert seen_order == ["Громкая компания", "Тихая компания"], (
        "громкая (deal_count выше) идёт первой, тихий лот вообще не запрашивается")


def test_fns_confirm_by_inn_never_calls_search(monkeypatch):
    """Ручной посев по уже проверенному ИНН (fns_seed_top_companies.py) не
    должен тратить `search` вовсе — только `egr`, иначе экономия смысла не
    имеет: узнавать компанию, которую мы и так знаем по номеру, поиском по
    имени — тот же лишний запрос, которого этот путь и призван избежать."""
    from pipeline.sync_fns import confirm_by_inn

    calls = {"search": 0, "egr": 0}

    class FakeClient:
        def search(self, *a, **kw):
            calls["search"] += 1
            return {"items": []}

        def egr(self, inn):
            calls["egr"] += 1
            return {"items": [{"ЮЛ": {
                "ИНН": inn, "ОГРН": "1027700000001",
                "НаимСокрЮЛ": 'ООО "Тест"', "Статус": "Действующая",
            }}]}

    db = get_session()
    try:
        if not db.get(Company, "confirm-by-inn-test"):
            db.add(Company(id="confirm-by-inn-test", name="Компания для теста ИНН"))
            db.flush(); db.commit()
        confirm_by_inn(db, FakeClient(), "confirm-by-inn-test", "7700000001", dry_run=True)
    finally:
        db.close()
    assert calls == {"search": 0, "egr": 1}


def test_fns_sync_from_registry_confirms_syncs_and_skips_when_fresh(monkeypatch):
    """pipeline/COMPANY_FINANCE_BRIEF.md, П2: --from-registry применяет
    суждение из pipeline/fns_registry.py (кто есть кто) без единого search —
    только egr/bo/changes по уже известному ИНН, и не тратит их повторно,
    пока данные не устарели (REGISTRY_SYNC_STALE_DAYS)."""
    from pipeline import sync_fns

    fake_registry = [
        {"company_id": "registry-sync-test", "decision": "confirmed", "inn": "7700000055",
         "reason": "тест", "date": "2026-08-22"},
        {"company_id": "registry-sync-bank-test", "decision": "bank", "inn": None,
         "reason": "тест — банк, из ФНС не берём", "date": "2026-08-22"},
    ]
    monkeypatch.setattr(sync_fns, "FNS_REGISTRY", fake_registry)

    calls = {"egr": 0, "bo": 0, "changes": 0}

    class FakeClient:
        def egr(self, inn):
            calls["egr"] += 1
            return {"items": [{"ЮЛ": {
                "ИНН": inn, "ОГРН": "1027700000055",
                "НаимСокрЮЛ": 'ООО "Реестр-Тест"', "Статус": "Действующая",
            }}]}

        def bo(self, inn):
            calls["bo"] += 1
            return {inn: {"2025": {"2110": "1000000"}}}

        def changes(self, inn):
            calls["changes"] += 1
            return {"items": []}

    db = get_session()
    try:
        if not db.get(Company, "registry-sync-test"):
            db.add(Company(id="registry-sync-test", name="Реестр-Тест"))
            db.flush(); db.commit()

        stats = sync_fns.sync_from_registry(db, FakeClient(), dry_run=False)
        assert stats == {"confirmed_now": 1, "synced": 1, "skipped_fresh": 0, "errors": 0, "requests": 3}
        assert calls == {"egr": 2, "bo": 1, "changes": 1}  # confirm_by_inn + sync_entity оба читают egr

        entity = db.query(LegalEntity).filter_by(company_id="registry-sync-test").one()
        assert entity.inn == "7700000055"
        assert entity.match_status == LegalEntityMatchStatus.confirmed
        report = db.query(FinancialReport).filter_by(legal_entity_id=entity.id).one()
        assert report.revenue_rub == 1_000_000_000

        # Второй прогон — данные свежие, ни одного запроса.
        calls_before = dict(calls)
        stats2 = sync_fns.sync_from_registry(db, FakeClient(), dry_run=False)
        assert stats2 == {"confirmed_now": 0, "synced": 0, "skipped_fresh": 1, "errors": 0, "requests": 0}
        assert calls == calls_before

        # --force игнорирует свежесть.
        stats3 = sync_fns.sync_from_registry(db, FakeClient(), dry_run=False, force=True)
        assert stats3["synced"] == 1
        assert calls["bo"] == 2
    finally:
        db.close()


def test_fns_sync_from_registry_limit_counts_real_work_not_list_position(monkeypatch):
    """23 августа 2026: `limit` считался срезом списка ДО проверки
    свежести (`confirmed[:limit]`) — стартовый скан прода с limit=30
    навсегда перерабатывал первые 30 строк реестра, которые почти всегда
    уже свежие (skipped_fresh), а партии 2 и дальше не доезжали до прода
    НИ ОДНИМ следующим деплоем. `limit` обязан быть потолком РЕАЛЬНОЙ
    работы: уже свежие записи впереди списка не должны отбирать бюджет у
    новых записей позади него."""
    from pipeline import sync_fns

    fake_registry = [
        {"company_id": "already-fresh-1", "decision": "confirmed", "inn": "7700000101",
         "reason": "т", "date": "2026-08-22"},
        {"company_id": "already-fresh-2", "decision": "confirmed", "inn": "7700000102",
         "reason": "т", "date": "2026-08-22"},
        {"company_id": "already-fresh-3", "decision": "confirmed", "inn": "7700000103",
         "reason": "т", "date": "2026-08-22"},
        {"company_id": "needs-work-1", "decision": "confirmed", "inn": "7700000201",
         "reason": "т", "date": "2026-08-23"},
        {"company_id": "needs-work-2", "decision": "confirmed", "inn": "7700000202",
         "reason": "т", "date": "2026-08-23"},
    ]
    monkeypatch.setattr(sync_fns, "FNS_REGISTRY", fake_registry)

    class FakeClient:
        def egr(self, inn):
            return {"items": [{"ЮЛ": {
                "ИНН": inn, "ОГРН": "10277" + inn[-8:],
                "НаимСокрЮЛ": 'ООО "Тест"', "Статус": "Действующая",
            }}]}

        def bo(self, inn):
            return {inn: {"2025": {"2110": "1000000"}}}

        def changes(self, inn):
            return {"items": []}

    db = get_session()
    try:
        # Идемпотентная подготовка (тесты этого файла делят одну dev-базу
        # между прогонами — тот же приём, что уже используется соседним
        # тестом sync_from_registry чуть выше).
        for row in fake_registry[:3]:
            cid, inn = row["company_id"], row["inn"]
            if not db.get(Company, cid):
                db.add(Company(id=cid, name=cid))
                db.flush()
            entity = db.query(LegalEntity).filter_by(company_id=cid).one_or_none()
            if entity is None:
                db.add(LegalEntity(company_id=cid, inn=inn, legal_name="Тест",
                                   match_status=LegalEntityMatchStatus.confirmed,
                                   fetched_at=datetime.utcnow()))
            else:
                entity.inn = inn
                entity.match_status = LegalEntityMatchStatus.confirmed
                entity.fetched_at = datetime.utcnow()
        db.commit()
        for row in fake_registry[3:]:
            if not db.get(Company, row["company_id"]):
                db.add(Company(id=row["company_id"], name=row["company_id"]))
        db.commit()
        # Записи «нужна работа» должны реально нуждаться в ней — снять
        # подтверждение, если тест уже когда-то прошёл на этой же базе.
        for row in fake_registry[3:]:
            leftover = db.query(LegalEntity).filter_by(company_id=row["company_id"]).one_or_none()
            if leftover is not None:
                db.delete(leftover)
        db.commit()

        stats = sync_fns.sync_from_registry(db, FakeClient(), limit=2, dry_run=False)
        assert stats["skipped_fresh"] == 3, "три уже свежие записи впереди списка должны быть пропущены"
        assert stats["confirmed_now"] == 2, "limit=2 обязан достаться НОВЫМ записям, а не быть исчерпан свежими"
        for cid in ("needs-work-1", "needs-work-2"):
            entity = db.query(LegalEntity).filter_by(company_id=cid).one()
            assert entity.match_status == LegalEntityMatchStatus.confirmed
    finally:
        db.close()


def test_fns_sync_from_registry_ignores_non_confirmed_decisions(monkeypatch):
    """bank/foreign/state_org/person/lot/no_match/brand_needs_inn не несут
    подтверждённого ИНН для ФНС — --from-registry обязан их пропускать, а не
    падать на отсутствующем inn."""
    from pipeline import sync_fns

    fake_registry = [
        {"company_id": "x", "decision": "bank", "inn": None, "reason": "т", "date": "2026-08-22"},
        {"company_id": "y", "decision": "foreign", "inn": None, "reason": "т", "date": "2026-08-22"},
        {"company_id": "z", "decision": "no_match", "inn": None, "reason": "т", "date": "2026-08-22"},
    ]
    monkeypatch.setattr(sync_fns, "FNS_REGISTRY", fake_registry)

    class FakeClient:
        def egr(self, inn):
            raise AssertionError("не должно вызываться для не-confirmed решений")

    db = get_session()
    try:
        stats = sync_fns.sync_from_registry(db, FakeClient(), dry_run=False)
    finally:
        db.close()
    assert stats == {"confirmed_now": 0, "synced": 0, "skipped_fresh": 0, "errors": 0, "requests": 0}


def test_fns_queue_clean_query_name_strips_only_our_own_trailing_disambiguator():
    """23 августа 2026: профиль «Кама» (Атом) заведён под этим именем именно
    чтобы не совпасть по транслитерационному ключу с профилем ЦБК «Кама»
    (см. CLAUDE.md) — но «(Атом)» это НАША пометка, не часть юрлица, и с ней
    поиск ФНС не найдёт ничего. Скобки внутри самого названия (редкость, но
    бывает) не должны обрезаться — паттерн якорен строго на конец строки."""
    from pipeline.fns_unresolved_queue import clean_query_name

    assert clean_query_name("«Кама» (Атом)") == "«Кама»"
    assert clean_query_name("Ильинская больница") == "Ильинская больница"
    assert clean_query_name("ООО «Ромашка (Юг)» (актив)") == 'ООО «Ромашка (Юг)»'


def test_fns_queue_unresolved_companies_sorted_by_freshest_deal_and_skips_covered():
    """П2''/П3'' брифа: очередь — свежие сделки первыми, не по числу сделок.
    Профиль уже в реестре, профиль-лот и подозреваемый профиль-близнец в
    очередь не попадают — им нечего делать среди кандидатов на поиск."""
    from pipeline.fns_unresolved_queue import unresolved_companies

    base = {
        "companies": {
            "cid-old": {"name": "Старая компания"},
            "cid-new": {"name": "Новая компания"},
            "cid-covered": {"name": "Уже в реестре"},
            "cid-lot": {"name": "Лот из двух юрлиц", "lot": True},
            "cid-twin": {"name": "Подозреваемый близнец"},
        },
        "deals": [
            {"buyer": "cid-old", "date": "2020-01-01"},
            {"target": "cid-new", "date": "2026-08-01"},
            {"seller_id": "cid-covered", "date": "2026-08-10"},
            {"buyer": "cid-lot", "date": "2026-08-10"},
            {"target": "cid-twin", "date": "2026-08-10"},
        ],
    }
    registry_idx = {"cid-covered": {"decision": "confirmed"}}
    rows = unresolved_companies(base, registry_idx, exclude={"cid-twin"})
    ids = [r[0] for r in rows]
    assert ids == ["cid-new", "cid-old"]  # свежая сделка (2026) раньше старой (2020)
    assert "cid-covered" not in ids and "cid-lot" not in ids and "cid-twin" not in ids


def test_fns_queue_attempt_single_exact_match_requires_uniqueness_and_active_status():
    """Механика этого шага НАРОЧНО у́же, чем match_companies(auto_confirm=True)
    (0.965 похожести имени без ОКВЭД/региона — на «Арнест» вернул 10
    кандидатов без сигнала, какой из них главный, см. докстринг скрипта):
    подтверждает только когда после поиска остаётся РОВНО один действующий
    результат с точным (не похожим) именем. Два действующих тёзки или один
    ликвидированный результат — не подтверждение."""
    from pipeline.fns_unresolved_queue import attempt_single_exact_match

    class OneExactMatch:
        def search(self, q):
            return {"items": [{"ЮЛ": {
                "ИНН": "7700000010", "НаимСокрЮЛ": 'ООО "Тестовая Компания"',
                "Статус": "Действующее",
            }}]}

    hit = attempt_single_exact_match(OneExactMatch(), "Тестовая компания")
    assert hit == ("7700000010", 'ООО "Тестовая Компания"')

    class TwoHomonyms:
        def search(self, q):
            return {"items": [
                {"ЮЛ": {"ИНН": "7700000011", "НаимСокрЮЛ": 'ООО "Тестовая Компания"', "Статус": "Действующее"}},
                {"ЮЛ": {"ИНН": "7700000012", "НаимСокрЮЛ": 'ООО "Тестовая Компания"', "Статус": "Действующее"}},
            ]}

    assert attempt_single_exact_match(TwoHomonyms(), "Тестовая компания") is None

    class OnlyLiquidated:
        def search(self, q):
            return {"items": [{"ЮЛ": {
                "ИНН": "7700000013", "НаимСокрЮЛ": 'ООО "Тестовая Компания"',
                "Статус": "Находится в стадии ликвидации",
            }}]}

    assert attempt_single_exact_match(OnlyLiquidated(), "Тестовая компания") is None


def test_fns_queue_append_registry_writes_valid_python_without_touching_existing_records(tmp_path):
    """Дописанный блок обязан остаться синтаксически верным Python (файл —
    рабочий код, не только данные) и не задеть уже существующие записи."""
    from pipeline.fns_unresolved_queue import _append_registry

    fixture = tmp_path / "fake_registry.py"
    fixture.write_text(
        'REGISTRY = [\n'
        '    {"company_id": "existing", "decision": "confirmed", "inn": "1234567890",\n'
        '     "reason": "уже было", "date": "2026-08-01"},\n'
        ']\n\n\n'
        'def by_company_id() -> dict[str, dict]:\n'
        '    return {row["company_id"]: row for row in REGISTRY}\n',
        encoding="utf-8",
    )
    _append_registry([("newco", 'ООО «Новая» (тест)', "7700000099", 'ООО "Новая"')], path=str(fixture))

    src = fixture.read_text(encoding="utf-8")
    compile(src, str(fixture), "exec")  # синтаксическая проверка без выполнения
    namespace = {}
    exec(compile(src, str(fixture), "exec"), namespace)
    idx = namespace["by_company_id"]()
    assert idx["existing"]["inn"] == "1234567890"          # старая запись не тронута
    assert idx["newco"]["decision"] == "confirmed"
    assert idx["newco"]["inn"] == "7700000099"


def test_fns_queue_console_message_carries_marker_name_and_link():
    """Маркер `[инн <id>]` в первой строке — за него держится разбор
    ответа в main.py::telegram_webhook (см. докстринг модуля)."""
    from pipeline.fns_unresolved_queue import console_message

    text = console_message("gc2792a44", "АФК «Система»", "2026-06-01")
    assert text.startswith("⚠️ [инн gc2792a44]")
    assert "АФК «Система»" in text
    assert "/#/companies/gc2792a44" in text
    assert "2026-06-01" in text


def test_fns_queue_send_to_console_dry_run_sends_nothing(monkeypatch):
    """Без --write — план печатается, ни один HTTP-запрос не уходит."""
    from pipeline.fns_unresolved_queue import send_queue_to_console
    import sys as _sys
    _sys.path.insert(0, "pipeline/ingest")
    import send_drafts

    monkeypatch.setattr(send_drafts, "send_targets", lambda: ["123"])
    sent = send_queue_to_console([("gtest", "Тест", "2026-08-20")], write=False)
    assert sent == []


def test_fns_queue_send_to_console_without_targets_sends_nothing(monkeypatch):
    """Ни TELEGRAM_REVIEW_GROUP_ID, ни TELEGRAM_REVIEW_CHAT_IDS — консоли
    нет, и это честный отказ, а не попытка отправить в никуда."""
    from pipeline.fns_unresolved_queue import send_queue_to_console
    import sys as _sys
    _sys.path.insert(0, "pipeline/ingest")
    import send_drafts

    monkeypatch.setattr(send_drafts, "send_targets", lambda: [])
    sent = send_queue_to_console([("gtest", "Тест", "2026-08-20")], write=True)
    assert sent == []


def test_fns_queue_stamp_asked_writes_date_on_the_profile(tmp_path, monkeypatch):
    """Штамп `fns_asked` — тот же приём, что `reviewed` на карточке сделки:
    переживает контейнер, потому что пишется прямо в git-файл базы."""
    from pipeline.fns_unresolved_queue import stamp_asked
    import json as _json

    monkeypatch.setenv("FNS_QUEUE_DATE", "2026-08-23")
    fixture = tmp_path / "deals_promoted.json"
    base = {"companies": {"cid-a": {"name": "А"}, "cid-b": {"name": "Б"}}}
    stamp_asked(base, ["cid-a"], path=str(fixture))

    written = _json.loads(fixture.read_text(encoding="utf-8"))
    assert written["companies"]["cid-a"]["fns_asked"] == "2026-08-23"
    assert "fns_asked" not in written["companies"]["cid-b"]


def test_fns_queue_unresolved_companies_skips_already_asked_profiles():
    """Этап 3, П3''': компания со штампом `fns_asked` уже была спрошена в
    консоли — не повторять молчащий вопрос каждый день."""
    from pipeline.fns_unresolved_queue import unresolved_companies

    base = {
        "companies": {
            "cid-new": {"name": "Новая компания"},
            "cid-asked": {"name": "Уже спрошенная", "fns_asked": "2026-08-20"},
        },
        "deals": [
            {"target": "cid-new", "date": "2026-08-20"},
            {"buyer": "cid-asked", "date": "2026-08-21"},
        ],
    }
    ids = [r[0] for r in unresolved_companies(base, registry_idx={}, exclude=set())]
    assert ids == ["cid-new"]


def test_fns_queue_send_one_omits_reply_markup_when_no_keyboard():
    """Сообщение очереди «нужен ИНН» не несёт кнопок (решение — ответ
    текстом, не нажатие) — `reply_markup` не должен уйти в теле запроса
    вовсе (null), как и у обычных уведомлений notification_service."""
    import sys as _sys
    _sys.path.insert(0, "pipeline/ingest")
    import send_drafts

    calls = []

    class _Resp:
        status_code = 200
        def json(self):
            return {"ok": True}

    class _FakeClient:
        def post(self, url, json=None):
            calls.append(json)
            return _Resp()

    ok = send_drafts.send_one(_FakeClient(), "tok", "111", "текст", None)
    assert ok is True
    assert "reply_markup" not in calls[0]

    calls.clear()
    ok = send_drafts.send_one(_FakeClient(), "tok", "111", "текст", {"inline_keyboard": [[]]})
    assert ok is True
    assert calls[0]["reply_markup"] == {"inline_keyboard": [[]]}


def test_fns_notes_parse_inn_requires_exactly_one_bare_number():
    from pipeline.fns_notes_to_registry import parse_inn

    assert parse_inn("ИНН 7736207543") == "7736207543"
    assert parse_inn("7736207543") == "7736207543"
    assert parse_inn("770708389012") == "770708389012"       # 12 знаков — ИП/физлицо
    assert parse_inn("два номера: 7736207543 и 7700000010") is None
    assert parse_inn("телефон +7 999 773 62 07") is None      # не 10-12 цифр подряд
    assert parse_inn("не знаю") is None
    assert parse_inn("") is None


def test_fns_notes_collect_confirms_valid_inn_and_rejects_the_rest():
    """Четыре класса отказа проверены отдельно: профиля нет, уже в реестре,
    в ответе не одно число, контрольная сумма не сходится. Пятый случай —
    честное подтверждение, когда ИНН реальный (Яндекс, известно верный)."""
    from pipeline.fns_notes_to_registry import collect

    companies = {"yandex": {"name": "Яндекс"}, "gknown": {"name": "Уже решено"}}
    registry_idx = {"gknown": {"decision": "no_match"}}
    notes = [
        {"id": 1, "deal_id": "инн~yandex", "edited_text": "7736207543"},
        {"id": 2, "deal_id": "инн~ghost", "edited_text": "7736207543"},
        {"id": 3, "deal_id": "инн~gknown", "edited_text": "7736207543"},
        {"id": 4, "deal_id": "инн~yandex", "edited_text": "не нашёл, не отвечает телефон"},
        {"id": 5, "deal_id": "инн~yandex", "edited_text": "7736207544"},   # искажена цифра
        {"id": 6, "deal_id": "gnote-unrelated", "edited_text": "правка карточки, не ИНН"},
    ]
    ready, rejected = collect(notes, registry_idx, companies)
    assert [(n["id"], cid, inn) for n, cid, inn in ready] == [(1, "yandex", "7736207543")]
    rejected_ids = [n["id"] for n, _cid, _why in rejected]
    assert rejected_ids == [2, 3, 4, 5]           # заметка 6 — не наш префикс, не участвует вовсе


def test_fns_notes_append_registry_writes_valid_python(tmp_path):
    from pipeline.fns_notes_to_registry import append_registry

    fixture = tmp_path / "fake_registry.py"
    fixture.write_text(
        'REGISTRY = [\n'
        '    {"company_id": "existing", "decision": "confirmed", "inn": "1234567890",\n'
        '     "reason": "уже было", "date": "2026-08-01"},\n'
        ']\n\n\n'
        'def by_company_id() -> dict[str, dict]:\n'
        '    return {row["company_id"]: row for row in REGISTRY}\n',
        encoding="utf-8",
    )
    note = {"id": 42, "deal_id": "инн~newco", "edited_text": "7700000099"}
    append_registry([(note, "newco", "7700000099")], path=str(fixture))

    src = fixture.read_text(encoding="utf-8")
    namespace = {}
    exec(compile(src, str(fixture), "exec"), namespace)
    idx = namespace["by_company_id"]()
    assert idx["existing"]["inn"] == "1234567890"
    assert idx["newco"]["decision"] == "confirmed" and idx["newco"]["inn"] == "7700000099"
    assert "42" in idx["newco"]["reason"]


def test_fns_notes_main_write_applies_replies_and_consumes(tmp_path, monkeypatch):
    """Сквозной прогон --write: main() пишет реестр, отвечает реплаем на
    исходное сообщение и помечает заметку применённой — та же цепочка,
    которую read_notes.py уже требует от обычных заметок. `append_registry`
    подменена шпионом, чтобы не трогать боевой pipeline/fns_registry.py —
    её собственная запись уже проверена отдельным тестом на файловом
    фикстуре (test_fns_notes_append_registry_writes_valid_python)."""
    import json as _json
    import sys as _sys
    import pipeline.fns_notes_to_registry as fns_notes
    import read_notes

    data_file = tmp_path / "deals_promoted.json"
    data_file.write_text(_json.dumps({"companies": {"yandex": {"name": "Яндекс"}}}), encoding="utf-8")
    monkeypatch.setattr(fns_notes, "DATA", str(data_file))
    monkeypatch.setattr(fns_notes, "by_company_id", lambda: {})

    monkeypatch.setattr(read_notes, "fetch_notes", lambda: [
        {"id": 9, "deal_id": "инн~yandex", "edited_text": "7736207543",
         "chat_id": "111", "reply_message_id": 777},
    ])
    appended, replied, consumed = [], [], []
    monkeypatch.setattr(fns_notes, "append_registry", lambda ready, path=None: appended.append(ready))
    monkeypatch.setattr(read_notes, "send_reply", lambda nid, text: replied.append((nid, text)) or True)
    monkeypatch.setattr(read_notes, "consume", lambda ids: consumed.extend(ids))
    monkeypatch.setattr(_sys, "argv", ["fns_notes_to_registry.py", "--write"])

    fns_notes.main()

    assert appended and [(cid, inn) for _n, cid, inn in appended[0]] == [("yandex", "7736207543")]
    assert replied and replied[0][0] == 9 and "7736207543" in replied[0][1]
    assert consumed == [9]


def test_fns_notes_main_dry_run_writes_nothing(tmp_path, monkeypatch):
    """Без --write — план виден, ни реестр, ни ответ, ни consume не трогаются
    (тот же принцип «сухой прогон без аргументов», что у остальных скриптов
    pipeline/)."""
    import json as _json
    import sys as _sys
    import pipeline.fns_notes_to_registry as fns_notes
    import read_notes

    data_file = tmp_path / "deals_promoted.json"
    data_file.write_text(_json.dumps({"companies": {"yandex": {"name": "Яндекс"}}}), encoding="utf-8")
    monkeypatch.setattr(fns_notes, "DATA", str(data_file))
    monkeypatch.setattr(fns_notes, "by_company_id", lambda: {})
    monkeypatch.setattr(read_notes, "fetch_notes", lambda: [
        {"id": 9, "deal_id": "инн~yandex", "edited_text": "7736207543",
         "chat_id": "111", "reply_message_id": 777},
    ])
    touched = []
    monkeypatch.setattr(fns_notes, "append_registry", lambda *a, **kw: touched.append("append"))
    monkeypatch.setattr(read_notes, "send_reply", lambda *a, **kw: touched.append("reply"))
    monkeypatch.setattr(read_notes, "consume", lambda *a, **kw: touched.append("consume"))
    monkeypatch.setattr(_sys, "argv", ["fns_notes_to_registry.py"])

    fns_notes.main()
    assert not touched


def test_fns_seed_script_writes_company_row_before_legal_entity(tmp_path):
    """18 августа 2026 первый боевой прогон fns_seed_top_companies.py упал
    на PostgreSQL: `ForeignKeyViolation` — company_id ещё не было строки в
    companies, когда скрипт уже пробовал вставить legal_entities. На
    локальном SQLite это не ловится: там внешние ключи по умолчанию не
    проверяются вовсе, тот же класс дефекта, что уже описан в CLAUDE.md про
    `ALTER TABLE ... IF NOT EXISTS`. Здесь — отдельная SQLite-база с явно
    включёнными внешними ключами (`PRAGMA foreign_keys=ON`), чтобы тест
    воспроизводил именно то ограничение, которое реально сломало прогон."""
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from db.models import Base
    import pipeline.fns_seed_top_companies as seed_mod

    db_path = tmp_path / "fk_check.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def egr(self, inn):
            return {"items": [{"ЮЛ": {
                "ИНН": inn, "ОГРН": "1027700000001",
                "НаимСокрЮЛ": 'ООО "Тест"', "Статус": "Действующая",
            }}]}

    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(seed_mod, "SessionLocal", Session)
        monkeypatch.setattr(seed_mod, "engine", engine)
        monkeypatch.setattr(seed_mod, "ApiFnsClient", FakeClient)
        monkeypatch.setattr(seed_mod, "SEED", {"yandex": ("7736207543", "тест")})
        code = seed_mod.main(["--write"])
    finally:
        monkeypatch.undo()
    assert code == 0, "внешний ключ не должен упасть — company-строка обязана появиться первой"

    from db.models import Company, LegalEntity
    with Session() as db:
        assert db.get(Company, "yandex") is not None
        assert db.query(LegalEntity).filter_by(company_id="yandex").count() == 1


def test_fns_seed_script_never_claims_success_when_every_request_fails(monkeypatch, capsys):
    """18 августа 2026 сам провайдер (api-fns.ru) вернул 403 на все 7 запросов
    первого посевного прогона, а скрипт всё равно напечатал «Записано» —
    выглядело так, будто что-то записалось, хотя не записалось ничего.
    Итоговая строка обязана отличать «0 из N успешно» от настоящей записи,
    и возвращать код завершения, по которому видно, что прогон не удался."""
    import pipeline.fns_seed_top_companies as seed_mod
    from fns_client import ApiFnsError

    class AlwaysFailsClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def egr(self, inn):
            raise ApiFnsError("403 Forbidden (тест)")

    monkeypatch.setattr(seed_mod, "ApiFnsClient", AlwaysFailsClient)
    code = seed_mod.main(["--write"])
    out = capsys.readouterr().out
    assert code != 0
    assert "Успешно: 0 из" in out
    assert "Записано." not in out


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
        # curated_companies.json удалён 3 августа 2026: профили переехали в
        # deals_promoted.json — единый источник данных. Проверяем теперь его.
        Path("static/data/deals_promoted.json"),
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


def test_subscription_actually_reaches_the_subscriber(client):
    """Сквозной путь подписки: оформил — появилась сделка — пришло уведомление.

    Проверяется именно то, что было сломано: подписки сохранялись и
    показывались, но никто никогда не сверял их с новыми сделками, и
    обещание интерфейса «Новые совпадения появятся в уведомлениях» не
    выполнялось ни разу. Тест написан так, чтобы падать на коде до правки:
    без шага рассылки уведомление не появится.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent / "pipeline" / "publish"))
    import notify_subscribers

    user = _login(client, "subscriber@example.com")
    assert client.post("/api/subscriptions",
                       json={"industry": "ИТ и интернет",
                             "min_amount_mln_rub": 1000}).status_code == 200

    fresh = {"id": "test-subscription-deal", "title": "Крупная сделка в ИТ",
             "ind": "ИТ и интернет", "sum": "8,7 млрд ₽"}
    quiet = {"id": "test-subscription-small", "title": "Мелкая сделка в ИТ",
             "ind": "ИТ и интернет", "sum": "200 млн ₽"}
    other = {"id": "test-subscription-other", "title": "Крупная сделка в финансах",
             "ind": "Финансы", "sum": "8,7 млрд ₽"}

    db = get_session()
    try:
        stats = notify_subscribers.notify_new_deals(db, [fresh, quiet, other], {})
        assert stats["created"] == 1, f"ушло {stats['created']} уведомлений вместо одного: {stats}"
        rows = db.query(Notification).filter_by(user_id=user.id).all()
        assert [r.deal_id for r in rows] == ["test-subscription-deal"], \
            "уведомление пришло не о той сделке"
        assert "отрасль" in (rows[0].body or ""), "в уведомлении не сказано, почему оно пришло"
        # Второй прогон по тем же карточкам не должен слать то же самое ещё раз:
        # «уже сообщали» — это существующая строка Notification, а не отдельный
        # файл состояния, который на боевом хосте потерялся бы при деплое.
        again = notify_subscribers.notify_new_deals(db, [fresh, quiet, other], {})
        assert again["created"] == 0 and again["repeat"] == 1, f"повтор не отсечён: {again}"
    finally:
        db.close()


def test_first_deploy_seeds_quietly_and_the_next_one_notifies(client):
    """Сверка подписок на старте сайта: первый прогон молчит, второй сообщает.

    Приток работает в другом облаке и до базы пользователей не достаёт (она во
    внутренней сети хостинга), поэтому сверять подписки может только сам сайт.
    Единственный момент, когда на сайте появляются новые карточки, — деплой
    нового deals_promoted.json, то есть старт процесса.

    Первый прогон обязан МОЛЧАТЬ: пока таблица `deals_seen` пуста, «новыми»
    формально являются все полторы тысячи карточек, и честный ответ «всё»
    означал бы залп уведомлений по всей истории рынка.
    """
    import subscription_feed

    user = _login(client, "deploy-subscriber@example.com")
    # Ключевое слово нарочно уникальное: база тестов общая на весь файл, и
    # подписка «отрасль ИТ» ловила бы заодно подписчика из соседнего теста —
    # счётчик стал бы зависеть от порядка запуска.
    assert client.post("/api/subscriptions",
                       json={"keyword": "Компасдеплойтест"}).status_code == 200

    # Отрасль и сумма подобраны так, чтобы под подписку соседнего теста
    # («ИТ и интернет» от 1000 млн ₽) эти карточки НЕ попадали.
    old = {"id": "test-deploy-old", "title": "Старая сделка Компасдеплойтест",
           "ind": "Логистика", "sum": "Не раскрыта"}
    new = {"id": "test-deploy-new", "title": "Новая сделка Компасдеплойтест",
           "ind": "Логистика", "sum": "Не раскрыта"}

    db = get_session()
    try:
        db.query(DealSeen).delete()
        db.commit()

        first = subscription_feed.scan_new_deals(db, [old], {})
        assert first["seeded"] == 1 and first["created"] == 0, \
            f"первый прогон разбудил подписчика: {first}"

        second = subscription_feed.scan_new_deals(db, [old, new], {})
        assert second["fresh"] == 1, f"новой карточки не заметили: {second}"
        rows = db.query(Notification).filter_by(user_id=user.id).all()
        assert [r.deal_id for r in rows] == ["test-deploy-new"], \
            "уведомление пришло не о той карточке"

        # Перезапуск процесса без новых карточек не шлёт ничего повторно:
        # состояние живёт в базе, а не в файле рядом с кодом, который на
        # хостинге переписывается при каждом деплое.
        third = subscription_feed.scan_new_deals(db, [old, new], {})
        assert third["fresh"] == 0 and third["created"] == 0, \
            f"перезапуск повторил уведомления: {third}"
    finally:
        db.close()


# ==================== Модерация черновиков через Telegram ====================

def _mod_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    monkeypatch.setenv("TELEGRAM_REVIEW_CHAT_IDS", "111, 222")


def test_moderation_button_decision_is_stored_and_served(client, monkeypatch):
    """Кнопка под черновиком -> таблица -> API для рутины публикации.

    Решение принимает человек в Telegram, вебхук приходит на сайт, а применяет
    решение рутина в одноразовом контейнере, которой база сайта недоступна
    (приватная сеть хостинга). Таблица + API — единственный мост между ними.
    """
    _mod_env(monkeypatch)
    r = client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"data": "mod:gtest123:ok", "from": {"id": 111}}})
    assert r.status_code == 200
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gtest123"]
    assert rows and rows[0]["verdict"] == "approve" and rows[0]["decided_by"] == "111"
    # Применённое решение выдаваться больше не должно.
    r = client.post("/api/moderation/decisions/consume",
                    json={"token": "тайна", "ids": [rows[0]["id"]]})
    assert r.json()["consumed"] == 1
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    assert not [d for d in r.json()["decisions"] if d["deal_id"] == "gtest123"]


def test_milestone_button_decision_carries_the_tilde_separated_id(client, monkeypatch):
    """Раздел A (22 августа): кнопка «пост в канал»/«без поста» под вехой
    несёт `deal_id~kind` в callback_data — регэксп в main.py обязан принять
    `~` (расширен вместе с `[\\w-]`), а решение в таблице обязано сохранить
    ИМЕННО эту составную строку — send_telegram.py режет её сам, main.py её
    не разбирает."""
    _mod_env(monkeypatch)
    r = client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"data": "mod:gmru-nspk-privatization~approval:post_ok",
                            "from": {"id": 111}}})
    assert r.status_code == 200
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gmru-nspk-privatization~approval"]
    assert rows and rows[0]["verdict"] == "post_yes"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_moderation_reply_with_text_overrides_the_post(client, monkeypatch):
    """Ответ на сообщение-черновик с текстом = «опубликовать вот с этим текстом».

    Личный чат с ботом: chat.id и from.id у Telegram совпадают, но проверка
    обязана идти по from.id (отправитель), а не по chat.id (куда упало
    сообщение) — иначе следующий тест на группе не смог бы отличить
    «разрешить всем» от «не разрешить никому».
    """
    _mod_env(monkeypatch)
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 222}, "from": {"id": 222}, "text": "Наш вариант поста",
                     "reply_to_message": {"text": "[черновик gtest456]\nПроект поста…"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gtest456"]
    assert rows and rows[0]["edited_text"] == "Наш вариант поста"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_moderation_reply_in_a_shared_group_checks_the_sender_not_the_group(client, monkeypatch):
    """Владелец и партнёр обсуждают черновики в общей группе — а не в личке.

    В группе `chat.id` один на всех участников (сама группа), а `from.id` —
    личный id того, кто написал. Проверка по chat.id в группе либо пустила бы
    ЛЮБОГО участника группы (chat.id совпал бы с «разрешённым» случайно), либо
    не пустила бы НИКОГО (chat.id группы никогда не совпадает с личными id из
    TELEGRAM_REVIEW_CHAT_IDS) — оба исхода одинаково сломаны. Правильная
    проверка идёт по from.id и не зависит от того, где физически идёт разговор.
    """
    _mod_env(monkeypatch)
    GROUP_CHAT_ID = -1001234567890  # id группы — Telegram делает их отрицательными
    # Партнёр (id 222, входит в TELEGRAM_REVIEW_CHAT_IDS) пишет в общей группе.
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": GROUP_CHAT_ID}, "from": {"id": 222},
                     "text": "Публикуем с моей правкой",
                     "reply_to_message": {"text": "[черновик gtest-group]\nПроект поста…"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gtest-group"]
    assert rows, "решение участника группы, у которого есть право, потеряно"
    assert rows[0]["edited_text"] == "Публикуем с моей правкой"
    assert rows[0]["decided_by"] == "222", "записан не тот, кто фактически ответил"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})

    # Посторонний участник той же группы (не входит в TELEGRAM_REVIEW_CHAT_IDS)
    # решений оставлять не может, хотя chat.id у него тот же самый.
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": GROUP_CHAT_ID}, "from": {"id": 999},
                     "text": "А давайте я тоже решу",
                     "reply_to_message": {"text": "[черновик gtest-group-2]\nПроект поста…"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    assert not [d for d in r.json()["decisions"] if d["deal_id"] == "gtest-group-2"]


def test_moderation_rejects_strangers_and_bad_tokens(client, monkeypatch):
    """Право решать — только у владельца и партнёра; API — только с токеном.

    Бота может найти кто угодно: нажатая чужим человеком кнопка не должна
    публиковать карточки.
    """
    _mod_env(monkeypatch)
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"data": "mod:gstranger:ok", "from": {"id": 999}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    assert not [d for d in r.json()["decisions"] if d["deal_id"] == "gstranger"]
    assert client.get("/api/moderation/decisions", params={"token": "чужой"}).status_code == 404
    # Без настроенного секрета мост закрыт совсем, а не открыт всем.
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET")
    monkeypatch.delenv("MODERATION_TOKEN", raising=False)
    assert client.get("/api/moderation/decisions", params={"token": ""}).status_code == 404


def test_approve_publishes_on_decision_or_silence_and_respects_hold():
    """Три исхода модерации: решение, молчание сутки, «придержать».

    Молчание — согласие: немой шаг, который держит весь поток, у нас уже был
    (тормоз E9), второй раз те же грабли не берём.
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    fresh = (now - timedelta(hours=2)).isoformat(timespec="seconds")
    stale = (now - timedelta(hours=30)).isoformat(timespec="seconds")
    # `reviewed` стоит у всех, кроме a7: с 9 августа НЕПРОЧИТАННАЯ карточка не
    # выходит по молчанию — черновик собран из заголовка, и публиковать его
    # «как есть» значит выпускать каркасные дефекты (см. approve.plan_actions).
    cards = [
        {"id": "a1", "title": "решили опубликовать", "draft_sent": True, "pending_since": fresh,
         "reviewed": "2026-08-09"},
        {"id": "a2", "title": "решили придержать",   "draft_sent": True, "pending_since": fresh,
         "reviewed": "2026-08-09"},
        {"id": "a3", "title": "молчание сутки",      "draft_sent": True, "pending_since": stale,
         "reviewed": "2026-08-09"},
        {"id": "a4", "title": "ещё ждём",            "draft_sent": True, "pending_since": fresh,
         "reviewed": "2026-08-09"},
        {"id": "a5", "title": "придержана раньше",   "draft_sent": True, "pending_since": stale,
         "held": True, "reviewed": "2026-08-09"},
        # Черновик, который никому не разослали, по таймауту НЕ публикуется:
        # молчание — согласие только того, кто сообщение получил.
        {"id": "a6", "title": "не рассылался",       "pending_since": stale,
         "reviewed": "2026-08-09"},
        # А этот разослан и отмолчался сутки, но НЕ ПРОЧИТАН против источника —
        # и потому тоже ждёт. Владелец 9 августа: «косячные карточки не должны
        # появляться, пока не изучена статья».
        {"id": "a7", "title": "не прочитана",        "draft_sent": True, "pending_since": stale},
    ]
    decisions = [
        {"deal_id": "a1", "verdict": "approve", "edited_text": "текст владельца"},
        {"deal_id": "a2", "verdict": "hold"},
    ]
    publish, hold, wait, discard = approve.plan_actions(cards, decisions, now)
    assert {c["id"] for c, _o, _w in publish} == {"a1", "a3"}
    assert next(o for c, o, _ in publish if c["id"] == "a1") == "текст владельца"
    assert {c["id"] for c, _w in hold} == {"a2"}
    assert {c["id"] for c, _w in wait} == {"a4", "a5", "a6", "a7"}
    # Решение человека сильнее: прочитанность требуется только для молчания.
    assert "не прочитана" in next(w for c, w in wait if c["id"] == "a7")


def test_webhook_subscribes_to_button_clicks_not_only_messages():
    """Забыть callback_query в ALLOWED_UPDATES — значит зарегистрировать вебхук,
    на который кнопки молча не доходят: Telegram их просто не шлёт, если тип
    не в списке, а «зарегистрировано» при этом печатается как успех. Ровно
    так и было до 5 августа: модерация написана целиком, а её кнопки были бы
    невидимы боту, потому что регистрация вебхука просила только 'message'.
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/publish")))
    import setup_telegram_webhook as w
    assert "callback_query" in w.ALLOWED_UPDATES
    assert "message" in w.ALLOWED_UPDATES


def test_send_targets_prefers_the_shared_group_over_personal_dms(monkeypatch):
    """TELEGRAM_REVIEW_GROUP_ID — куда слать; TELEGRAM_REVIEW_CHAT_IDS — кто решает.

    Это разные переменные с разным смыслом, и перепутать их легко: если бы
    отправка шла по группе, а авторизация проверялась бы тоже по группе,
    ответ любого её участника засчитывался бы за решение — ровно тот баг,
    который поймал предыдущий тест на уровне вебхука. Здесь проверяется
    только выбор адреса отправки.
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import send_drafts
    monkeypatch.setenv("TELEGRAM_REVIEW_CHAT_IDS", "111, 222")
    monkeypatch.delenv("TELEGRAM_REVIEW_GROUP_ID", raising=False)
    assert send_drafts.send_targets() == ["111", "222"]
    monkeypatch.setenv("TELEGRAM_REVIEW_GROUP_ID", "-1001234567890")
    assert send_drafts.send_targets() == ["-1001234567890"]
    # Список авторизованных решать при этом не меняется — это отдельная величина.
    assert send_drafts.reviewers() == ["111", "222"]


def test_bot_answers_bare_start_and_help(client, monkeypatch):
    """Голый «/start» раньше не делал НИЧЕГО и молчал.

    Человек писал боту и получал тишину, неотличимую от поломки: ни ответа, ни
    ошибки. Тот же класс, что E9 — отсутствие ошибки читается как успех.
    """
    _mod_env(monkeypatch)
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 111}, "from": {"id": 111}, "text": "/start"}})
    assert sent, "«/start» остался без ответа"
    method, body = sent[0]
    assert method == "sendMessage"
    # Ответ объясняет, ЧТО человек может сделать, а не просто здоровается.
    assert "опубликовать" in body["text"].lower()
    # И показывает это кнопками: текстом непонятно, что вообще можно нажать.
    assert body.get("reply_markup", {}).get("inline_keyboard")


def test_bot_queue_command_survives_the_group_suffix(client, monkeypatch):
    """В группе Telegram шлёт «/queue@compass_bot», а не «/queue».

    Правило, написанное под личный чат, в группе молча не срабатывает: команда
    отправлена, бот молчит, причина невидима. Суффикс обязателен к отрезанию.
    """
    _mod_env(monkeypatch)
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": -1001234567890}, "from": {"id": 222},
                     "text": "/queue@compass_bot"}})
    assert sent, "команда с суффиксом бота осталась без ответа"
    text = sent[0][1]["text"].lower()
    assert "на проверке" in text or "очередь пуста" in text

    # Посторонний в той же группе состав очереди не получает.
    sent.clear()
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": -1001234567890}, "from": {"id": 999}, "text": "/queue"}})
    assert sent and "только владельцу и партнёру" in sent[0][1]["text"]


def test_queue_report_shows_three_console_blocks():
    """/queue говорит на языке трёх типов сообщений консоли.

    До 5 августа сырьё показывалось строкой «кнопкой не решаются» и жило только
    файлом в git. По решению владельца оно теперь решается кнопками под своим
    сообщением (⚠️), поэтому сводка обязана считать его ЖДУЩИМ решения, а не
    справочным, — и отдельно от карточек предпросмотра (🗂📣): у них разные
    правила молчания (карточки по молчанию выходят, сырьё — никогда).
    """
    report = main._queue_report()
    assert "🗂📣" in report or "Очередь пуста" in report
    if "⚠️" in report:
        assert "ждут вашего слова" in report.lower()
        assert "кнопками" in report.lower()


def test_post_no_is_a_modifier_and_does_not_hold_the_card():
    """«Без поста» — модификатор канала, а не вердикт по карточке.

    Старый план считал «любой не-approve вердикт» придержанием: post_no
    остановил бы публикацию карточки на сайт, хотя человек сказал ровно
    обратное — «карточку выпускай, канал промолчи».
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    stale = (now - timedelta(hours=30)).isoformat(timespec="seconds")
    cards = [{"id": "p1", "title": "карточка без поста", "draft_sent": True,
              "pending_since": stale, "reviewed": "2026-08-09"}]
    decisions = [{"deal_id": "p1", "verdict": "post_no", "created_at": "x"}]
    publish, hold, wait, discard = approve.plan_actions(cards, decisions, now)
    assert not hold, "post_no придержал карточку — это модификатор, а не вердикт"
    assert {c["id"] for c, _o, _w in publish} == {"p1"}, "таймаут молчания должен сработать"
    # …а сам модификатор читается отдельной выборкой.
    assert approve.last_by_deal(decisions, approve.POST_VERDICTS)["p1"]["verdict"] == "post_no"


def test_raw_drafts_need_a_button_and_never_publish_on_silence():
    """Сырьё решается только кнопкой: молчание не делает его сделкой.

    Ворота эти черновики уже не пропустили; таймаут «молчание — согласие»
    существует только для карточек, ПРОШЕДШИХ ворота.
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    drafts = [{"draft_id": "d1", "title": "взять"},
              {"draft_id": "d2", "title": "бросить"},
              {"draft_id": "d3", "title": "молчание — ничего не происходит"}]
    decisions = [{"deal_id": "d1", "verdict": "take"},
                 {"deal_id": "d2", "verdict": "drop"}]
    take, drop = approve.plan_raw(drafts, decisions)
    assert [d["draft_id"] for d in take] == ["d1"]
    assert [d["draft_id"] for d in drop] == ["d2"]


def test_plan_raw_skips_a_draft_already_recorded_as_decided():
    """Решение, уже применённое и записанное в `decided_raw`, не применяется
    повторно — даже если сайт всё ещё считает его «живым».

    Это и есть предохранитель от Wegosty 21 августа: `--consume` теперь
    отдельный шаг ПОСЛЕ git push, а значит между `--write` и подтверждением
    сайту есть окно, где решение локально уже применено, а сайт ещё не
    знает об этом. Без проверки `decided_raw` следующий прогон увидел бы то
    же «живое» решение и создал бы ВТОРУЮ карточку того же черновика —
    `to_card()` каждый раз генерирует новый случайный id, второй раз не
    заметит, что первый уже был."""
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    drafts = [{"draft_id": "d1", "title": "уже применено"}]
    decisions = [{"deal_id": "d1", "verdict": "take"}]
    take, drop = approve.plan_raw(drafts, decisions, decided_raw={"d1": "take"})
    assert not take and not drop, "решение уже в decided_raw — применять снова нельзя"
    # без decided_raw (как раньше) оно бы прошло — проверяем, что тест не
    # проходит просто потому, что данные сломаны
    take2, _ = approve.plan_raw(drafts, decisions, decided_raw={})
    assert [d["draft_id"] for d in take2] == ["d1"]


def test_approve_main_deduplicates_the_same_raw_draft_across_hold_files(tmp_path, monkeypatch):
    """Один и тот же черновик, перенесённый в НЕСКОЛЬКО дневных hold-файлов
    (он там лежит, пока по нему нет решения), не должен породить несколько
    карточек на одно решение «в работу».

    Ровно так родились три карточки-близнеца 21 августа
    (g855e50b1/gf544dd13/g5cba276f) из одного и того же draft_id d59961733,
    лежавшего в трёх дневных файлах сразу — `plan_raw` видел его три раза
    в объединённом списке `raw_all`."""
    import json
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    import promote
    import send_drafts
    # Взятый черновик рассылается в консоль сразу — не тот путь, который
    # проверяет этот тест; подменяем на заглушку, чтобы не задеть реальные
    # static/data/*.json (send_drafts.py считает свои ROOT/DATA/PENDING
    # независимо от approve.py, монкипатч ROOT/DATA/PENDING его не коснётся).
    monkeypatch.setattr(send_drafts, "main", lambda write=False: 0)

    hold_dir = tmp_path / "data" / "inbox" / "hold"
    hold_dir.mkdir(parents=True)
    draft = {"draft_id": "dup1", "title": "Один и тот же черновик",
             "date": "2026-08-01", "src": [["Источник", "https://example.invalid/x"]],
             "sum": None, "type": "Инвестиция", "status": None, "events": [],
             "buyer_name": None, "asset": "Тест", "seller": None, "ind": "ИТ и интернет"}
    for day in ("2026-08-18", "2026-08-19", "2026-08-21"):
        (hold_dir / ("%s.json" % day)).write_text(
            json.dumps({"drafts": [draft]}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(approve, "ROOT", str(tmp_path))
    monkeypatch.setattr(approve, "PENDING", str(tmp_path / "pending.json"))
    monkeypatch.setattr(approve, "DATA", str(tmp_path / "deals.json"))
    monkeypatch.setattr(promote, "STATE", str(tmp_path / "moderation_state.json"))
    (tmp_path / "pending.json").write_text(json.dumps({"cards": []}), encoding="utf-8")
    (tmp_path / "deals.json").write_text(
        json.dumps({"deals": [], "companies": {}}), encoding="utf-8")
    monkeypatch.setattr(approve, "fetch_decisions",
                        lambda: ([{"deal_id": "dup1", "verdict": "take", "id": 1}], None))

    approve.main(write=True)

    pending = json.loads((tmp_path / "pending.json").read_text(encoding="utf-8"))
    assert len(pending["cards"]) == 1, (
        "один draft_id в трёх hold-файлах породил %d карточек вместо одной"
        % len(pending["cards"]))


def test_webhook_routes_raw_and_post_buttons(client, monkeypatch):
    """Кнопки трёх типов сообщений дают три разных класса вердиктов."""
    _mod_env(monkeypatch)
    for data, verdict in (("mod:d9тест:take", "take"), ("mod:d9тест2:drop", "drop"),
                          ("mod:g9тест:post_no", "post_no")):
        client.post("/api/telegram/webhook/тайна", json={
            "callback_query": {"data": data.replace("тест", "test"),
                                "from": {"id": 111}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    got = {d["deal_id"]: d["verdict"] for d in r.json()["decisions"]}
    assert got.get("d9test") == "take" and got.get("d9test2") == "drop"
    assert got.get("g9test") == "post_no"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна",
                      "ids": [d["id"] for d in r.json()["decisions"]]})


def test_reply_to_card_message_becomes_a_note_not_a_publication(client, monkeypatch):
    """Ответ на [карточка <id>] — заметка для рутины, а не команда публиковать.

    Заметка применяется через review.py с его проверками цитат; будь она
    вердиктом approve, любой комментарий («дата какая-то странная») публиковал
    бы карточку немедленно.
    """
    _mod_env(monkeypatch)
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 111}, "from": {"id": 111},
                     "text": "дата не та — в источнике сказано 4 мая",
                     "reply_to_message": {"text": "🗂 [карточка gnote1] — НА САЙТ"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gnote1"]
    assert rows and rows[0]["verdict"] == "note"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_note_reply_is_acked_instantly_and_carries_a_reply_target(client, monkeypatch):
    """Раздел C MILESTONES_BRIEF.md (22 августа): заметка получает мгновенное
    подтверждение прямо в исходном сообщении («— 💬 Заметка принята»), а
    решение несёт chat_id/reply_message_id — иначе рутине нечем ответить
    реплаем позже (read_notes.py --reply). До этого заметка тонула молча:
    второй человек в группе не видел, принята ли она вообще.
    """
    _mod_env(monkeypatch)
    calls = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: calls.append((method, kw)) or {"ok": True})
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 111}, "from": {"id": 111, "first_name": "Борис"},
                     "text": "это отдельная веха, а не новая сделка",
                     "reply_to_message": {"message_id": 777,
                                          "text": "📌 [карточка gnote2] — НА САЙТ"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gnote2"]
    assert rows and rows[0]["verdict"] == "note"
    # Мост для рутины: без этих двух полей read_notes.py --reply ответить не сможет.
    assert rows[0]["chat_id"] == "111"
    assert rows[0]["reply_message_id"] == 777
    # Мгновенное подтверждение — штамп в ТО ЖЕ сообщение, editMessageText,
    # не отдельное новое сообщение (которое легко потерять среди прочих).
    edits = [kw for method, kw in calls if method == "editMessageText"]
    assert edits, "заметка не получила мгновенного подтверждения"
    assert edits[0]["message_id"] == 777
    assert "Заметка принята" in edits[0]["text"] and "Борис" in edits[0]["text"]
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_reply_to_inn_queue_message_becomes_a_namespaced_note(client, monkeypatch):
    """Этап 3, П3''': ответ на [инн <id компании>] — заметка, а deal_id несёт
    префикс «инн~», а не голый id компании. Семь id в базе уже совпадают
    между сделками и компаниями (citibank и другие кураторские слаги) — без
    префикса заметка о номере ИНН могла бы быть прочитана как заметка о
    карточке сделки с тем же id."""
    _mod_env(monkeypatch)
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 111}, "from": {"id": 111},
                     "text": "7740000076",
                     "reply_to_message": {"text": "⚠️ [инн citibank] — НУЖЕН ИНН"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "инн~citibank"]
    assert rows and rows[0]["verdict"] == "note"
    assert rows[0]["edited_text"] == "7740000076"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_approve_reply_does_not_carry_a_note_reply_target(client, monkeypatch):
    """Только заметки (verdict='note') несут chat_id/reply_message_id —
    решению approve отвечать реплаем не нужно, оно уже подтверждается штампом
    у кнопок (_mark_decided). Смешивать нельзя: иначе рутина попытается
    ответить реплаем и на публикацию поста тоже, что не входит в контракт."""
    _mod_env(monkeypatch)
    monkeypatch.setattr(main.notification_service, "tg_api", lambda *a, **kw: {"ok": True})
    client.post("/api/telegram/webhook/тайна", json={
        "message": {"chat": {"id": 222}, "from": {"id": 222},
                     "text": "Наш вариант поста",
                     "reply_to_message": {"message_id": 888,
                                          "text": "[черновик gnote3]\nПроект поста…"}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    rows = [d for d in r.json()["decisions"] if d["deal_id"] == "gnote3"]
    assert rows and rows[0]["verdict"] == "approve"
    assert rows[0]["chat_id"] is None and rows[0]["reply_message_id"] is None
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна", "ids": [rows[0]["id"]]})


def test_discard_kills_the_card_and_beats_the_silence_timeout():
    """«Выкинуть» сильнее и «придержать», и таймаута молчания.

    Просьба владельца 6 августа: нероссийский контур и не-M&A не «придержать
    навечно», а убрать совсем. Критично, чтобы discard побеждал таймаут: без
    этого выкинутая карточка с истёкшими сутками всё равно ушла бы на сайт.
    """
    import sys
    sys.path.insert(0, str(Path("pipeline/ingest")))
    import approve
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    stale = (now - timedelta(hours=48)).isoformat(timespec="seconds")
    cards = [{"id": "x1", "title": "выкинутая, сутки прошли",
              "draft_sent": True, "pending_since": stale}]
    decisions = [{"deal_id": "x1", "verdict": "discard"}]
    publish, hold, wait, discard = approve.plan_actions(cards, decisions, now)
    assert not publish and not hold
    assert {c["id"] for c, _w in discard} == {"x1"}


def test_webhook_discard_button_and_edit_hint(client, monkeypatch):
    """🗑 пишет вердикт discard; ✏️ — только подсказка, НЕ решение."""
    _mod_env(monkeypatch)
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"data": "mod:gdel1:discard", "from": {"id": 111}}})
    client.post("/api/telegram/webhook/тайна", json={
        "callback_query": {"data": "mod:gdel2:edit", "from": {"id": 111}}})
    r = client.get("/api/moderation/decisions", params={"token": "тайна"})
    got = {d["deal_id"]: d["verdict"] for d in r.json()["decisions"]}
    assert got.get("gdel1") == "discard"
    assert "gdel2" not in got, "кнопка «изменить» не должна оставлять вердикт"
    client.post("/api/moderation/decisions/consume",
                json={"token": "тайна",
                      "ids": [d["id"] for d in r.json()["decisions"]]})


# ---------- панель основателей и меню бота (9 августа 2026) ----------

def test_ops_dashboard_is_closed_without_the_token(client):
    """Состав очереди и незаконченная работа — не для публичного показа."""
    assert client.get("/ops").status_code == 404
    assert client.get("/ops?token=неверный").status_code == 404
    assert client.get("/api/ops/summary").status_code == 404


def test_ops_dashboard_opens_with_the_token(client, monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    r = client.get("/ops?token=тайна")
    assert r.status_code == 200
    assert "панель основателей" in r.text
    # Подписи называют МНОЖЕСТВО, а не только величину (урок CLAUDE.md).
    assert "сделок на сайте" in r.text
    assert "выйдут сами в течение суток" in r.text


def test_ops_summary_counts_the_same_numbers_as_the_page(client, monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "тайна")
    n = client.get("/api/ops/summary?token=тайна").json()
    for key in ("deals", "companies", "added_week", "queue_soon", "queue_unread", "queue_held",
                "unread", "from_ingest", "thin_2026", "published"):
        assert isinstance(n[key], int), key
    assert n["deals"] > 1000, "база должна быть непустой"
    assert n["unread"] <= n["from_ingest"]


def test_ops_week_counter_ignores_bulk_import_days(monkeypatch):
    """«Добавлено за неделю» обязано считать приток, а не разовый импорт: в
    день переноса архива приезжают сотни карточек, и счётчик показывал бы
    бурный рост рынка вместо нашей же заливки (урок CLAUDE.md про метку
    «новое»). День с более чем 30 карточками — импорт, а не новости."""
    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()
    bulk_day = (today - timedelta(days=2)).isoformat()
    drip_day = (today - timedelta(days=1)).isoformat()
    fake = {"deals": [{"id": "b%d" % i, "added": bulk_day} for i in range(50)]
                     + [{"id": "d%d" % i, "added": drip_day} for i in range(3)],
            "companies": {}, "telegram_posts": {}}

    def fake_read(path, default):
        return fake if "deals_promoted" in path else {"cards": []}

    monkeypatch.setattr(main, "_read_json", fake_read)
    n = main._ops_numbers()
    assert n["added_week"] == 3, "день с 50 карточками — импорт, его считать нельзя"


def test_bot_start_offers_buttons_instead_of_a_wall_of_text():
    """Голый текст не показывает, что вообще можно нажать: команду приходилось
    помнить наизусть."""
    menu = main._bot_menu()["inline_keyboard"]
    data = [b["callback_data"] for row in menu for b in row]
    # Кнопки ведут туда, где можно РЕШАТЬ, а не только смотреть: очередь,
    # придержанное и сомнительные приходят карточками со своими кнопками.
    assert "show:soon" in data and "show:held" in data and "show:raw" in data
    assert "show:unread" in data
    assert "menu:stats" in data
    for row in menu:
        for button in row:
            assert button["text"].strip(), "кнопка без подписи"


def test_bot_help_speaks_to_a_partner_not_to_a_developer():
    """Справку читает партнёр: никаких наших терминов и кодов бэклога."""
    text = main.BOT_HELP.lower()
    for jargon in ("g7", "pending", "from_ingest", "промоут", "драфт", "eco", "bulk"):
        assert jargon not in text, jargon
    assert "опубликовать" in text and "придержать" in text


def test_stats_report_is_readable_russian():
    """Сводка в боте — те же цифры, что на панели, но словами."""
    text = main._stats_report()
    assert "Сделок на сайте" in text and "Вы придержали" in text
    for jargon in ("G7", "pending", "from_ingest", "thin_2026"):
        assert jargon not in text


def test_queue_buttons_send_actionable_cards_not_a_plain_list(monkeypatch, tmp_path):
    """Список без кнопок — тупик: увидел и ничего не можешь сделать.

    Владелец 9 августа: «я так и не понял, как проверять те, которые
    придержаны». Первая версия присылала перечисление заголовков; теперь
    каждая карточка приходит своим сообщением с рабочими кнопками.
    """
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    monkeypatch.setattr(main, "_read_json", lambda path, default: {
        "cards": [{"id": "gh1", "title": "Придержанная сделка", "held": True,
                   "buyer_name": "«Покупатель»", "sum": "1 млрд ₽"},
                  {"id": "gs1", "title": "Выйдет сама", "buyer_name": "«Другой»",
                   "reviewed": "2026-08-01"}],
    } if "pending" in path else default)

    main._send_queue_batch(-100, "held")
    buttons = [kw.get("reply_markup") for _m, kw in sent if kw.get("reply_markup")]
    assert buttons, "придержанные пришли без единой кнопки"
    data = [b["callback_data"] for row in buttons[0]["inline_keyboard"] for b in row]
    # Полный набор из четырёх — тот же, что в исходном сообщении при первом
    # черновике (send_drafts.card_keyboard). Раньше /queue урезал до двух
    # (ok/discard для held, hold/discard для soon) — владелец 10 августа не
    # нашёл кнопку «Опубликовать» у карточки, которая скоро выйдет сама.
    assert data == ["mod:gh1:ok", "mod:gh1:hold", "mod:gh1:edit", "mod:gh1:discard"], data
    # Заголовок и факты видны прямо в сообщении — решать можно не открывая сайт.
    card_text = [kw["text"] for _m, kw in sent if "gh1" in kw.get("text", "")][0]
    assert "Придержанная сделка" in card_text and "1 млрд ₽" in card_text

    sent.clear()
    main._send_queue_batch(-100, "soon")
    kb = [kw.get("reply_markup") for _m, kw in sent if kw.get("reply_markup")][0]
    data = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
    assert data == ["mod:gs1:ok", "mod:gs1:hold", "mod:gs1:edit", "mod:gs1:discard"], data


def test_unread_card_is_not_counted_as_soon(monkeypatch):
    """«Скоро выйдет» и «ждёт прочтения» — разные утверждения о карточке.

    До 18 августа «soon» значило просто «не придержана» — и непрочитанная
    карточка час за часом отчитывалась как «выйдет сама», хотя молчание её
    никогда не публикует (approve.py, `plan_actions`): «Крупный комплекс в
    Ленобласти» и допэмиссия «М.видео» простояли так больше суток без
    единого изменения в отчёте, и владелец не понимал, что вообще происходит.
    """
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append((method, kw)) or {"ok": True})
    monkeypatch.setattr(main, "_read_json", lambda path, default: {
        "cards": [{"id": "gu1", "title": "Ещё не прочитана", "buyer_name": "«Компания»"},
                  {"id": "gs1", "title": "Прочитана, ждёт таймаута",
                   "buyer_name": "«Другая»", "reviewed": "2026-08-01"}],
    } if "pending" in path else default)

    assert main._send_queue_batch(-100, "soon") == 1
    only_sent = [kw["text"] for _m, kw in sent if "gs1" in kw.get("text", "")]
    assert only_sent and "gu1" not in "".join(kw["text"] for _m, kw in sent)

    sent.clear()
    assert main._send_queue_batch(-100, "unread") == 1
    head = [kw["text"] for _m, kw in sent if "Ждут прочтения" in kw.get("text", "")]
    assert head, "заголовок непрочитанной очереди не отправлен"
    unread_card = [kw["text"] for _m, kw in sent if "gu1" in kw.get("text", "")]
    assert unread_card and "gs1" not in "".join(kw["text"] for _m, kw in sent)


def test_queue_batch_says_out_loud_when_it_shows_only_a_part():
    """Умолчавший предел читается как «это всё» — урок CLAUDE.md про консоль."""
    import inspect
    src = inspect.getsource(main._send_queue_batch)
    assert "Показаны первые" in src
    assert main.BATCH_LIMIT <= 10, "Telegram пускает ~20 сообщений в минуту"


def test_card_line_shows_every_source_not_just_the_first():
    """Урезанная строка «Источник: X» пряталa остальные источники карточки —

    владелец 19 августа принял карточку «HeadHunter»/Happy Job с четырьмя
    источниками и 1800+ знаками обогащённого текста за почти пустую именно
    по этой строке в консоли (там был виден только первый источник).
    """
    one_source = {"title": "Т", "src": [["Mergers.ru", "https://mergers.ru/x"]]}
    assert "Источник: Mergers.ru" in main._card_line(one_source)

    four_sources = {"title": "Т", "src": [
        ["Mergers.ru", "https://mergers.ru/x"], ["TAdviser", "https://tadviser.ru/x"],
        ["РБК Компании", "https://companies.rbc.ru/x"], ["Абирег", "https://abireg.ru/x"],
    ]}
    line = main._card_line(four_sources)
    assert "Источники (4)" in line
    for name in ("Mergers.ru", "TAdviser", "РБК Компании", "Абирег"):
        assert name in line, f"источник {name} пропал из строки"


def test_empty_queue_answers_instead_of_silence(monkeypatch):
    sent = []
    monkeypatch.setattr(main.notification_service, "tg_api",
                        lambda method, **kw: sent.append(kw) or {"ok": True})
    monkeypatch.setattr(main, "_read_json",
                        lambda path, default: {"cards": []} if "pending" in path else default)
    assert main._send_queue_batch(-100, "held") == 0
    assert any("пусто" in kw.get("text", "") for kw in sent)


def test_bot_help_explains_how_to_edit_a_card_and_a_post():
    """Владелец: «нужно, чтобы было понятно, как изменять карту, как изменять
    пост». Справка обязана объяснять оба пути ответом на сообщение."""
    text = main.BOT_HELP
    assert "станет текстом поста" in text
    assert "замечанием" in text and "по источнику" in text
    assert "callback" not in text.lower()


def test_bot_menu_offers_the_doubtful_queue_too():
    """Сомнительные (⚠️) до этого нельзя было вызвать заново — они приходили
    один раз и терялись в переписке."""
    data = [b["callback_data"] for row in main._bot_menu()["inline_keyboard"] for b in row]
    assert "show:raw" in data
