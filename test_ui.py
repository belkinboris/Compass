"""Дымовые тесты интерфейса: экраны открываются, ничего не падает, не переполняет.

Ловят ровно тот класс дефектов, который дважды проходил мимо ручных проверок:
страница фирмы не отрисовывалась из-за исключения в рендере (прошлый прогон), а
панель фильтров переполняла экран на 100px, но только в открытом виде.

ВАЖНО: слушаем `pageerror`, а не только `console`. Необработанное исключение в
консоль не попадает — «ошибок в консоли 0» без этого ничего не доказывает.

Запуск: python3 -m pytest test_ui.py -q
Пропускается, если не установлен Playwright (тогда гоняются только остальные).
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="playwright не установлен")
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parent
# Локально браузер предустановлен по этому пути (PLAYWRIGHT_BROWSERS_PATH), и
# `playwright install` запускать не нужно. В CI его нет — там Chromium ставится
# отдельным шагом, и Playwright сам знает, где он лежит.
_PRESET = Path("/opt/pw-browsers/chromium")
LAUNCH = {"executable_path": str(_PRESET)} if _PRESET.exists() else {}
WIDTHS = (360, 390, 1280)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_server(extra_env):
    """uvicorn в отдельном процессе. Переменные окружения — явно: вход по
    заявке (ACCESS_GATE, main.py) по умолчанию ВКЛЮЧЁН, и без ACCESS_GATE=0
    каждый экран этого файла оказался бы за дверью."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env={**os.environ, **extra_env}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.skip("не удалось поднять uvicorn")
    return proc, url


@pytest.fixture(scope="session")
def base_url():
    proc, url = _start_server({"ACCESS_GATE": "0"})
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def gated_url():
    """Второй сервер с включённым гейтом — для единственного теста двери.
    Без TELEGRAM_BOT_TOKEN уведомление владельцам молча не уходит (сети нет),
    а вебхук с секретом и списком решающих — живой."""
    env = {"ACCESS_GATE": "1", "TELEGRAM_WEBHOOK_SECRET": "ui-secret",
           "TELEGRAM_REVIEW_CHAT_IDS": "111", "TELEGRAM_BOT_TOKEN": ""}
    proc, url = _start_server(env)
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def browser():
    """Один браузер на сессию: запуск Chromium дороже всех тестов вместе."""
    with sync_playwright() as p:
        try:
            br = p.chromium.launch(**LAUNCH)
        except Exception as exc:
            pytest.skip(f"Chromium для Playwright недоступен: {exc}")
        yield br
        br.close()


@pytest.fixture(scope="session")
def page(base_url, browser):
    pg = browser.new_page(viewport={"width": 1280, "height": 1000})
    pg.crashes = []
    pg.on("pageerror", lambda e: pg.crashes.append(f"pageerror: {e}"))
    pg.on("console", lambda m: pg.crashes.append(f"console: {m.text}")
          if m.type == "error" else None)
    pg.goto(base_url + "/#/", wait_until="networkidle")
    pg.wait_for_timeout(2500)          # ждём вторую загрузку базы
    assert pg.evaluate("() => bulkLoaded"), "база так и не догрузилась"
    yield pg
    pg.close()


def visit(page, base_url, hash_):
    page.crashes.clear()
    page.goto(base_url + "/" + hash_, wait_until="networkidle")
    page.wait_for_timeout(900)
    assert not page.crashes, f"{hash_}: {page.crashes[:3]}"


SCREENS = [
    ("главная", "#/"),
    ("карточка сделки", "#/deal/citibank"),
    ("компании", "#/companies"),
    ("профиль компании", "#/companies/yandex"),
    ("консультанты", "#/advisors"),
    ("страница фирмы", "#/advisors/orion"),
    ("аналитика", "#/analytics"),
    ("отрасль", "#/industry/Банки"),
    ("подборка по ссылке", "#/deals?ind=Банки&year=2024&full=1"),
    ("ассистент", "#/assistant"),
    ("вход", "#/account"),
]


@pytest.mark.parametrize("name,hash_", SCREENS, ids=[s[0] for s in SCREENS])
def test_screen_renders_without_errors(page, base_url, name, hash_):
    visit(page, base_url, hash_)
    body = page.inner_text("#app").strip()
    assert len(body) > 120, f"{name}: экран почти пуст ({len(body)} знаков)"


def test_every_firm_page_opens(page, base_url):
    """Три фирмы из 64 не открывались: FIRM_MATCH заполнен не для всех, и
    рендер падал на rx.test. Проверяем не «нет ошибок», а что страница есть."""
    visit(page, base_url, "#/advisors")
    ids = page.evaluate("() => FIRMS.concat(INV_FIRMS).map(f => f.id)")
    broken = []
    for fid in ids:
        page.crashes.clear()
        page.goto(f"{base_url}/#/advisors/{fid}", wait_until="networkidle")
        page.wait_for_timeout(230)
        ok = page.evaluate("() => !!document.querySelector('#app .d-head h1')")
        if not ok or page.crashes:
            broken.append((fid, page.crashes[:1]))
    assert not broken, f"страница фирмы не открылась: {broken[:5]}"


def test_every_industry_page_opens(page, base_url):
    visit(page, base_url, "#/analytics")
    inds = page.evaluate("""() => [...new Set([...DEALS, ...MINI_DEALS, ...CHANNEL_DEALS,
        ...BULK_DEALS].map(x => x.ind).filter(Boolean))]""")
    broken = []
    for ind in inds:
        page.crashes.clear()
        page.goto(f"{base_url}/#/industry/{ind}", wait_until="networkidle")
        page.wait_for_timeout(230)
        ok = page.evaluate("() => !!document.querySelector('#app .an-card')")
        if not ok or page.crashes:
            broken.append((ind, page.crashes[:1]))
    assert not broken, f"страница отрасли не открылась: {broken[:5]}"


@pytest.mark.parametrize("width", WIDTHS)
def test_no_horizontal_overflow(page, base_url, width):
    """Переполнение ищем и в открытом состоянии панели фильтров: закрытая
    ничего не показывает, а открывают её ссылки #/theme/ и #/ind/."""
    # gcf05509a: статус «Согласование получено» — самая длинная из новых
    # цветных плашек (раздел B, 22 августа); citibank один короче не ловит
    # переполнение на самом длинном значении, как уже требует урок CLAUDE.md.
    checks = ["#/", "#/deal/citibank", "#/deal/g8ce554c5", "#/analytics",
              "#/assistant", "#/industry/Банки", "#/ind/Банки", "#/advisors/orion"]
    bad = []
    for h in checks:
        page.goto(base_url + "/" + h, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(450)
        over = page.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if over:
            bad.append((h, over))
        page.set_viewport_size({"width": 1280, "height": 1000})
    assert not bad, f"горизонтальное переполнение на {width}px: {bad}"


def test_no_external_requests(page, base_url):
    """Всё должно работать из России: ни одного запроса за пределы своего домена."""
    external = []
    handler = lambda r: external.append(r.url) if (
        "127.0.0.1" not in r.url and not r.url.startswith("data:")) else None
    page.on("request", handler)
    for h in ("#/", "#/analytics", "#/deal/citibank"):
        page.goto(base_url + "/" + h, wait_until="networkidle")
        page.wait_for_timeout(1200)
    page.remove_listener("request", handler)
    assert not external, f"внешние запросы: {external[:5]}"


def test_deal_has_timeline_and_inline_correction_dialog(page, base_url):
    visit(page, base_url, "#/deal/agrostroy-zemlya")
    # У сделки одна новость (продажа сразу закрыта) — «Ход сделки» не показываем:
    # единственный этап не добавил бы ничего к тому, что уже написано на карточке.
    assert page.locator(".deal-progress").count() == 0
    page.locator("#fixdeal").click()
    assert page.locator(".dialog-backdrop").is_visible()
    page.locator("#correctionBody").fill("Проверка редакционной формы")
    page.locator("#correctionSend").click()
    page.wait_for_selector(".dialog-msg.ok")
    assert "передано редакции" in page.locator(".dialog-msg.ok").inner_text().lower()


def test_citibank_is_one_deal_with_clickable_stage_history(page, base_url):
    visit(page, base_url, "#/deal/citibank")
    assert page.evaluate("() => DEALS.filter(d => d.id === 'citibank' || d.id === 'gf57ea8cb').length") == 1
    assert page.locator(".progress-current .progress-title").inner_text() == "Сделка завершена"
    assert page.locator(".progress-history").is_hidden()
    assert page.locator(".progress-history .progress-row").count() == 2

    page.locator("#historyToggle").click()
    assert page.locator(".progress-history").is_visible()
    page.locator(".progress-history .progress-row").last.click()
    page.wait_for_timeout(250)
    assert "/stage/negotiations-2024-01-01" in page.url
    assert page.locator(".stage-card").is_visible()
    assert "M&A Новости" in page.locator(".src").inner_text()


def test_sparse_notice_has_no_unrelated_deal_link(page, base_url):
    # На «Агрострой» блок «раскрыто немного деталей» раньше предлагал
    # «Посмотреть более подробную карточку» — рекомендация подбиралась по
    # отрасли и обычно оказывалась совсем другой сделкой. Ссылку убрали
    # целиком: пустое состояние честнее случайного перехода.
    visit(page, base_url, "#/deal/agrostroy-zemlya")
    note = page.locator(".coverage-note")
    assert note.is_visible()
    assert note.locator("a").count() == 0


def test_deal_source_block_shows_last_verified_date_when_known(page, base_url):
    # У карточки есть отметки, когда её сверяли с источником (кампания
    # дочитывания) — читатель раньше не видел ни одной из них. Показываем
    # самую позднюю, человеческими словами, без жаргона полей.
    visit(page, base_url, "#/deal/g1d36d186")
    note = page.locator(".src .acct-note")
    assert note.is_visible()
    assert "Сверено с источником" in note.inner_text()
    assert "16 авг" in note.inner_text()

    # У карточки без единой отметки о сверке строка честно не рисуется —
    # не выдумываем дату, которой нет. Раньше здесь стояла конкретная
    # карточка без reviewed/deep_researched — но кампания дочитывания
    # (22 августа 2026) закрыла всю такую очередь до нуля: держать в тесте
    # id живой карточки, у которой ЭТОГО поля нет, значит держать тест,
    # который сломается при следующей же партии обогащения. Проверяем
    # функцию `lastVerifiedDate` напрямую на синтетическом объекте — тот
    # же код, что рендерит блок, но без зависимости от состояния базы.
    visit(page, base_url, "#/deal/g1d36d186")
    assert page.evaluate("lastVerifiedDate({})") is None


@pytest.mark.parametrize("width", WIDTHS)
def test_advanced_filter_panel_with_new_select_has_no_overflow(browser, base_url, width):
    """Этап 16, П2 добавил пятый `<select>` в панель расширенного поиска —
    родня уже известного класса дефекта: скрытые состояния (открытая панель)
    проверяются отдельно от свёрнутых, и именно в открытом виде панель уже
    переполняла экран однажды (CLAUDE.md). Проверяем на всех трёх ширинах."""
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    try:
        pg = ctx.new_page()
        pg.crashes = []
        pg.on("pageerror", lambda e: pg.crashes.append(f"pageerror: {e}"))
        pg.goto(base_url + "/#/deals?ind=Банки", wait_until="networkidle")  # advOpen=true через параметр ленты
        pg.wait_for_timeout(900)
        assert pg.locator("#selrev").count() == 1, "нет фильтра «Финансы цели» в открытой панели"
        assert not pg.crashes
        assert pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        pg.close()
    finally:
        ctx.close()


def test_feed_finance_filter_narrows_by_target_revenue(browser, base_url):
    """Этап 16, П2: фильтр «Финансы цели» в ленте. Вставляем синтетическую
    сделку прямо в `DEALS` (та же техника, что и у теста мультипликатора на
    карточке) и подменяем `financeScreening` напрямую, не дожидаясь сети, —
    живая база не даёт управлять тем, у какой ИМЕННО компании есть выручка.
    Свежий контекст, а не общий `page`: тест мутирует глобальное состояние
    ленты (DEALS, financeScreening, filterMinRevenue), и even с откатом в
    конце безопаснее не делить его с остальными тестами сессии вовсе — тот
    же приём, что и у route-подмены сети в других тестах этого файла."""
    ctx = browser.new_context()
    try:
        pg = ctx.new_page()
        pg.crashes = []
        pg.on("pageerror", lambda e: pg.crashes.append(f"pageerror: {e}"))
        pg.goto(base_url + "/#/", wait_until="networkidle")
        pg.wait_for_timeout(2000)
        assert pg.evaluate("() => bulkLoaded")
        pg.evaluate("""() => {
            DEALS.push({id: 'zzz-screen-deal', date: '2024-06-01', added: '2024-06-01',
                        title: 'Синтетическая сделка для теста фильтра', type: 'M&A',
                        status: 'Закрыта', ind: 'ИТ и интернет', sum: 'Не раскрыта',
                        target: 'zzz-screen-target', buyer: 'yandex'});
            financeScreening = {'zzz-screen-target': {year: 2023, revenue_rub: 2e9}};
        }""")
        pg.evaluate("() => { feedPage = 1; feedQuery = 'Синтетическая сделка для теста'; renderFeedList(); }")
        pg.wait_for_timeout(300)
        link = 'a[href="#/deal/zzz-screen-deal"]'
        assert pg.locator(link).count() == 1

        # Порог выше настоящей выручки (2 млрд < 10 млрд) — карточка исчезает.
        pg.evaluate("() => { filterMinRevenue = '1e10'; feedPage = 1; renderFeedList(); }")
        pg.wait_for_timeout(300)
        assert pg.locator(link).count() == 0

        # Порог ниже настоящей выручки — карточка снова видна.
        pg.evaluate("() => { filterMinRevenue = '1e9'; feedPage = 1; renderFeedList(); }")
        pg.wait_for_timeout(300)
        assert pg.locator(link).count() == 1

        # Пока financeScreening ещё не пришёл (null) — фильтр не должен молча
        # прятать всю ленту, а показывать всё до момента, когда данные придут.
        pg.evaluate("() => { financeScreening = null; filterMinRevenue = '1e10'; feedPage = 1; renderFeedList(); }")
        pg.wait_for_timeout(300)
        assert pg.locator(link).count() == 1, \
            "фильтр спрятал карточку до того, как данные вообще загрузились"

        assert not pg.crashes, pg.crashes[:3]
        assert pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        pg.close()
    finally:
        ctx.close()


def test_deal_multiple_line_reads_only_verified_facts(page, base_url):
    """С 6 сентября 2026 клиент ничего не выводит из прозы: `dealMultipleLine`
    берёт числитель из d.facts и показывает мультипликатор только для
    сделки, у которой доля, цена и периметр ПОДТВЕРЖДЕНЫ двумя чтениями
    (facts.admitted.multiple_text). facts для синтетических сделок считает
    Python (facts.derive) — единственный исполнитель правил; здесь
    проверяется, что клиент честно читает результат, а не свои копии."""
    import facts
    visit(page, base_url, "#/deal/g1d36d186")
    registry = {"t1": {"company_id": "t1", "decision": "confirmed", "inn": "7700000001"}}
    ctx = {"registry": registry, "lot_ids": set()}
    base = {"type": "M&A", "status": "Закрыта", "date": "2024-06-01", "sum": "1 000 млн ₽",
            "target": "t1", "buyer": "b1", "seller": "Иван Иванов", "eco": {"share": "Куплено 100% долей"}}

    def with_facts(d, verified=False):
        f = facts.derive(d, ctx)
        if verified:
            for key in ("stake", "price"):
                f[key]["basis"] = "verified"
            f["price"]["scope"] = "equity"
            f["price"]["attribution"] = "parties"
            f["target"]["perimeter"] = "verified"
            f["target"]["perimeter_report"] = {"inn": "7700000001", "year": 2023, "revenue_rub": 5e8}
            f["nature"]["control_change_basis"] = "verified"
            f = facts.derive(dict(d, facts=f), ctx)
        return dict(d, facts=f)

    # по тексту всё сходится (100%, цена в рублях, ИНН подтверждён) — но не прочитано: нет
    rule_only = with_facts(base)
    assert page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2023)" % json.dumps(rule_only)) is None
    assert page.evaluate("factReason(%s, 'multiple_text')" % json.dumps(rule_only)) == "price_not_verified"
    # подтверждено двумя чтениями — есть, и формула та же: 1000 / 500
    ok = with_facts(base, verified=True)
    line = page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2023)" % json.dumps(ok))
    assert line and line["multiple"] == 2.0
    # без facts (карточка предпросмотра) — ни в один показатель
    assert page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2023)" % json.dumps(base)) is None
    assert page.evaluate("countsAsPrice(%s)" % json.dumps(base)) is False
    # не на вкладке цели — нет
    assert page.evaluate("dealMultipleLine(%s, 'b1', 500000000, 2023)" % json.dumps(ok)) is None
    # знаменатель — только тот отчёт, по которому читатели подтвердили периметр
    # (год и выручка): другой год или другая выручка — мультипликатора нет
    assert page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2024)" % json.dumps(ok)) is None
    assert page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2022)" % json.dumps(ok)) is None
    assert page.evaluate("dealMultipleLine(%s, 't1', 600000000, 2023)" % json.dumps(ok)) is None
    # год сделки — из подтверждённой даты закрытия, а не из даты карточки
    closed_later = dict(ok, facts=dict(ok["facts"], date=dict(ok["facts"]["date"], basis="verified", meaning="closing", value="2025-02-01")))
    assert page.evaluate("multipleYear(%s)" % json.dumps(closed_later))["year"] == 2025
    assert page.evaluate("dealMultipleLine(%s, 't1', 500000000, 2023)" % json.dumps(closed_later)) is not None  # разрыв 2 — допустим
    assert page.evaluate("multipleYear(%s)" % json.dumps(ok)) == {"year": 2024, "basis": "дата карточки"}
    # абсурдный мультипликатор — почти всегда выручка не того юрлица
    absurd = dict(ok, facts=dict(ok["facts"], price=dict(ok["facts"]["price"], value_rub=75_500_000_000)))
    assert page.evaluate("dealMultipleLine(%s, 't1', 17400000, 2023)" % json.dumps(absurd)) is None
    # допуски по показателям — из facts: деньги только из прочитанных цен
    assert page.evaluate("countsAsPrice(%s)" % json.dumps(rule_only)) is False
    assert page.evaluate("factReason(%s, 'purchase_sums')" % json.dumps(rule_only)) == "price_not_read"
    assert page.evaluate("countsAsPrice(%s)" % json.dumps(ok)) is True
    assert page.evaluate("countsAsTopPurchase(%s)" % json.dumps(ok)) is True
    est = with_facts(dict(base, sum="~1 000 млн ₽"))
    assert page.evaluate("sumBasis(%s)" % json.dumps(est)) == "estimate"
    assert page.evaluate("countsAsPrice(%s)" % json.dumps(est)) is False


def test_assistant_retrieval_finds_deal_regardless_of_word_case(page, base_url):
    """Этап 16, П4: ассистент ищет по своей базе (`relevantDeals`) до похода в
    Яндекс — но вопрос падежом отличается от заголовка карточки, и это не
    должно ломать поиск.

    Замер 30 августа 2026: «Ситибанком» (вопрос, творительный падеж) не
    находил карточку с «Ситибанк» (заголовок, именительный) — усечение слова
    до пропорциональной длины давало разный остаток для разных окончаний.
    Починено переходом на уже проверенный компаратор `sameWordFuzzy` (тот же,
    что работает в поиске по ленте), с ограничением разницы длины слов — иначе
    короткое «сити» (Москва-Сити) фаззи-совпадало с «ситибанк» и перетягивало
    ранжирование на сделки про недвижимость."""
    visit(page, base_url, "#/")
    for q in ("Кто купил Ситибанк?", "Что известно про сделку с Ситибанком?"):
        ids = page.evaluate("(q) => relevantDeals(q, 40).map(d => d.id)", q)
        assert "citibank" in ids, f"{q!r} не нашёл карточку citibank среди {len(ids)} кандидатов"
    # Тот же класс задачи в обратную сторону: короткое слово-предлог («про»)
    # не должно фаззи-совпадать с чужим более длинным словом («проект») и
    # вытеснять настоящий ответ из топа.
    top5_titles = page.evaluate(
        "relevantDeals('Что известно про Магнит', 5).map(d => d.title.toLowerCase())")
    assert sum(1 for t in top5_titles if "магнит" in t) >= 3, \
        f"«Магнит» вытеснен из топ-5 нерелевантными совпадениями: {top5_titles}"


def test_analytics_page_shows_market_multiples_block(browser, base_url):
    """Этап 16, П1: блок «Мультипликаторы рынка» на Аналитике — проверяем оба
    честных состояния (пусто и заполнено) подменой сетевого ответа, а не
    ожиданием, что в базе БФО когда-нибудь наберётся нужный набор сделок.
    Свежий контекст (не общий `page`), чтобы route-подмена не осталась
    висеть на остальных тестах сессии — тот же приём, что и у чипов группы."""
    ctx = browser.new_context()
    try:
        def populated(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "candidates_total": 42, "clean_total": 3, "median": 1.5,
                "industries": [{"industry": "ИТ и интернет", "count": 3, "median": 1.5, "min": 1.0, "max": 2.0}],
                "deals": [{"id": "citibank", "title": "Тестовая сделка", "year": 2024,
                           "target_id": "citibank", "target_name": "ООО Тест",
                           "sum_rub": 1000000000, "revenue_rub": 500000000,
                           "revenue_year": 2023, "multiple": 2.0}],
                "methodology": "Тестовая методика.",
            }))
        ctx.route("**/api/analytics/multiples", populated)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/analytics", wait_until="networkidle")
        pg.wait_for_timeout(800)
        body = pg.inner_text("#multiplesCard")
        assert "×1.5" in body or "×1,5" in body
        assert "ИТ и интернет" in body
        assert "Тестовая сделка" in body
        assert not errors
        assert pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        pg.close()

        # Сервер сказал «медианы не показывать» (SHOW_MULTIPLE_MEDIANS, по
        # умолчанию выключено до утверждения методики — вторая критика,
        # 6 сентября 2026): ни общей ×1.5, ни отраслевой строки, но список
        # сделок с ценой и показателем и текст методики остаются.
        def hidden(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "candidates_total": 42, "clean_total": 3, "median": 1.5, "show_medians": False,
                "industries": [{"industry": "ИТ и интернет", "count": 3, "median": 1.5, "min": 1.0, "max": 2.0}],
                "deals": [{"id": "citibank", "title": "Тестовая сделка", "year": 2024,
                           "target_id": "citibank", "target_name": "ООО Тест",
                           "sum_rub": 1000000000, "revenue_rub": 500000000,
                           "revenue_year": 2023, "multiple": 2.0}],
                "methodology": "Тестовая методика.",
            }))
        ctx.unroute("**/api/analytics/multiples")
        ctx.route("**/api/analytics/multiples", hidden)
        pg1 = ctx.new_page()
        pg1.goto(base_url + "/#/analytics", wait_until="networkidle")
        pg1.wait_for_timeout(800)
        body1 = pg1.inner_text("#multiplesCard")
        assert "×1.5" not in body1 and "×1,5" not in body1, body1
        assert "ИТ и интернет" not in body1
        assert "Тестовая сделка" in body1 and "×2" in body1
        assert "Медиану пока не выводим" in body1  # медианы скрыты (SHOW_MULTIPLE_MEDIANS)
        # Методика с 6 сентября 2026 — под раскрывашкой «Как считаем и почему
        # так»: три абзаца пояснений над пятью строками данных читались как
        # объяснительная записка (вопрос владельца «а что сейчас в таблице»).
        assert "Как считаем и почему так" in body1 and "Тестовая методика" not in body1
        pg1.click("#multiplesCard summary")
        pg1.wait_for_timeout(200)
        assert "Тестовая методика" in pg1.inner_text("#multiplesCard")
        pg1.close()

        def empty(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "candidates_total": 10, "clean_total": 0, "median": None,
                "industries": [], "deals": [], "methodology": "Тестовая методика.",
            }))
        ctx.unroute("**/api/analytics/multiples")
        ctx.route("**/api/analytics/multiples", empty)
        pg2 = ctx.new_page()
        pg2.goto(base_url + "/#/analytics", wait_until="networkidle")
        pg2.wait_for_timeout(800)
        body2 = pg2.inner_text("#multiplesCard")
        assert "не прошла все проверки" in body2.lower()
        pg2.close()
    finally:
        ctx.close()


def test_analytics_page_shows_nationalized_assets_section(browser, base_url):
    """Просьба владельца 5 сентября 2026: раздел «Аналитики» об изъятых и
    национализированных активах. Строится по теме «Национализация / иск
    Генпрокуратуры» (структурный признак, не поиск слов на лету): годы,
    отрасли, список последних сделок и ссылка на все сделки темы. Проверяем
    на трёх ширинах: карточка на всю ширину сетки, строки графиков не
    вылезают за экран (min-width:0 у колонок), ошибок нет."""
    for width in (1280, 390, 360):
        ctx = browser.new_context(viewport={"width": width, "height": 900})
        try:
            pg = ctx.new_page()
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(base_url + "/#/analytics", wait_until="networkidle")
            pg.wait_for_function(
                "typeof DEALS !== 'undefined' && DEALS.length > 100 && !!document.getElementById('nationalizedCard')",
                timeout=20000)
            pg.wait_for_timeout(700)
            # .label рисуется капителью (text-transform) — inner_text отдаёт ВЕРХНИЙ регистр.
            body = pg.inner_text("#nationalizedCard").lower()
            assert "изъятые и национализированные активы" in body
            assert "иску генпрокуратуры" in body and "все сделки темы" in body
            stats = pg.evaluate("""() => {
              const c = document.getElementById('nationalizedCard');
              const rows = [...c.querySelectorAll('.nat-grid .an-row')];
              return {items: c.querySelectorAll('.nat-list .an-deal').length,
                      years: c.querySelectorAll('.nat-grid > div:first-child .an-row').length,
                      clipped: rows.filter(r => r.getBoundingClientRect().right > document.documentElement.clientWidth + 1).length,
                      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                      opacity: getComputedStyle(c).opacity};
            }""")
            assert stats["items"] >= 5, stats
            assert stats["years"] >= 2, stats
            assert stats["clipped"] == 0 and stats["overflow"] == 0, (width, stats)
            assert stats["opacity"] == "1", "карточка осталась прозрачной после анимации проявления"
            assert not errors, errors
            # Ссылка на все сделки темы ведёт на список с карточками.
            pg.click("#nationalizedCard a[href^='#/theme/']")
            pg.wait_for_timeout(600)
            assert pg.evaluate("document.querySelectorAll('#app a[href^=\"#/deal/\"]').length") >= 5
            assert not errors, errors
        finally:
            ctx.close()


def test_leaving_analytics_before_multiples_reply_does_not_crash_advisors(browser, base_url):
    """2 сентября 2026: health-check поймал `pageerror` на «Консультантах»
    («Cannot set properties of null (setting 'innerHTML')»), хотя ломалась
    не эта страница — виновата `mountMarketMultiples()` со страницы
    «Аналитика»: она захватывает DOM-узел ДО await, а если пользователь
    уходит на другой экран, пока ответ ещё в пути, `route()` уже заменил
    `#app`, и запись в отсоединённый узел роняет исключение с ЧУЖОЙ, новой
    страницы. Подмена ответа через `page.route`/`route.fulfill` с задержкой
    ЗДЕСЬ НЕ ГОДИТСЯ (проверено — такой тест проходит одинаково что с
    починкой, что без неё, ничего не ловит) — гонку даёт только подмена
    `window.fetch` ДО загрузки страницы (`add_init_script`), чтобы
    задержался ЕДИНСТВЕННЫЙ, естественно запущенный самим рендером вызов,
    без второго, наведённого вручную (второй вызов сам путает картину —
    его собственный поздний ответ обгоняет первый, и узел оказывается
    отсоединён ещё до перехода на другой экран)."""
    ctx = browser.new_context()
    try:
        ctx.add_init_script("""
            const orig = window.fetch;
            window.fetch = function(url, ...args) {
                if (String(url).includes('/api/analytics/multiples')) {
                    return new Promise(resolve => setTimeout(() => resolve(orig(url, ...args)), 1500));
                }
                return orig(url, ...args);
            };
        """)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/analytics", wait_until="domcontentloaded")
        pg.wait_for_timeout(900)
        pg.evaluate("location.hash = '#/advisors'")
        pg.wait_for_timeout(2000)
        assert not errors
        pg.close()
    finally:
        ctx.close()


def test_analytics_multiples_toggle_switches_to_revenue_view(browser, base_url):
    """Два вида одного блока (не две карточки). С 31 августа 2026 первым и
    по умолчанию открыт «По прибыли» (просьба владельца), «По выручке» —
    второй; клик по нему должен подменить содержимое на другую методику и
    другую цифру, не оставляя оба набора цифр на экране разом. Если данных
    по прибыли нет (первый тест этого блока), открывается «По выручке»."""
    ctx = browser.new_context()
    try:
        def populated(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "candidates_total": 42, "clean_total": 3, "median": 1.5,
                "industries": [{"industry": "ИТ и интернет", "count": 3, "median": 1.5, "min": 1.0, "max": 2.0}],
                "deals": [{"id": "citibank", "title": "Тестовая сделка (выручка)", "year": 2024,
                           "target_id": "citibank", "target_name": "ООО Тест",
                           "sum_rub": 1000000000, "revenue_rub": 500000000,
                           "revenue_year": 2023, "multiple": 2.0}],
                "methodology": "Тестовая методика по выручке.",
                "operating_profit": {
                    "clean_total": 2, "median": 4.0,
                    "industries": [{"industry": "ИТ и интернет", "count": 2, "median": 4.0, "min": 3.0, "max": 5.0}],
                    "deals": [{"id": "citibank", "title": "Тестовая сделка (опер. прибыль)", "year": 2024,
                               "target_id": "citibank", "target_name": "ООО Тест",
                               "sum_rub": 1000000000, "operating_profit_rub": 250000000,
                               "operating_profit_year": 2023, "multiple": 4.0}],
                    "methodology": "Тестовая методика по операционной прибыли.",
                },
            }))
        ctx.route("**/api/analytics/multiples", populated)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/analytics", wait_until="networkidle")
        pg.wait_for_timeout(800)
        before = pg.inner_text("#multiplesCard")
        assert "×4" in before
        pg.click("#multiplesCard summary")
        pg.wait_for_timeout(200)
        before = pg.inner_text("#multiplesCard")
        assert "тестовая методика по операционной прибыли" in before.lower()
        assert "тестовая методика по выручке" not in before.lower()
        # кнопки одинаковой ширины — сетка из двух равных колонок
        widths = pg.evaluate("[...document.querySelectorAll('#multiplesCard [data-multview]')].map(b=>b.getBoundingClientRect().width)")
        assert len(widths) == 2 and abs(widths[0] - widths[1]) < 2, widths

        pg.click("#multiplesCard [data-multview='revenue']")
        pg.wait_for_timeout(300)
        pg.click("#multiplesCard summary")
        pg.wait_for_timeout(200)
        after = pg.inner_text("#multiplesCard")
        assert "×1.5" in after or "×1,5" in after
        assert "тестовая методика по выручке" in after.lower()
        assert "тестовая методика по операционной прибыли" not in after.lower()  # старый вид не остался на экране рядом
        assert not errors
        assert pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        pg.close()
    finally:
        ctx.close()


def test_deal_card_shows_ev_revenue_line_for_qualifying_target(browser, base_url):
    """Этап 16, П1в: строка «EV/Выручка» на вкладке «Экономист» — вызываем
    `mountDealFns` напрямую с синтетической сделкой (та же техника, что и в
    тесте на чистую функцию выше), а сетевой ответ о выручке цели подменяем
    route-перехватом. Так тест не зависит ни от содержимого живой базы, ни
    от того, синхронизировалась ли уже конкретная компания с ФНС на проде.

    Отчёт заодно несёт operating_profit_rub — проверяем, что рядом со
    строкой по выручке появляется и вторая, по операционной прибыли
    (ближе к привычному EV/EBITDA, deal_multiples.py), а не только одна
    из двух — это два независимых расчёта на одной и той же карточке."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": True, "company_id": "zzz-mult-target", "company_name": "ООО Тестцель",
                "entities": [{
                    "entity": {"id": 1, "legal_name": "ООО Тестцель", "inn": "7700000321"},
                    "reports": [{"year": 2023, "revenue_rub": 500_000_000, "operating_profit_rub": 100_000_000,
                                 "net_profit_rub": 1, "assets_rub": 1, "equity_rub": 1}],
                    "report_years": [2023], "has_more_reports": False, "has_more_events": False,
                    "events": [], "ownership": {"available": False},
                }],
                "access": {"paid": True, "full_history": True, "downloads": True},
            }))
        ctx.route("**/api/companies/zzz-mult-target/fns*", fake_fns)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/deal/citibank", wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click('[data-l="eco"]')  # рендерит #deal-fns — до этого его нет в DOM (вкладка "Обзор" по умолчанию)
        pg.wait_for_timeout(400)
        import facts
        deal = {"type": "M&A", "status": "Закрыта", "date": "2024-06-01", "sum": "1 000 млн ₽",
                "target": "zzz-mult-target", "buyer": "b1", "seller": "Иван Иванов",
                "eco": {"share": "Куплено 100% долей"}}
        # Мультипликатор на карточке — только по фактам, подтверждённым двумя
        # чтениями (facts.admitted.multiple_text); синтетической сделке они
        # выставляются так, как их записал бы facts_confirm.py.
        ctx_f = {"registry": {"zzz-mult-target": {"company_id": "zzz-mult-target", "decision": "confirmed", "inn": "7700000321"}}, "lot_ids": set()}
        f = facts.derive(deal, ctx_f)
        for key in ("stake", "price"):
            f[key]["basis"] = "verified"
        f["price"]["scope"] = "equity"
        f["price"]["attribution"] = "parties"
        f["target"]["perimeter"] = "verified"
        f["target"]["perimeter_report"] = {"inn": "7700000321", "year": 2023, "revenue_rub": 5e8}
        f["nature"]["control_change_basis"] = "verified"
        deal["facts"] = facts.derive(dict(deal, facts=f), ctx_f)
        pg.evaluate("mountDealFns(%s)" % json.dumps(deal))
        pg.wait_for_timeout(600)
        body = pg.inner_text("#deal-fns")
        # .tag рендерится заглавными (text-transform:uppercase), а innerText
        # отдаёт текст ПОСЛЕ CSS-преобразований — сравниваем без учёта регистра.
        # «EV» на карточке больше не обещается: считается цена пакета к выручке,
        # без долга — и подпись говорит это прямо (третий разбор рецензента)
        assert "цена ÷ выручка" in body.lower() and "ev/" not in body.lower()
        assert "×2" in body
        assert "2023" in body
        assert "цена ÷ операционная прибыль" in body.lower()
        assert "×10" in body  # 1000 млн / 100 млн
        assert not errors
        assert pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        pg.close()
    finally:
        ctx.close()


def test_pdf_button_note_does_not_get_stuck_on_login_prompt(page, base_url):
    # Кнопка ставила "Готовим PDF…" ДО запроса, а на 401 (гость не вошёл)
    # уводила во всплывающий тост и никогда не убирала эту строку — рядом с
    # кнопками навсегда оставалось "Готовим PDF…", хотя ничего не готовилось.
    # С 5 сентября 2026 гость получает PDF без входа (DEAL_EXPORT_GUESTS), и
    # 401 в живом сервере не встречается — ветку проверяем подменой ответа:
    # флаг когда-нибудь выключат, и строка не должна зависнуть и тогда.
    visit(page, base_url, "#/deal/g1d36d186")
    page.locator("#downloaddeal").click()
    page.wait_for_function(
        "document.getElementById('dealtoolnote').innerText === 'PDF скачан.'", timeout=15000)
    page.route("**/api/deals/*/export", lambda route: route.fulfill(
        status=401, content_type="application/json", body='{"error":"войдите"}'))
    try:
        page.locator("#downloaddeal").click()
        page.wait_for_selector(".toast")
        assert page.locator("#dealtoolnote").inner_text() == ""
    finally:
        page.unroute("**/api/deals/*/export")


def test_pre_2022_deals_hidden_from_site(page, base_url):
    # Сделки до 2022 года остаются в deals_promoted.json, но не показываются на
    # сайте: прямой переход по адресу карточки должен молча показать ленту
    # сделок (как для любого другого несуществующего id), а не пустую карточку.
    visit(page, base_url, "#/")
    assert page.evaluate("() => DEALS.some(d => d.id === 'g19d36a35')") is False
    visit(page, base_url, "#/deal/g19d36a35")
    assert page.locator(".heroslider").is_visible()
    assert page.locator(".deal-plate").count() == 0


def test_feed_card_without_sum_keeps_industry_tag_aligned(page, base_url):
    # На телефоне «.deal-meta» — flex с gap:14px (сумма и отраслевая метка в
    # ряд). Пустой блок суммы у сделки без суммы всё равно создавал зазор, и
    # метка отрасли съезжала на 14px правее заголовка и статуса — владелец
    # заметил это на карточке «ЗПИФ Прайм Первый» (химия и удобрения, суммы
    # нет). Блок суммы теперь не рисуется вовсе, если суммы нет. Ищем сделку
    # без суммы в живых данных, а не жёстко зашитый id — обогащение может
    # когда-нибудь заполнить сумму именно у примера из бага.
    # Смена хеша — переход внутри уже загруженной страницы (SPA), а не
    # перезагрузка: `visit()` не сбрасывает JS-переменные фильтров ленты
    # (feedYear/filterInd/filterTheme/…), а `page` общий на весь файл теста.
    # Прогон после теста, оставившего фильтр открытым, видел бы урезанную
    # ленту без искомой сделки (прогон одного теста — не проверка изоляции,
    # см. CLAUDE.md) — сбрасываем фильтры явно, а не полагаемся на переход.
    visit(page, base_url, "#/")
    did = page.evaluate("""() => {
        const d = DEALS.find(x => !x.sum);
        return d ? d.id : null;
    }""")
    assert did, "в базе не нашлось сделки без суммы — пример для теста нужно обновить"
    page.set_viewport_size({"width": 390, "height": 900})
    # Карточка без суммы может оказаться за первой страницей ленты — вместо
    # догадок о сортировке и кликов «показать ещё» просто просим ленту
    # отрисовать всё сразу, сбросив попутно все фильтры.
    page.evaluate("""() => {
        feedQuery = ""; filterInd = "Все"; feedYear = "Все"; filterTheme = "Все";
        filterFirm = "Все"; filterAdvisorGroup = "Все"; onlyFull = false; feedPage = 999;
        renderFeedList();
    }""")
    page.wait_for_timeout(300)
    row = page.locator(f'a.deal-row[href="#/deal/{did}"]')
    assert row.count() == 1
    assert row.locator(".deal-sum").count() == 0
    title_x = row.locator(".deal-title").bounding_box()["x"]
    tags_x = row.locator(".deal-tags").bounding_box()["x"]
    assert title_x == tags_x, f"метка отрасли не на одной вертикали с заголовком: {title_x} vs {tags_x}"
    page.set_viewport_size({"width": 1280, "height": 1000})


def test_citibank_seller_is_rendered(page, base_url):
    visit(page, base_url, "#/deal/citibank")
    plate = page.locator(".deal-plate").inner_text()
    assert "Citigroup" in plate
    assert "Продавец\nНе раскрыт" not in plate


def test_deal_plate_hides_asset_text_that_only_echoes_the_headline(page, base_url):
    # Этап 9, П6-9: «Алор брокер» купил «неназванную брокерскую компанию» —
    # предмет текстом дословно повторяет заголовок над плашкой, читателю
    # нечего узнать во второй раз. Плашка при этом не пустая целиком (есть
    # покупатель) — пропадает только блок «Предмет сделки».
    visit(page, base_url, "#/deal/g6bf41023")
    plate = page.locator(".deal-plate")
    assert plate.is_visible(), "плашка должна остаться — покупатель известен"
    assert plate.locator(".dp-asset").count() == 0, \
        "предмет — чистый повтор заголовка, не должен показываться текстом"
    assert "«Алор брокер»" in plate.inner_text()


def test_deal_plate_shows_asset_text_with_real_novelty(page, base_url):
    # Тот же механизм на карточке, где предмет называет то, чего в заголовке
    # нет (адрес, а не пересказ заголовка), — строка обязана остаться.
    visit(page, base_url, "#/deal/g304f9065")
    plate = page.locator(".deal-plate")
    assert plate.locator(".dp-asset").count() == 1
    assert "элеватор" in plate.locator(".dp-asset").inner_text().lower()


def test_account_form_is_visible_after_async_auth_check(page, base_url):
    visit(page, base_url, "#/account")
    assert page.locator("#loginForm").is_visible()
    assert page.locator("#loginEmail").is_visible()
    assert "Войти" in page.locator("#app").inner_text()


def test_account_form_survives_late_base_load(browser, base_url):
    """`loadBulkDeals()` безусловно звала `route()` вторым проходом, когда
    deals_promoted.json наконец догружался, — и на «Подписках» аккаунта это
    стирало то, что человек уже успел ввести. Внутри SPA переход на «Подписки»
    — смена хеша, а не перезагрузка страницы: `loadBulkDeals()`, запущенный
    ПЕРВЫМ заходом на сайт, продолжает висеть в фоне, и его отложенный
    `route()` перерисовывал форму, пока человек её заполнял. Страница подписок
    не читает DEALS/COMPANIES вообще — перерисовывать её после прихода базы
    не было смысла, только риск. Держим domain-файл искусственно долго и
    переходим на «Подписки» сменой хеша (`location.hash=`, как в реальном
    интерфейсе), а не повторным `goto` — иначе тест перезапускает
    `loadBulkDeals()` заново и не попадает в то же окно, что и живой баг."""
    ctx = browser.new_context()
    try:
        def delay(route):
            time.sleep(2)
            route.continue_()
        ctx.route("**/static/data/deals_promoted.json*", delay)
        pg = ctx.new_page()
        pg.goto(base_url + "/#/", wait_until="domcontentloaded")
        email = f"race{int(time.time()*1000)}@example.com"
        reg = pg.evaluate("""async (email) => {
            const r = await fetch("/api/auth/register", {method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({email, password:"testpass123", full_name:"Тест Гонщиков",
                    company:null, position:null, role:"individual"})});
            return r.status;
        }""", email)
        assert reg == 200, "регистрация не удалась"

        pg.evaluate("location.hash = '#/account?tab=subscriptions'")
        pg.wait_for_selector("#subInd", timeout=10000)
        pg.select_option("#subInd", label="ИТ и интернет")
        pg.fill("#subKw", "гонка")
        pg.click("#subAdd")
        pg.wait_for_timeout(3000)               # дать отложенной базе догрузиться и route() сработать

        rows = pg.evaluate("""async () => {
            const r = await fetch("/api/subscriptions");
            return r.ok ? await r.json() : null;
        }""")
        assert rows and any(x.get("keyword") == "гонка" for x in rows), \
            f"подписка не сохранилась — форму стёрло перерисовкой после прихода базы: {rows}"
    finally:
        ctx.close()


def test_search_ignores_dots_and_hyphens_inside_names(base_url, browser):
    """«авто ру» и «ттехнологии» обязаны находить «Авто.ру» и «Т-Технологии».
    Замер до правки: у 367 карточек название в заголовке содержит точку или
    дефис внутри, а индекс сравнивался дословно — «авто ру», «авто-ру» и
    «ттехнологии» давали ПУСТО, а «т технологии» находило чужую сделку.
    Проверяем и обратное: поиск не должен начать находить всё подряд.
    Чистый контекст: фильтры ленты живут в глобальных переменных и переживают
    смену хеша, поэтому в общем прогоне состояние пришло бы от прошлого теста."""
    ctx = browser.new_context()
    try:
        pg = ctx.new_page()
        pg.goto(base_url + "/#/deals", wait_until="networkidle")
        pg.wait_for_function("typeof bulkLoaded !== 'undefined' && bulkLoaded", timeout=30000)

        def search(q):
            pg.fill("#feedq", q)
            pg.press("#feedq", "Enter")
            pg.wait_for_timeout(400)
            return pg.evaluate("document.getElementById('feedlist').innerText")

        for q in ("авто.ру", "авто ру", "авто-ру", "т-технологии", "ттехнологии", "т технологии"):
            text = search(q)
            assert "Авто.ру" in text and "Т-Технологии" in text, \
                f"запрос «{q}» не нашёл сделку Т-Технологии/Авто.ру"

        # Продавец и предмет записаны текстом, а не ссылкой на профиль: без них
        # в индексе по продавцу не находились 254 карточки из 653.
        assert "Flowwow" in search("Владельцы Flowwow"), "по продавцу текстом сделка не находится"

        # Обратная проверка: нормализация не должна стирать различия между
        # разными компаниями — иначе «находит всё» неотличимо от «ищет хорошо».
        other = search("сбербанк")
        assert "Авто.ру" not in other, "поиск стал находить нерелевантные сделки"
        assert len(other.strip()) > 0, "запрос «сбербанк» не нашёл вообще ничего — сломан сам поиск"
    finally:
        ctx.close()


def test_shared_link_restores_the_selection(base_url, browser):
    """Подборка должна открываться у коллеги так же, как у отправителя:
    раньше три фильтра оставляли адрес #/ и ссылка не несла ничего.
    Обязательно в ЧИСТОМ контексте: в своей вкладке фильтры уже в памяти, и
    ссылка выглядит рабочей, даже когда она пустая."""
    ctx = browser.new_context()
    try:
        pg = ctx.new_page()
        pg.goto(base_url + "/#/deals?ind=Банки&year=2024&full=1", wait_until="networkidle")
        pg.wait_for_timeout(2500)
        state = pg.evaluate("""() => ({ind: filterInd, year: feedYear, full: onlyFull,
            rows: document.querySelectorAll('#feedlist .deal-row').length})""")
    finally:
        ctx.close()
    assert state["ind"] == "Банки" and state["year"] == "2024" and state["full"] is True, state
    assert state["rows"] > 0, "подборка по ссылке пуста"


def test_failed_base_load_shows_retry_instead_of_fake_small_numbers(browser, base_url):
    """Баг с телефона владельца: на нестабильной мобильной сети запрос
    deals_promoted.json иногда срывается, а `bulkLoaded=true` выставлялся
    безусловно после обеих попыток fetch — сайт тихо объявлял себя
    загруженным с 36 захардкоженными компаниями и ~161 сделкой вместо
    настоящих ~1300, без единого признака, что это не полная база. Теперь
    неудача повторяется несколько раз, а если так и не удалось — честно
    показывает «Не удалось загрузить» вместо вымышленных маленьких чисел.
    Отдельный чистый контекст: тест рвёт сеть и не должен задеть общий `page`,
    которым пользуются остальные тесты файла."""
    ctx = browser.new_context()
    try:
        ctx.route("**/*", lambda route: route.abort()
                  if "deals_promoted.json" in route.request.url else route.continue_())
        pg = ctx.new_page()
        pg.goto(base_url + "/#/", wait_until="networkidle")
        # 4 попытки с паузами 1.5/3/4.5/6с — с запасом до отказа
        pg.wait_for_timeout(17000)
        assert pg.evaluate("() => bulkLoaded") is False
        assert pg.evaluate("() => bulkLoadFailed") is True
        hero = pg.locator(".hero-note").inner_text()
        assert "Не удалось загрузить" in hero
        assert "161" not in hero and "36" not in hero, "вымышленные числа не должны показываться как настоящие"
        retry = pg.locator("#reloadBase")
        assert retry.count() >= 1

        ctx.unroute("**/*")
        retry.first.click()
        pg.wait_for_timeout(2500)
        assert pg.evaluate("() => bulkLoaded") is True
        assert pg.evaluate("() => TOTAL_DEALS()") > 1000
    finally:
        ctx.close()


def test_cards_without_eco_or_law_render_without_pageerror(page, base_url):
    """У 136 карточек нет объекта `eco`, у 112 — `law`, и интерфейс их читал
    без проверки.

    `d.eco.share` на «Обзоре» вычислялся ВСЕГДА, когда предмет не разобран
    структурно: карточка «Возврат отеля «Имеретинский»» роняла `renderDeal`
    с `Cannot read properties of undefined (reading 'share')`. Страница при
    этом что-то показывала, поэтому проверка «экран не пуст» дефекта не
    видела — его поймал только слушатель `pageerror`. Тот же класс, что
    урок E9 в CLAUDE.md: тормоз `NEW_CARDS_NEED_REVIEW` год не пускал в базу
    новых карточек, и десятки мест, читающих `d.law.adv` без проверки, не
    проявлялись.

    Два других таких же места: фильтр ленты по фирме (`it.rec.law.adv`) и
    страница фирмы (`d.law.adv.find`, `d.eco.finadv`).
    """
    visit(page, base_url, "#/")
    thin = page.evaluate(
        "() => DEALS.filter(d => !d.eco || !d.law).slice(0, 12).map(d => d.id)")
    assert thin, "в базе не осталось карточек без eco/law — проверка потеряла смысл"
    for deal_id in thin:
        page.evaluate("id => location.hash = '#/deal/' + id", deal_id)
        page.wait_for_timeout(220)
        assert page.inner_text("#app").strip(), f"{deal_id}: экран пуст"
    assert not page.crashes, f"падения на карточках без eco/law: {page.crashes[:3]}"


def test_no_undefined_on_screen_for_cards_without_status(page, base_url):
    """У 136 карточек нет поля `status`, а лента и шапка печатали его напрямую.

    На экране это выглядело так: «28 июл. 2022 · UNDEFINED · ГМК и добыча» —
    и в строке ленты, и в шапке карточки, и в тексте кнопки «поделиться», и
    отдельным столбцом «undefined» в аналитике. Дефект видно только глазами
    или такой проверкой: экран не пуст, ошибок в консоли нет, разметка
    валидна — всё молчит.
    """
    visit(page, base_url, "#/")
    ids = page.evaluate("() => DEALS.filter(d => !d.status).slice(0, 6).map(d => d.id)")
    assert ids, "в базе не осталось карточек без статуса — проверка потеряла смысл"
    for hash_ in ["#/", "#/analytics"] + ["#/deal/" + i for i in ids]:
        visit(page, base_url, hash_)
        text = page.inner_text("#app")
        assert "undefined" not in text.lower(), f"{hash_}: на экране слово undefined"


def test_regulatory_analyzer_is_hidden(page, base_url):
    """Анализатор регуляторики спрятан с сайта (просьба владельца 10 августа:

    «он пока бесполезный») — ни кнопки на «Обзоре», ни панели в «Юристе» быть
    не должно. Код панели (`regPanelHtml`) не удалён, только отключены оба
    места вызова — так что тест проверяет именно ОТСУТСТВИЕ на экране, а не
    отсутствие функции в файле.
    """
    visit(page, base_url, "#/")
    any_id = page.evaluate("() => DEALS[0] && DEALS[0].id")
    assert any_id, "в базе нет карточек для проверки"
    visit(page, base_url, "#/deal/" + any_id)
    assert page.locator("[data-reg-open]").count() == 0, "кнопка анализатора всё ещё на экране"
    page.evaluate("document.querySelector('[data-l=\"law\"]').click()")
    page.wait_for_timeout(400)
    assert page.locator("#reg-panel").count() == 0, "панель анализатора всё ещё на экране"
    assert not page.crashes, f"падения на карточке: {page.crashes[:3]}"


def test_analytics_period_filter_narrows_every_card(page, base_url):
    """Аналитика — рабочая страница, а не простыня цифр.

    Фильтры стоят первыми и сужают ВСЕ карточки разом; выбранный год
    разворачивается в месяцы, потому что одна колонка на весь график («2025 —
    100%») — это не график, а строка.
    """
    visit(page, base_url, "#/analytics")
    assert page.locator("#anYearSel").count() == 1, "нет фильтра периода"
    assert page.locator("#anIndSel").count() == 1, "нет фильтра отрасли"
    whole = page.inner_text(".an-filters-note")

    page.select_option("#anYearSel", "2025")
    page.wait_for_timeout(600)
    assert not page.crashes, page.crashes[:3]
    head = page.locator(".an-card .label").first.inner_text()
    assert "2025" in head, f"график не развернулся в месяцы: {head!r}"
    narrowed = page.inner_text(".an-filters-note")
    assert narrowed != whole, "подпись выборки не изменилась"
    # Сужение обязано затронуть не только первый график: если карточка «Статус
    # сделок» считает по всей базе, соседние числа на одном экране начинают
    # противоречить друг другу.
    shown = int(re.search(r"Показано (\d+)", narrowed).group(1))
    status_card = page.evaluate(
        "() => [...document.querySelectorAll('.an-card')]"
        ".find(c => /статус сделок/i.test(c.innerText)).innerText")
    assert re.search(r"из %d\b" % shown, status_card), \
        f"карточка статусов считает не по выборке: {status_card[:160]!r}"

    page.click("#anReset")
    page.wait_for_timeout(600)
    assert page.inner_text(".an-filters-note") == whole, "сброс не вернул полную выборку"


def test_analytics_shows_sum_dynamics_and_advisor_league(page, base_url):
    """Этап 16, П3: «сколько сделок» и «на сколько» — разные графики.

    Карточка сумм по периодам разворачивается в кварталы при выборе года
    (та же логика, что у графика счётчика сделок), а «Консультанты»
    называют знаменатель «где консультант известен», а не общее число сделок.
    """
    visit(page, base_url, "#/analytics")
    cards = page.locator(".an-card")
    labels = [cards.nth(i).locator(".label").inner_text().lower() for i in range(cards.count())]
    sum_card_idx = next((i for i, l in enumerate(labels) if "сумма сделок по годам" in l), None)
    assert sum_card_idx is not None, f"нет карточки суммы сделок по годам: {labels}"
    # «Лига консультантов» → «Консультанты» (просьба владельца 31 августа 2026:
    # слово «лига» по-русски здесь не говорят); знаменатель по-прежнему «где
    # консультант известен», а не общее число сделок.
    league_idx = next((i for i, l in enumerate(labels) if l == "консультанты"), None)
    assert league_idx is not None, f"нет карточки «Консультанты»: {labels}"
    league_note = cards.nth(league_idx).locator("p").inner_text().lower()
    assert "консультант известен" in league_note, f"нет знаменателя раскрытия: {league_note!r}"
    assert "лига" not in " ".join(labels)

    page.select_option("#anYearSel", "2025")
    page.wait_for_timeout(600)
    assert not page.crashes, page.crashes[:3]
    cards2 = page.locator(".an-card")
    labels2 = [cards2.nth(i).locator(".label").inner_text().lower() for i in range(cards2.count())]
    sum_card2 = next((l for l in labels2 if "сумма сделок по кварталам" in l), None)
    assert sum_card2 and "2025" in sum_card2, f"карточка суммы не развернулась в кварталы: {labels2}"

    page.click("#anReset")
    page.wait_for_timeout(600)


def test_analytics_names_the_set_it_counts(page, base_url):
    """У числа на экране два свойства: величина и множество.

    В файле 1538 карточек, а на сайте показаны только сделки с 2022 года —
    191 запись скрыта. Подпись «вся база» над отфильтрованным числом была бы
    арифметически верной и всё равно врала.
    """
    visit(page, base_url, "#/analytics")
    shown = page.evaluate("() => DEALS.length")
    # Шапка «Аналитики» с 6 августа — тёмная hero-полоса (.page-hero),
    # а не .sec-head: чередование тёмных и светлых страниц.
    head = page.inner_text(".page-hero")
    assert str(shown) in head, f"шапка не называет своё число: {head[:160]!r}"
    assert "с 2022" in head, "не сказано, какое множество посчитано"
    assert "вся база" not in head.lower(), "показанное названо всей базой"


def test_company_sector_opens_the_industry_page(page, base_url):
    """Отрасль на карточке компании — вход в отрасль, а не украшение.

    Ссылку внутрь карточки поставить нельзя (вся карточка уже <a> на профиль),
    поэтому переход делает делегированный обработчик — и проверять его надо
    именно кликом, а не наличием href.
    """
    visit(page, base_url, "#/companies")
    page.locator("[data-co-ind]").first.click()
    page.wait_for_timeout(900)
    assert "#/industry/" in page.url, f"клик по отрасли никуда не увёл: {page.url}"
    assert not page.crashes, page.crashes[:3]
    assert len(page.inner_text("#app").strip()) > 120, "страница отрасли пуста"

    visit(page, base_url, "#/companies/yandex")
    tag = page.locator(".d-head a.tag").first
    assert tag.count() == 1, "на странице компании отрасль не ссылка"
    assert (tag.get_attribute("href") or "").startswith("#/industry/")


def _company_links_shown(pg):
    """`SHOW_COMPANY_LINKS` в static/index.html: связи между компаниями
    («Контроль у», «Под контролем», «Входит в группу», «В группу входит»,
    «Портфель») выключены 3 сентября 2026 по просьбе владельца до тех пор,
    пока данные неполные. Тесты, проверяющие текст этих строк, при
    выключенном флаге пропускаются, а их отсутствие держит
    `test_company_links_are_hidden_while_the_data_is_incomplete`."""
    return bool(pg.evaluate("typeof SHOW_COMPANY_LINKS !== 'undefined' && SHOW_COMPANY_LINKS"))


LINKS_OFF = "связи между компаниями выключены (SHOW_COMPANY_LINKS=false, 3 сентября 2026)"


def test_company_group_membership_is_shown_both_ways(page, base_url):
    """`holding.id` резолвится через `co()`, а не через отдельный справочник.

    До 18 августа 2026 группа резолвилась через захардкоженный `HOLDINGS{}`:
    у «УГМК-Инвест» `holding.id` верно указывал на настоящий профиль «УГМК»
    (`g3a8fb04f`), но резолвер знал только про `HOLDINGS`, и бейдж молча не
    рендерился ни на одной из двух карточек — связь была в данных и не была
    видна на экране (тот же класс дефекта, что «текстовое поле стороны может
    быть невидимым» — BM-банк/RWB). Проверяем оба направления текстом на
    экране, а не структурой DOM: именно так дефект и находился раньше.
    """
    visit(page, base_url, "#/companies/ugmkinvest")
    if not _company_links_shown(page):
        pytest.skip(LINKS_OFF)
    body = page.inner_text("#app").lower()
    assert "входит в группу" in body, "бейдж группы не показан у дочерней карточки"
    assert "угмк" in body

    visit(page, base_url, "#/companies/g3a8fb04f")
    body = page.inner_text("#app").lower()
    assert "в группу входит" in body, "обратная ссылка на дочерние компании не показана"
    assert "угмк-инвест" in body


def test_group_members_show_finance_chip_and_honest_disclaimer(browser, base_url):
    """23 августа 2026, этап 2 брифа: карточка-хаб группы («Роснефть»,
    `g300b9ead`) должна не просто перечислять компании группы («Башнефть»,
    `gf9a640d2` — уже настоящая связь `holding.id` в базе), а показывать
    рядом чип с последней выручкой, если данные ФНС подтверждены и не
    устарели, и честную строку про то, что это НЕ консолидированная
    отчётность. Живые данные Башнефти сейчас устарели (штамп 2020 года,
    /api/companies/.../fns их сам не отдаёт — см. `stale_latest_year`),
    поэтому сеть подменяется на свежий ответ: тест должен проверять код
    рендера чипа, а не то, успела ли ФНС обновить конкретное юрлицо."""
    ctx = browser.new_context()
    try:
        def fresh_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": True, "company_id": "gf9a640d2", "company_name": "Башнефть",
                "entities": [{
                    "entity": {"id": 1, "legal_name": 'ПАО АНК "БАШНЕФТЬ"', "inn": "0274051582"},
                    "reports": [{"year": 2025, "revenue_rub": 700_000_000_000,
                                "net_profit_rub": 1, "assets_rub": 1, "equity_rub": 1}],
                    "report_years": [2025], "has_more_reports": False, "has_more_events": False,
                    "events": [], "ownership": {"available": False},
                }],
                "access": {"paid": True, "full_history": True, "downloads": True},
            }))
        ctx.route("**/api/companies/gf9a640d2/fns*", fresh_fns)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/companies/g300b9ead", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        if not _company_links_shown(pg):
            pytest.skip(LINKS_OFF)
        body = pg.inner_text("#app")
        assert "консолидированная отчётность группы обычно не раскрывается" in body.lower()
        assert "700" in body and ("млрд" in body.lower())
        assert not errors, "pageerror при рендере чипов группы: %s" % errors
        assert pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
    finally:
        ctx.close()


def test_group_badge_appears_in_catalog_for_operating_groups(page, base_url):
    """23 августа 2026, этап 3 брифа: `group:true` — первая партия из 21
    профиля (16 целей `holding.id` + 5 общеизвестных групп вроде Яндекса).
    Бейдж «Группа компаний» обязан быть виден уже в каталоге, до перехода на
    карточку, — иначе владельцу пришлось бы открывать каждый профиль, чтобы
    понять, кто группа, а кто нет."""
    visit(page, base_url, "#/companies")
    try:
        page.fill("#coq", "МТС")
        page.wait_for_timeout(600)
        cards = page.locator(".co-card")
        assert cards.count() >= 1, "поиск «МТС» не нашёл карточку в каталоге"
        assert "группа компаний" in cards.first.inner_text().lower(), \
            "бейдж группы не показан в каталоге у профиля с group:true"
    finally:
        # `coQuery` — глобальная JS-переменная, не сбрасывается переходом по
        # хешу (см. CLAUDE.md, «переход по хешу — не перезагрузка страницы
        # для теста»): не очистив её, следующий тест каталога в том же `page`
        # унаследует фильтр «МТС» и увидит не всю базу компаний.
        page.fill("#coq", "")
        page.wait_for_timeout(600)


def test_investor_portfolio_never_says_group_membership(page, base_url):
    """АФК «Система» держит долю в МТС, но МТС НЕ «входит в группу АФК
    Система» — владелец прямо просил не путать эти два факта (запись в
    CLAUDE.md, 23 августа 2026). Карточка инвестора показывает «Портфель», а
    не бейдж «Группа компаний» и не блок «В группу входит»."""
    visit(page, base_url, "#/companies/gc2792a44")
    if not _company_links_shown(page):
        pytest.skip(LINKS_OFF)
    body = page.inner_text("#app").lower()
    assert "портфель" in body, "блок «Портфель» не показан на карточке инвестора"
    assert "мтс" in body, "МТС не видна в портфеле АФК «Система»"
    assert "группа компаний" not in body, "инвестор не должен нести бейдж «Группа компаний»"
    assert "в группу входит" not in body, "инвестор не должен показывать блок «В группу входит»"


def test_owned_company_shows_investor_in_ownership_block(page, base_url):
    """Обратное направление того же факта: на карточке МТС в «Собственники»
    видна АФК «Система» с долей и источником (страница МТС для инвесторов),
    а не выдуманная цифра."""
    visit(page, base_url, "#/companies/g69c88bc7")
    body = page.inner_text("#app").lower()
    assert "собственники" in body
    assert "афк" in body and "система" in body
    assert "42,085%" in page.inner_text("#app")


def test_group_badge_shown_even_without_current_dependent_profiles(page, base_url):
    """Яндекс — общеизвестная операционная группа, но сегодня в базе нет ни
    одного профиля, чей `holding.id` указывал бы на неё, — обратное правило
    целостности не требуется (см. docstring pipeline/mark_operating_groups.py
    и test_data.py::test_holding_target_is_always_flagged_as_group). Бейдж
    обязан быть виден, а пустой блок «В группу входит: 0» — нет: родня уже
    записанного урока «блок, который всегда полон, ничего не подбирает»,
    только здесь про блок, обязанный уметь не существовать при нуле."""
    visit(page, base_url, "#/companies/yandex")
    body = page.inner_text("#app").lower()
    assert "группа компаний" in body, "бейдж группы не показан у Яндекса"
    assert "в группу входит" not in body, "пустой блок состава не должен рисоваться"


def test_group_schema_button_is_gone_everywhere(page, base_url):
    """Этап 8: оба партнёра вживую увидели схему («Схема бесполезная
    конечно… собирать группу по нашей базе сделок здесь точно не
    работает — либо брать со всего интернета, включая ЕГРЮЛ, либо не
    добавлять вообще на этом этапе») и попросили её убрать. Кнопка снята
    с экрана на всех профилях, включая те, что раньше её показывали
    (Ростелеком — ≥2 holding-детей, Альфа-Банк — портфель из трёх). Текст
    блока «Структура и связи» (в т. ч. строки «В группу входит»/
    «Портфель») остаётся — просьба была именно про схему, не про сам
    блок. `groupSchemaSvg()` в коде не удалена — вернуть кнопку, когда
    состав групп будет собираться из настоящих источников (ЕГРЮЛ и т. п.),
    не из id-ссылок внутри своей базы."""
    for company_id in ("g00f14033", "ga2cfae5b", "gc2792a44"):
        visit(page, base_url, f"#/companies/{company_id}")
        assert page.locator("#toggleGroupSchema").count() == 0, \
            f"кнопка схемы не должна показываться на {company_id}"
        assert page.locator("#group-schema").count() == 0, \
            f"контейнер схемы не должен рендериться на {company_id}"
    if _company_links_shown(page):
        body = page.inner_text("#app").lower()
        assert "портфель" in body and "мтс" in body, "строка «Портфель» обязана остаться и без кнопки схемы"


def test_company_ownership_block_shown_only_when_known(page, base_url):
    """G8 (PRODUCT_ROADMAP.md): «Собственники» — новый блок на странице
    компании, пилот на двух профилях (владелец сравнивал нас с TAdviser,
    у которого видны собственники, а у нас поле `ownership` было пустым
    у всех профилей). Проверяем оба состояния: у карточки с фактом блок
    показывает имя, долю и дату источника; у карточки без факта блок не
    рисуется вовсе — честная пустота, а не всегда пустой блок (родня уже
    записанного урока «Блок, который всегда полон, ничего не подбирает» —
    здесь зеркально: блок обязан уметь не существовать).
    """
    visit(page, base_url, "#/companies/gfd143c7d")
    body = page.inner_text("#app").lower()
    assert "собственники" in body
    assert "деметра-холдинг" in body
    assert "100%" in body
    assert "октябрь 2024" in body

    visit(page, base_url, "#/companies/yandex")
    assert "собственники" not in page.inner_text("#app").lower()


def test_ao_participants_show_founders_heading_without_overlap(browser, base_url):
    """Этап 5, П1'''''/П2''''': для АО вкладка «Участники» обязана сказать
    прямо, что это учредители при регистрации, а не текущий состав (ЕГРЮЛ
    не отслеживает акционеров АО) — и длинное ФИО не должно перекрываться
    чипом доли. Сеть подменена, потому что живые данные АФК в базе сейчас
    без известных долей — нужен и «доля есть» (для проверки наложения), и
    «доли нет ни у кого» (для проверки единой строки-пояснения) кейс сразу."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": True, "company_id": "gc2792a44", "company_name": "АФК «Система»",
                "entities": [{
                    "entity": {"id": 1, "legal_name": 'ПАО АФК "Система"', "inn": "7708004767",
                              "legal_form": "Публичное акционерное общество"},
                    "reports": [], "report_years": [], "has_more_reports": False,
                    "has_more_events": False, "events": [],
                    "ownership": {
                        "available": True, "is_ao": True, "heading": "Учредители при регистрации",
                        "as_of": "2002-11-11",
                        "current": [
                            {"name": "Гончарук Александр Юрьевич", "type": "Физическое лицо",
                             "inn": "770500000002", "nominal_value_rub": 23625, "share_percent": 8.3333},
                            {"name": "Евтушенков Владимир Петрович", "type": "Физическое лицо",
                             "inn": "770500000001", "nominal_value_rub": 615312, "share_percent": 12.5},
                        ],
                        "history": [], "has_more_history": False,
                        "notice": ("ЕГРЮЛ не отслеживает акционеров акционерного общества — здесь список "
                                  "учредителей на момент регистрации, а не текущие владельцы. Актуальные "
                                  "собственники, если раскрыты, — в блоке «Собственники» на странице компании."),
                    },
                }],
                "access": {"paid": True, "full_history": True, "downloads": True},
            }))
        ctx.route("**/api/companies/gc2792a44/fns*", fake_fns)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_viewport_size({"width": 360, "height": 900})
        pg.goto(base_url + "/#/companies/gc2792a44", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        pg.click("[data-fnstab='ownership']")
        pg.wait_for_timeout(300)
        body = pg.inner_text("#app").lower()
        assert "учредители при регистрации" in body
        assert "не отслеживает акционеров" in body
        assert not errors, "pageerror при рендере вкладки участников: %s" % errors

        goncharuk_card = pg.locator(".owner-card", has_text="Гончарук")
        name_box = goncharuk_card.locator(".owner-name").bounding_box()
        share_box = goncharuk_card.locator(".owner-share").bounding_box()
        assert name_box and share_box, "у карточки с известной долей должны быть и имя, и чип"
        # Пересечение по X: правая граница имени должна быть левее (или на
        # чипе только там, где сам чип начинается) — конкретно проверяем,
        # что бокс имени не заходит за левый край чипа доли того же ряда
        # (оба — в первой owner-card, где известна доля).
        overlap = not (name_box["x"] + name_box["width"] <= share_box["x"]
                      or share_box["x"] + share_box["width"] <= name_box["x"]
                      or name_box["y"] + name_box["height"] <= share_box["y"]
                      or share_box["y"] + share_box["height"] <= name_box["y"])
        assert not overlap, "чип доли перекрывает имя участника"
    finally:
        ctx.close()


def test_participants_without_any_known_share_get_one_note_not_n_chips(browser, base_url):
    """Этап 5, П2''''': «Доля не указана» на КАЖДОЙ строке — не пометка, а
    шум. Когда доля не известна ни у одного участника, страница показывает
    ОДНУ строку-пояснение над списком, а не чип на каждой карточке."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": True, "company_id": "gc2792a44", "company_name": "АФК «Система»",
                "entities": [{
                    "entity": {"id": 1, "legal_name": 'ПАО АФК "Система"', "inn": "7708004767"},
                    "reports": [], "report_years": [], "has_more_reports": False,
                    "has_more_events": False, "events": [],
                    "ownership": {
                        "available": True, "is_ao": True, "heading": "Учредители при регистрации",
                        "as_of": "2002-11-11",
                        "current": [
                            {"name": "Гончарук Александр Юрьевич", "type": "Физическое лицо",
                             "inn": None, "nominal_value_rub": 23625, "share_percent": None},
                            {"name": "Евтушенков Владимир Петрович", "type": "Физическое лицо",
                             "inn": None, "nominal_value_rub": 615312, "share_percent": None},
                        ],
                        "history": [], "has_more_history": False, "notice": "тест",
                    },
                }],
                "access": {"paid": True, "full_history": True, "downloads": True},
            }))
        ctx.route("**/api/companies/gc2792a44/fns*", fake_fns)
        pg = ctx.new_page()
        pg.goto(base_url + "/#/companies/gc2792a44", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        pg.click("[data-fnstab='ownership']")
        pg.wait_for_timeout(300)
        assert pg.locator(".owner-share").count() == 0, "без известных долей чипов быть не должно"
        assert "доли в этой выписке не раскрыты" in pg.inner_text("#app").lower()
    finally:
        ctx.close()


def test_bank_profile_shows_cbr_block_instead_of_fns_grid(browser, base_url):
    """Этап 6, П4-6: банк не сдаёт коммерческую БФО в общем порядке — вместо
    пустой сетки ФНС на его странице показывается то, что банк САМ публикует
    перед ЦБ (форма 806/102). Живой Сбербанк (g28ff15bb) уже проверен вручную
    (скриншот 390px) — здесь сеть подменена, чтобы тест не зависел от того,
    опубликовал ли ЦБ новый квартал именно сегодня, и проверял оба ответа
    /fns сразу (сопоставлено юрлицо и нет — оба несут category:"bank")."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": False, "hidden": False, "company_id": "g28ff15bb",
                "company_name": "Сбербанк", "configured": True, "category": "bank",
                "reason": "Кредитная организация — бухгалтерскую отчётность в общем порядке "
                          "банки не сдают, только по отдельной форме перед Банком России.",
            }))

        def fake_finance(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "g28ff15bb": {
                    "regnum": 1481, "legal_name": "Публичное акционерное общество «Сбербанк России»",
                    "as_of_balance": "2026-04-01", "assets_rub": 65137327668000,
                    "assets_rub_prior_year": 65210686723000, "equity_rub": 8627750211000,
                    "equity_rub_prior_year": 8115080880000,
                    "as_of_profit": "2026-07-01", "net_profit_rub": 995264348000,
                },
            }))
        ctx.route("**/api/companies/g28ff15bb/fns*", fake_fns)
        ctx.route("**/static/data/bank_finance.json*", fake_finance)
        # Этап 8, П2-8: mountCompanyFns грузит оба файла параллельно —
        # без явного мока полная таблица тянула бы реальный
        # bank_full_balance.json с диска и делала бы этот тест зависимым
        # от того, что в нём лежит сегодня; здесь проверяется только сводка.
        ctx.route("**/static/data/bank_full_balance.json*",
                   lambda route: route.fulfill(status=200, content_type="application/json", body="{}"))
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_viewport_size({"width": 360, "height": 900})
        pg.goto(base_url + "/#/companies/g28ff15bb", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        body = pg.inner_text("#fns-company").lower()
        assert "банк россии" in body
        assert "65,1 трлн" in body or "65.1 трлн" in body
        assert "8,6 трлн" in body or "8.6 трлн" in body
        assert "995,3 млрд" in body or "995.3 млрд" in body
        assert "источник: фнс" not in body, "у банка не должно остаться сетки ФНС"
        assert "не отслеживает акционеров" not in body
        assert not errors, "pageerror при рендере блока ЦБ: %s" % errors
        over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert over == 0, "блок ЦБ переполняет экран на 360px: %d" % over
    finally:
        ctx.close()


def test_bank_profile_without_cbr_data_shows_honest_reason(browser, base_url):
    """Этап 6, П4-6: банк известен (`category:"bank"`), но данных ЦБ пока
    нет (`bank_finance.json` не несёт этого company_id — например, свежая
    запись в реестре, синхронизация ещё не прогонялась) — честная короткая
    строка вместо пустой сетки метрик с прочерками."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": False, "hidden": False, "company_id": "g28ff15bb",
                "company_name": "Сбербанк", "configured": True, "category": "bank",
                "reason": "Кредитная организация — бухгалтерскую отчётность в общем порядке "
                          "банки не сдают, только по отдельной форме перед Банком России.",
            }))

        def fake_finance(route):
            route.fulfill(status=200, content_type="application/json", body="{}")
        ctx.route("**/api/companies/g28ff15bb/fns*", fake_fns)
        ctx.route("**/static/data/bank_finance.json*", fake_finance)
        ctx.route("**/static/data/bank_full_balance.json*",
                   lambda route: route.fulfill(status=200, content_type="application/json", body="{}"))
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/companies/g28ff15bb", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        assert pg.locator("#fns-company .fns-shell").count() == 0, "без данных ЦБ сетка метрик не должна рисоваться"
        body = pg.inner_text("#fns-company").lower()
        assert "кредитная организация" in body
        assert not errors, "pageerror при рендере честного состояния банка без данных ЦБ: %s" % errors
    finally:
        ctx.close()


def test_bank_profile_shows_full_balance_sheet_below_summary_tiles(browser, base_url):
    """Этап 8, П2-8: партнёр вживую попросил не только сводные плитки, а
    полный баланс («Активы и пассивы, 1-2 странички… ОСВ, отчёт о финансовых
    результатах не надо»). Проверяем все три раздела на экране, отрицательное
    значение со знаком минус (учит регэксп с `-`), пустую строку без данных
    (не показана вовсе — «Инвестиции в дочерние…» у Сбербанка) и отсутствие
    переполнения на 360px с самым длинным названием статьи (193 знака)."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": False, "hidden": False, "company_id": "g28ff15bb",
                "company_name": "Сбербанк", "configured": True, "category": "bank",
                "reason": "Кредитная организация — бухгалтерскую отчётность в общем порядке "
                          "банки не сдают, только по отдельной форме перед Банком России.",
            }))

        def fake_finance(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "g28ff15bb": {"regnum": 1481, "legal_name": "ПАО Сбербанк", "as_of_balance": "2026-04-01",
                              "assets_rub": 65137327668000, "assets_rub_prior_year": 65210686723000,
                              "equity_rub": 8627750211000, "equity_rub_prior_year": 8115080880000},
            }))

        def fake_full_balance(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "g28ff15bb": {
                    "regnum": 1481, "legal_name": "ПАО Сбербанк", "as_of": "2026-04-01",
                    "sections": [
                        {"title": "I. Активы", "rows": [
                            {"num": "1", "name": "Денежные средства", "note": "",
                             "period_rub": 702499267000, "prior_year_rub": 701792637000},
                            {"num": "8", "name": "Инвестиции в дочерние и зависимые организации",
                             "note": "", "period_rub": None, "prior_year_rub": None},
                            {"num": "14", "name": "Всего активов", "note": "",
                             "period_rub": 65137327668000, "prior_year_rub": 65210686723000},
                        ]},
                        {"title": "II. Пассивы", "rows": [
                            {"num": "24", "name": "Всего обязательств", "note": "",
                             "period_rub": 56509577457000, "prior_year_rub": 57095605843000},
                        ]},
                        {"title": "III. Источники собственных средств", "rows": [
                            {"num": "29", "name": "Переоценка финансовых активов, оцениваемых по справедливой "
                                                   "стоимости через прочий совокупный доход, уменьшенная на "
                                                   "отложенное налоговое обязательство (увеличенная на "
                                                   "отложенный налоговый актив)",
                             "note": "", "period_rub": -311872957000, "prior_year_rub": -333059648000},
                            {"num": "38", "name": "Всего источников собственных средств", "note": "",
                             "period_rub": 8627750211000, "prior_year_rub": 8115080880000},
                        ]},
                    ],
                },
            }))
        ctx.route("**/api/companies/g28ff15bb/fns*", fake_fns)
        ctx.route("**/static/data/bank_finance.json*", fake_finance)
        ctx.route("**/static/data/bank_full_balance.json*", fake_full_balance)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_viewport_size({"width": 360, "height": 900})
        pg.goto(base_url + "/#/companies/g28ff15bb", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        body = pg.inner_text("#fns-company")
        body_l = body.lower()
        assert "бухгалтерский баланс" in body_l
        assert "i. активы" in body_l and "ii. пассивы" in body_l
        assert "iii. источники собственных средств" in body_l
        assert "денежные средства" in body_l
        assert "инвестиции в дочерние" not in body_l, "строка без данных не должна рисоваться"
        assert "−311,9 млрд" in body or "-311,9 млрд" in body, "отрицательное значение должно нести знак минус"
        assert not errors, "pageerror при рендере полного баланса: %s" % errors
        over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert over == 0, "полный баланс переполняет экран на 360px: %d" % over
    finally:
        ctx.close()


def test_company_profile_full_bfo_toggle_shows_and_hides_full_statement(browser, base_url):
    """Этап 8, П3-8: та же просьба, что у банков, только для обычных
    компаний — «не только эти показатели, а все из БФО». Кнопка «Показать
    полную БФО» скрыта по умолчанию (родня уже применённому правилу
    «скрытые состояния проверяются отдельно»), по клику рисует секции;
    длинное название статьи и отрицательное значение (реальные из формы
    ОДДС/финрезультатов) не должны переполнять экран на 360px."""
    ctx = browser.new_context()
    try:
        def fake_fns(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "available": True, "company_id": "yandex", "company_name": "Яндекс",
                "entities": [{
                    "entity": {"id": 1, "legal_name": 'ООО "ЯНДЕКС"', "inn": "7736207543"},
                    "reports": [{
                        "year": 2024, "revenue_rub": 544_580_000_000, "net_profit_rub": -11_680_000_000,
                        "assets_rub": 565_500_000_000, "equity_rub": 129_300_000_000,
                        "full_lines": [
                            {"title": "I. Внеоборотные активы", "rows": [
                                {"code": "1110", "name": "Нематериальные активы", "value_rub": 7_666_406_000},
                                {"code": "1100", "name": "Итого по разделу I", "value_rub": 197_597_977_000},
                            ]},
                            {"title": "Отчёт о финансовых результатах", "rows": [
                                {"code": "2110", "name": "Выручка", "value_rub": 544_580_000_000},
                                {"code": "2400", "name": "Чистая прибыль (убыток)", "value_rub": -11_680_000_000},
                            ]},
                            {"title": "Денежные потоки от инвестиционных операций", "rows": [
                                {"code": "4213", "name": "от возврата предоставленных займов, от продажи "
                                                          "долговых ценных бумаг (прав требования денежных "
                                                          "средств к другим лицам)", "value_rub": 1_200_000_000},
                            ]},
                        ],
                    }],
                    "report_years": [2024], "has_more_reports": False, "has_more_events": False,
                    "events": [], "ownership": {"available": False},
                }],
                "access": {"paid": True, "full_history": True, "downloads": True},
                "disclaimer": "Показатели относятся к указанному юридическому лицу по РСБУ.",
            }))
        ctx.route("**/api/companies/yandex/fns*", fake_fns)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_viewport_size({"width": 360, "height": 900})
        pg.goto(base_url + "/#/companies/yandex", wait_until="networkidle")
        pg.wait_for_timeout(1200)
        pg.click('[data-fnstab="finance"]')
        pg.wait_for_timeout(300)
        assert pg.locator("#toggleFullLines").count() == 1
        assert pg.locator("#full-lines table").count() == 0, "полная БФО не должна рисоваться до клика"
        pg.click("#toggleFullLines")
        pg.wait_for_timeout(300)
        body = pg.inner_text("#full-lines")
        body_l = body.lower()
        assert "нематериальные активы" in body_l
        assert "выручка" in body_l
        assert "от возврата предоставленных займов" in body_l, "длинная строка ОДДС должна попасть на экран"
        assert "−11,7 млрд" in body or "-11,7 млрд" in body, "отрицательная чистая прибыль должна нести знак минус"
        assert not errors, "pageerror при рендере полной БФО: %s" % errors
        over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert over == 0, "полная БФО переполняет экран на 360px: %d" % over
        # Повторный клик скрывает блок обратно, не убирая его из DOM (та же
        # ленивая перерисовка, что и у банковской схемы/группы).
        pg.click("#toggleFullLines")
        pg.wait_for_timeout(200)
        assert not pg.locator("#full-lines").is_visible()
    finally:
        ctx.close()


def test_advisor_catalogue_shows_no_practice_categories(page, base_url):
    """«С-hi», «К-hi», «mid» — наша внутренняя разметка, а не факт о фирме.

    Она нигде не подтверждена источником и делит каталог по признаку, которого
    читатель не выбирал. Раз её сняли с экрана, её не должно остаться ни в
    карточках, ни в фильтрах, ни на странице фирмы.
    """
    visit(page, base_url, "#/advisors")
    body = page.inner_text("#app").lower()
    for slug in ("категории практики", "все категории", "сопровождение сделок — крупный"):
        assert slug not in body, f"категории остались на экране: {slug}"
    visit(page, base_url, "#/advisors/alrud")
    assert "групп" not in page.inner_text(".d-head").lower(), "категории остались на странице фирмы"
    visit(page, base_url, "#/")
    assert page.locator("#selagroup").count() == 0, "фильтр категорий остался в ленте"


def test_wordmark_returns_to_the_top(page, base_url):
    """На главной адрес от клика по логотипу не меняется — `hashchange` не
    срабатывает, `route()` не вызывается, и без отдельного обработчика кнопка
    выглядела мёртвой: человек уехал вниз по ленте и остался на месте."""
    visit(page, base_url, "#/")
    page.evaluate("window.scrollTo(0, 3000)")
    page.wait_for_timeout(300)
    assert page.evaluate("window.scrollY") > 500, "не удалось прокрутить главную"
    page.click(".top .wordmark")
    page.wait_for_timeout(1200)
    assert page.evaluate("window.scrollY") < 60, "логотип не вернул наверх"


def test_analytics_deal_type_filter(page, base_url):
    """База шире M&A: 128 инвестиций, 44 IPO, 43 продажи с торгов.

    Смотреть их отдельно осмысленно, поэтому тип — такой же фильтр, как период
    и отрасль, и он складывается с ними по И.
    """
    visit(page, base_url, "#/analytics")
    assert page.locator("#anTypeSel").count() == 1, "нет фильтра по типу сделки"
    whole = page.inner_text(".an-filters-note")

    page.select_option("#anTypeSel", "IPO")
    page.wait_for_timeout(600)
    assert not page.crashes, page.crashes[:3]
    only_ipo = page.inner_text(".an-filters-note")
    assert only_ipo != whole, "фильтр типа ничего не сузил"

    page.select_option("#anYearSel", "2025")
    page.wait_for_timeout(600)
    both = int(re.search(r"Показано (\d+)", page.inner_text(".an-filters-note")).group(1))
    ipo_all = int(re.search(r"Показано (\d+)", only_ipo).group(1))
    assert both < ipo_all, "тип и период не складываются по И"
    assert "тип «IPO»" in page.inner_text(".an-card p"), "подпись не называет тип выборки"

    page.click("#anReset")
    page.wait_for_timeout(600)
    assert page.inner_text(".an-filters-note") == whole, "сброс не снял фильтр типа"


def test_year_only_date_is_never_shown_as_the_first_of_january(page, base_url):
    """У 238 карточек день неизвестен, и врать о нём нельзя.

    Раньше там стояла заглушка «1 января»: сайт показывал день, которого не
    знал, лента ставила сделку первым числом, а помесячный график рисовал
    январский всплеск. Теперь в базе лежит «2023», и это надо ПОКАЗАТЬ как
    «2023 год» — `new Date("2023")` молча даёт первое января, поэтому дефект
    вернётся беззвучно, если формат перестанут ловить до разбора.
    """
    visit(page, base_url, "#/")
    ids = page.evaluate("() => DEALS.filter(d => /^\\d{4}$/.test(d.date)).map(d => d.id)")
    assert ids, "в базе не осталось карточек с годом без дня — проверять нечего"
    assert page.evaluate('() => fmtDate("2023")') == "2023 год"

    for deal_id in ids[:4]:
        visit(page, base_url, f"#/deal/{deal_id}")
        head = page.inner_text(".d-head").lower()
        assert "янв" not in head, f"{deal_id}: показан выдуманный день"
        assert "год" in head, f"{deal_id}: год не назван"

    # Помесячный график обязан их исключить и сказать об этом, а не молча
    # приписать январю: в этом и была вся беда.
    visit(page, base_url, "#/analytics")
    page.select_option("#anYearSel", "2025")
    page.wait_for_timeout(600)
    caption = page.inner_text(".an-card p")
    assert "известен только год" in caption, f"график молчит про них: {caption[:160]!r}"


def test_unknown_industry_is_labelled_as_an_industry(page, base_url):
    """«Не определена» в плашке рядом со статусом читается как второй статус.

    Значение легально с самого начала (оно есть в `INDUSTRIES`), но до 5 августа
    им не была помечена ни одна карточка из 1541 — поэтому дефект и не был
    виден. В шапке сделки плашки идут подряд: «ЗАКРЫТА · НЕ ОПРЕДЕЛЕНА», и без
    слова «отрасль» непонятно, что именно не определено.
    """
    visit(page, base_url, "#/")
    # Подпись проверяется всегда, даже когда карточек без отрасли в базе нет:
    # значение легально и появится снова, а тест, зависящий от наличия данных,
    # молча перестал бы что-либо проверять.
    assert page.evaluate("() => indLabel('Не определена')") == "Отрасль не определена"
    assert page.evaluate("() => indLabel('Банки')") == "Банки"
    ids = page.evaluate("() => DEALS.filter(d => d.ind === 'Не определена').map(d => d.id)")
    for deal_id in ids[:3]:
        visit(page, base_url, f"#/deal/{deal_id}")
        head = page.inner_text(".d-head").lower()
        assert "отрасль не определена" in head, f"{deal_id}: плашка не называет отрасль"
        # …и ссылки «Все сделки отрасли «Не определена»» быть не должно.
        body = page.inner_text("#app")
        assert "отрасли «Не определена»" not in body, f"{deal_id}: ссылка в никуда"


def test_status_plaque_is_colour_coded_by_stage(page, base_url):
    """Раздел B, 22 августа: «Обсуждается»/«Подписана»/«Согласование
    получено» раньше были тем же нейтральным серым, что и «Закрыта» —
    нельзя было на глаз отличить идущую сделку от закрытой. Новый статус в
    данные не заводили (решение владельца), только цвет плашки по уже
    существующему значению `status`. Проверяем чистую функцию (все
    словоформы статуса) и реальный DOM хотя бы по одной карточке каждого
    класса — цвет плашки в шапке сделки должен совпасть с классом,
    который знает сама функция, а не просто «что-то отрисовалось».
    """
    visit(page, base_url, "#/")
    classes = page.evaluate("""() => ({
        negotiations: statusClass('Обсуждается'),
        signed: statusClass('Подписана'),
        approval: statusClass('Согласование получено'),
        closed: statusClass('Закрыта'),
        cancelled: statusClass('Не состоялась'),
    })""")
    assert classes["negotiations"] == "negotiations"
    assert classes["signed"] == "pending"
    assert classes["approval"] == "pending"
    assert classes["closed"] == "closed"
    assert classes["cancelled"] == "cancelled"

    # Ожидаемый цвет обвода — те же переменные палитры, что и в CSS
    # (--steel/--accent и захардкоженный #B3402A у «cancelled», он был и до
    # этой правки). Три разных цвета обязаны быть РАЗНЫМИ друг от друга —
    # иначе на глаз статусы снова неотличимы, даже если классы расставлены
    # верно.
    expect_colour = {"negotiations": "rgb(51, 85, 107)",   # --steel
                     "closed": "rgb(29, 90, 68)",          # --accent
                     "cancelled": "rgb(179, 64, 42)"}       # #B3402A
    for want_class, colour_hex in expect_colour.items():
        deal_id = page.evaluate(
            "(c) => (DEALS.find(d => statusClass(d.status) === c) || {}).id", want_class)
        assert deal_id, f"нет карточки со статусом класса {want_class!r} — проверять не на чем"
        visit(page, base_url, f"#/deal/{deal_id}")
        cls = page.evaluate("() => document.querySelector('.d-head .status')?.className")
        assert cls and want_class in cls.split(), f"{deal_id}: плашка не несёт класс {want_class!r} ({cls!r})"
        colour = page.evaluate(
            "() => getComputedStyle(document.querySelector('.d-head .status')).borderColor")
        assert colour == colour_hex, f"{deal_id}: плашка {want_class!r} цвета {colour}, а не {colour_hex}"


def test_milestone_appears_in_feed_without_moving_the_deal_count(page, base_url):
    """Раздел A, 22 августа: веха — не вторая карточка, а строка ленты,
    указывающая на ту же сделку. `TOTAL_DEALS()`/аналитика обязаны считать
    ТОЛЬКО карточки — иначе одна сделка с двумя вехами задвоила бы себя в
    счётчике на главной. Строка вехи находится по чипу «Веха · …» и ведёт на
    актуальную карточку сделки (`#/deal/<id>`), а не на отдельную страницу
    этапа — читатель кликает по НОВОСТИ и должен увидеть сделку целиком.
    """
    visit(page, base_url, "#/")
    before = page.evaluate("() => TOTAL_DEALS()")
    marker = "УНИКАЛЬНЫЙ-ТЕКСТ-ВЕХИ-ДЛЯ-ТЕСТА"
    injected = page.evaluate("""(marker) => {
        const d = DEALS[0];
        d.events = Array.isArray(d.events) ? d.events : [];
        d.events.push({kind: "approval", date: "2026-01-15", id: d.id + "-approval-test",
                       newsworthy: true, headline: marker,
                       snapshot: {title: d.title, sum: d.sum || null}});
        return d.id;
    }""", marker)
    after = page.evaluate("() => TOTAL_DEALS()")
    assert after == before, f"веха изменила счётчик сделок: {before} -> {after}"

    # Поиск (а не постраничный список) — иначе строка вехи с датой в прошлом
    # может просто не попасть на первую страницу ленты среди сотен карточек.
    page.crashes.clear()
    page.evaluate("(marker) => { feedQuery = marker; feedPage = 1; renderFeedList(); }", marker)
    page.wait_for_timeout(300)
    body = page.inner_text("#feedlist")
    # `.status` рисуется CSS'ом заглавными (text-transform:uppercase) —
    # inner_text отдаёт визуальный регистр, а не исходный текст DOM.
    assert "ВЕХА · СОГЛАСОВАНИЕ" in body.upper(), f"чип вехи не найден в ленте: {body[:300]!r}"
    assert marker in body

    page.click(f"text={marker}")
    page.wait_for_timeout(500)
    ok = f"#/deal/{injected}" in page.url
    crashes = list(page.crashes)

    # `page` — общий на всю сессию (session-scoped), а хеш-переход не
    # перезагружает JS-состояние: инъекция в DEALS[0] иначе осталась бы
    # навсегда и задела бы ДРУГИЕ тесты этого файла (тот самый урок из
    # CLAUDE.md — «прогон одного теста не проверка изоляции», только с
    # мутацией глобального массива вместо DOM/модалки). Откатываем ДО assert,
    # чтобы откат сработал даже при падении проверок выше.
    page.evaluate("""() => {
        const d = DEALS.find(x => Array.isArray(x.events) && x.events.some(e => e.id && e.id.endsWith("-approval-test")));
        if(d) d.events = d.events.filter(e => !(e.id && e.id.endsWith("-approval-test")));
        feedQuery = ""; feedPage = 1; renderFeedList();
    }""")

    assert ok, f"клик по вехе увёл не на карточку сделки: {page.url}"
    assert not crashes, crashes[:3]


def test_preview_route_renders_a_pending_card(page, base_url, browser):
    """Черновик виден по прямой ссылке и НЕ виден в ленте.

    Модерация держится на том, что карточка из pending.json не существует для
    сайта нигде, кроме #/preview/<id>: попади она в ленту или поиск до решения
    владельца, предпросмотр перестал бы быть предпросмотром.
    """
    import json as _json
    pending_path = Path("static/data/pending.json")
    backup = pending_path.read_text(encoding="utf-8") if pending_path.exists() else None
    card = {"id": "gtest-preview", "date": "2026-08-05",
            "title": "Тестовая компания «Альфа-Превью» купила завод «Бета-Превью»",
            "ind": "ИТ и интернет", "type": "M&A", "status": "Закрыта",
            "src": [["источник", "https://example.invalid/preview"]],
            "eco": {"sum": "—", "share": "—", "val": "—", "target_fin": "—",
                     "fin": "—", "rationale": "—", "context": "—", "finadv": "—"},
            "law": {"struct": "—", "appr": "—", "adv": [], "terms": "—"},
            "pending_since": "2026-08-05T00:00:00+00:00"}
    pending_path.write_text(_json.dumps({"cards": [card]}, ensure_ascii=False), encoding="utf-8")
    try:
        visit(page, base_url, "#/preview/gtest-preview")
        page.wait_for_timeout(900)
        text = page.inner_text("#app")
        assert "Альфа-Превью" in text, "черновик не отрисовался"
        assert "Черновик" in text, "нет плашки о том, что это черновик"
        # НАЛИЧИЕ В DOM — НЕ ВИДИМОСТЬ, И ЭТО ВИДНО ТОЛЬКО НА ХОЛОДНОЙ
        # ЗАГРУЗКЕ. `renderPreview` — единственный асинхронный рендер: он ждёт
        # fetch(pending.json), а проявление (`.reveal` -> `.reveal.in`)
        # запускается в конце `route()`, то есть по разметке состояния
        # загрузки. На тёплой странице (общий `page` уже открыт) pending.json
        # успевает вернуться раньше кадра, и дефекта не видно; при переходе по
        # ссылке из телеграма страница грузится с нуля, параллельно тянется
        # база на 774 КБ — pending.json приходит позже, и карточка остаётся с
        # `opacity:0` НАВСЕГДА: `inner_text` её видит, человек нет.
        # Проверено на себе: без `rerun()` в конце `renderPreview` здесь 12.
        cold = browser.new_context()
        try:
            cpg = cold.new_page()
            cpg.goto(base_url + "/#/preview/gtest-preview", wait_until="networkidle")
            cpg.wait_for_timeout(1500)
            hidden = cpg.evaluate(
                "() => [...document.querySelectorAll('#app .reveal')]"
                ".filter(el => getComputedStyle(el).opacity === '0').length")
            assert "Альфа-Превью" in cpg.inner_text("#app")
            assert hidden == 0, f"черновик отрисован, но невидим: {hidden} блоков с opacity:0"
        finally:
            cold.close()
        # В ленте и поиске черновика нет.
        assert page.evaluate("() => DEALS.some(d => d.id === 'gtest-preview')") is False
        # Несуществующий черновик — честное сообщение, а не пустой экран.
        visit(page, base_url, "#/preview/gtest-net-takogo")
        page.wait_for_timeout(700)
        assert "не найден" in page.inner_text("#app").lower()
    finally:
        if backup is None:
            pending_path.unlink(missing_ok=True)
        else:
            pending_path.write_text(backup, encoding="utf-8")


def test_slow_load_hint_mentions_vpn(page, base_url):
    """Долгая загрузка объясняется, а не просто крутится.

    Определить VPN из браузера нельзя, и плашка этого не утверждает: она
    напоминает, что сервер в России, и РЕКОМЕНДУЕТ выключить VPN. Появляется
    только после 8 секунд ожидания — при обычной загрузке её никто не видит.
    """
    visit(page, base_url, "#/")
    html = page.evaluate("() => { slowLoad = true; return loadingHtml('карточка'); }")
    assert "VPN" in html and "display:block" in html
    assert "Росси" in html
    # До восьми секунд подсказка есть в разметке, но скрыта.
    html_fast = page.evaluate("() => { slowLoad = false; return loadingHtml('карточка'); }")
    assert "display:none" in html_fast


def test_feed_is_ordered_by_publication_date_not_deal_date(page, base_url):
    """В ленте — дата публикации, в карточке — дата сделки (просьба владельца).

    До правки лента и сортировалась, и подписывалась датой САМОЙ СДЕЛКИ: карточка,
    одобренная 6 августа, но описывающая сделку мая, вставала сотой строкой. Владелец
    искал новое, видел наверху 5 августа и решал, что приток встал.
    """
    visit(page, base_url, "#/")
    page.wait_for_timeout(2500)
    rows = page.evaluate("""() => {
      const items = DEALS.map(d => ({added: d.added || '', date: d.date || ''}));
      return {
        добавлено: items.map(x => x.added).sort().reverse()[0],
        первая_в_ленте: (() => {
          const html = unifiedFeed()[0] || '';
          const m = html.match(/class="label num">([^<]+)</);
          return m ? m[1] : '';
        })(),
      };
    }""")
    # Верх ленты подписан датой САМОГО СВЕЖЕГО ПОПОЛНЕНИЯ, а не самой свежей сделки.
    assert rows["первая_в_ленте"], "в ленте нет даты"
    newest_added = page.evaluate(
        "() => DEALS.map(d=>d.added||'').filter(Boolean).sort().reverse()[0]")
    expected = page.evaluate("d => fmtDate(d)", newest_added)
    assert rows["первая_в_ленте"] == expected, (
        "лента начинается не с последнего пополнения: %r вместо %r"
        % (rows["первая_в_ленте"], expected))

    # А в самой карточке стоит дата сделки — её подменять датой публикации нельзя.
    probe = page.evaluate("""() => {
      const d = DEALS.find(x => x.added && x.date && x.added.slice(0,7) !== x.date.slice(0,7));
      return d ? {id: d.id, date: d.date, added: d.added} : null;
    }""")
    assert probe, "не нашлось карточки, у которой месяц сделки и месяц публикации различаются"
    visit(page, base_url, "#/deal/" + probe["id"])
    page.wait_for_timeout(700)
    # Шапка карточки набрана капителью (text-transform), поэтому сравниваем без регистра.
    head = page.inner_text(".d-head").lower()
    assert page.evaluate("d => fmtDate(d)", probe["date"]).lower() in head, (
        "в карточке нет даты сделки: %r" % head[:200])
    assert page.evaluate("d => fmtDate(d)", probe["added"]).lower() not in head, (
        "в карточке стоит дата публикации вместо даты сделки")


def test_company_cards_align_their_divider(page, base_url):
    """Линия над цифрами — на одной высоте у всех карточек каталога.

    Раньше её место определяли длина имени и длина описания, и ряд выглядел
    рваным: у «Сбербанка» описание в пять строк, у «Яндекса» — в три.
    """
    visit(page, base_url, "#/companies")
    page.wait_for_timeout(2500)
    tops = page.evaluate("""() => [...document.querySelectorAll('.co-card')].slice(0,24).map(c => {
      const n = c.querySelector('.co-nums');
      return Math.round(n.getBoundingClientRect().top - c.getBoundingClientRect().top);
    })""")
    assert len(tops) >= 12, "карточек компаний слишком мало для проверки"
    assert len(set(tops)) == 1, "линия стоит на разной высоте: %r" % sorted(set(tops))


def test_company_activity_names_what_it_counts(page, base_url):
    """«1 за год» не называло, чего именно один. Единица измерения склоняется."""
    visit(page, base_url, "#/companies")
    page.wait_for_timeout(2500)
    vals = page.evaluate("""() => [...document.querySelectorAll('.co-nums')].slice(0,40)
      .map(n => n.querySelector('.val').textContent.trim())""")
    assert vals, "не нашлось ни одной карточки компании"
    for v in vals:
        assert "за год" in v, "подпись активности потеряла период: %r" % v
        assert re.match(r"^\d+ (сделка|сделки|сделок) за год$", v), "неверное склонение: %r" % v
    # Правило склонения проверено на числах, которых может не быть на экране.
    for n, word in ((0, "сделок"), (1, "сделка"), (2, "сделки"), (5, "сделок"),
                    (11, "сделок"), (21, "сделка"), (22, "сделки"), (25, "сделок")):
        got = page.evaluate("n => plural(n,'сделка','сделки','сделок')", n)
        assert got == word, "plural(%d) = %r, ожидалось %r" % (n, got, word)


# ---------- замечания владельца с телефона (9 августа) ----------

def test_header_does_not_jump_while_scrolling(page, base_url):
    """Строка разделов зафиксирована, а не прячется при прокрутке.

    Раньше на главной шапка уезжала вверх, пока не проскроллено 55% экрана.
    С телефона это читается как дёрганье: разделы то есть, то нет, и попасть
    по ним пальцем во время прокрутки нельзя. Владелец: «блоки сверху не
    должны дёргаться вниз и вверх, они должны быть зафиксированы».
    """
    visit(page, base_url, "#/")
    tops = []
    for y in (0, 700, 1400, 300, 0):
        page.evaluate(f"window.scrollTo(0,{y})")
        page.wait_for_timeout(320)
        tops.append(page.evaluate(
            "() => Math.round(document.querySelector('.top').getBoundingClientRect().top)"))
    assert set(tops) == {0}, f"шапка ездит по вертикали при прокрутке: {tops}"


def test_scroll_to_feed_lands_below_fixed_header(page, base_url):
    """Этап 16, П5: прокрутка к ленте не прячет строку поиска под шапкой.

    Шапка `position:fixed` не занимает места в потоке, поэтому
    `feedAnchor.scrollIntoView()` (стрелка ↓ на герое, кнопка «Смотреть
    сделки») выравнивала верх #feed ровно по верху вьюпорта — то есть ПОД
    шапку. `scroll-margin-top` на #feed чинит это для того же
    programmatic-скролла, что и для якорных ссылок браузера.
    """
    visit(page, base_url, "#/")
    try:
        page.click(".hs-cue", force=True)
        page.wait_for_timeout(900)
        feed_top = page.evaluate("document.getElementById('feed').getBoundingClientRect().top")
        header_bottom = page.evaluate("document.querySelector('.top').getBoundingClientRect().bottom")
        assert feed_top >= header_bottom, (
            f"лента прячется под шапкой: верх ленты {feed_top}, низ шапки {header_bottom}")
    finally:
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(300)


def test_hero_dots_do_not_sit_on_the_text_on_short_screens(browser, base_url):
    """Точки слайдера не ложатся на текст на невысоком экране.

    Точки стоят `position:absolute; bottom:34px` и в поток не входят. В
    браузере телеграма высота окна около 640px — текст доходил до них, и
    подпись «сделки с 2022 года, база продолжает пополняться» читалась
    сквозь кружки (скриншот владельца 9 августа). Проверять надо именно
    низкий экран: на 844px перекрытия нет, и обычный прогон дефект не видит.
    """
    ctx = browser.new_context(viewport={"width": 393, "height": 640})
    try:
        pg = ctx.new_page()
        pg.goto(base_url + "/#/", wait_until="networkidle")
        pg.wait_for_timeout(2200)
        gap = pg.evaluate("""() => {
          const inr = document.querySelector('.hs-slide.on .hs-in').getBoundingClientRect();
          const d = document.querySelector('.hs-dots').getBoundingClientRect();
          return Math.round(d.top - inr.bottom);
        }""")
        assert gap >= 0, f"содержимое героя заходит на точки слайдера ({gap}px)"
        # И ничего не обрезано на полуслове: приписка на низком экране скрыта целиком.
        clipped = pg.evaluate("""() => {
          const s = document.querySelector('.hs-slide.on');
          const inr = s.querySelector('.hs-in').getBoundingClientRect();
          return [...s.querySelectorAll('h1,p,.hs-cta')]
            .filter(n => { const r = n.getBoundingClientRect();
                           return r.width > 0 && r.bottom > inr.bottom + 1; })
            .map(n => n.className || n.tagName);
        }""")
        assert not clipped, f"обрезано по нижней границе: {clipped}"
    finally:
        ctx.close()


def test_company_all_deals_expands_in_place_without_a_modal(page, base_url):
    """«Все сделки» на странице компании раскрываются списком, а не окном.

    Модальное окно на компьютере превращалось в узкую коробку посреди
    широкого экрана («на компьютере выглядит ужасно» — владелец). Заодно
    уходит риск из CLAUDE.md: диалог живёт вне `#app`, переживает смену
    экрана и молча перехватывает клики.
    """
    visit(page, base_url, "#/companies/yandex")
    page.wait_for_timeout(600)
    assert page.evaluate("() => document.getElementById('companyDealsAll').innerHTML.length") == 0
    page.click("#openCompanyDeals")
    page.wait_for_timeout(500)
    state = page.evaluate("""() => ({
      rows: document.querySelectorAll('#companyDealsAll .deal-list-item').length,
      modal: !!document.querySelector('.dialog-backdrop'),
      label: document.getElementById('openCompanyDeals').textContent.trim(),
    })""")
    assert not state["modal"], "список всё ещё открывается модальным окном"
    assert state["rows"] >= 3, f"в раскрытом списке всего {state['rows']} строк"
    assert "Свернуть" in state["label"]
    page.click("#openCompanyDeals")
    page.wait_for_timeout(350)
    assert page.evaluate("() => document.getElementById('companyDealsAll').innerHTML.length") == 0


def test_section_row_starts_from_the_first_item(page, base_url):
    """Строка разделов не уезжает вбок, пряча начало списка.

    `mark()` центрировал активный пункт — шесть разделов занимают 561px при
    238px видимых, и на «Консультантах» центрирование прокручивало строку на
    216px: «Сделки» и «Компании» уходили под логотип. Владелец прислал ровно
    эти экраны. Теперь прокрутка минимальная — только если пункт не виден.
    """
    page.set_viewport_size({"width": 393, "height": 852})
    try:
        for hash_ in ("#/", "#/companies"):
            visit(page, base_url, hash_)
            page.wait_for_timeout(500)
            left = page.evaluate("() => Math.round(document.querySelector('.top nav').scrollLeft)")
            assert left == 0, f"{hash_}: строка разделов прокручена на {left}px"
        # На дальнем разделе прокрутка допустима, но минимальная — не в конец.
        visit(page, base_url, "#/advisors")
        page.wait_for_timeout(500)
        left = page.evaluate("() => Math.round(document.querySelector('.top nav').scrollLeft)")
        assert left < 120, f"строка уехала на {left}px ради активного пункта"
    finally:
        page.set_viewport_size({"width": 1280, "height": 1000})


def test_web_search_failure_does_not_blame_missing_variables(page, base_url):
    """Сообщение о сбое не называет причину, которой не проверяло.

    Стояло «поиск включится, когда будут заданы YANDEX_API_KEY и
    YANDEX_FOLDER_ID» — и владелец увидел это при ЗАДАННЫХ переменных
    (живой /api/ask в тот же день отвечал за 26,7 с). Человек пошёл чинить
    то, что не сломано. Теперь фронтенд спрашивает /health и говорит правду.
    """
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "включится, когда в переменных приложения" not in html
    assert "не ответил вовремя" in html and '"/health"' in html


def test_deal_team_is_grouped_by_side_without_duplicate_firms(page, base_url):
    """Замечания владельца 31 августа 2026 на карточке MBO «ВымпелКома»
    (g64a94e27): «два раза АЛРУД» и «юридический и финансовый сливаются —
    надо поделить на стороны». Команда сделки группируется по сторонам,
    одна фирма на одной стороне показывается один раз, финансовый
    консультант стоит рядом с юридическим той же стороны."""
    visit(page, base_url, "#/deal/g64a94e27")
    page.wait_for_selector(".team")
    # text_content, а не inner_text: заголовки колонок набраны капителью через CSS
    team = page.locator(".team").text_content()
    assert "Со стороны покупателя" in team and "Со стороны продавца" in team
    assert len(re.findall(r"АЛРУД|ALRUD", team)) == 1, team
    seller_col = next(c for c in page.locator(".team-col").all() if "продавца" in c.text_content())
    seller_text = seller_col.text_content()
    assert "АЛРУД" in seller_text and "Aspring Capital" in seller_text, seller_text
    assert "юридический" in seller_text.lower() and "финансовый" in seller_text.lower()
    # плашка темы объясняет, что это за кнопка
    assert "Ещё сделки с той же особенностью" in page.locator(".theme-chips").text_content()
    # вкладка «Юрист»: расчёты по облигациям ушли к экономисту, условия — наш текст без «как предполагал „Ъ“»
    page.click(".lens [data-l='law']")
    page.wait_for_timeout(400)
    law = page.inner_text("#app")
    assert "как и предполагал" not in law.lower()
    assert "Сделка не предусматривает соглашений об обратном выкупе" in law
    assert "замещающие" not in law


def test_firm_page_reads_the_advised_side_from_context(page, base_url):
    """Владелец 5 сентября 2026 на странице Nextons: «Продавец 4, Покупатель 4,
    ещё у 10 сделок сторона не названа — это странно, неужели из контекста
    не понятно, с какой стороны они были?» Понятно: в пояснении стояло «за
    продавца», «консультировала Ingka», «консультант эмитента» — но страница
    фирмы читала только текст роли, своим узким правилом. Теперь сторона
    считается тем же advSide, что и «Команда сделки» на карточке: роль,
    имена сторон сделки (с псевдонимами профиля) и пояснение — а у IPO,
    выкупа и привлечения средств есть третий ответ, «сама компания».
    Замер по всем 229 парам фирма-сделка: известная сторона 134 → 205,
    у Nextons неизвестных 10 → 3 (у тех трёх источник действительно молчит)."""
    visit(page, base_url, "#/advisors/nextons")
    page.wait_for_selector(".an-card")
    card = next(c for c in page.locator(".an-card").all() if "За кого выступала" in c.text_content())
    text = card.text_content()
    rows = {r.locator(".an-key").text_content(): int(r.locator(".an-val").text_content())
            for r in card.locator(".an-row").all()}
    assert rows.get("Покупатель", 0) >= 5 and rows.get("Продавец", 0) >= 5, rows
    assert any(k.startswith("Сама компания") for k in rows), rows
    m = re.search(r"Ещё у (\d+) сдел", text)
    assert m and int(m.group(1)) <= 3, text
    assert "сторона не названа" not in text and "известно только" not in text, text
    # Та же сторона на карточке: «консультировала Ingka» — продавца, Иванян — покупателя
    visit(page, base_url, "#/deal/g4f1b5909")
    page.wait_for_selector(".team")
    cols = {c.locator(".team-kind").text_content(): c.text_content() for c in page.locator(".team-col").all()}
    assert "Nextons" in cols.get("Со стороны продавца", ""), cols
    assert "Иванян" in cols.get("Со стороны покупателя", ""), cols
    # IPO: эмитент — «сама компания», банки-организаторы — своя колонка, не «не уточнена»
    visit(page, base_url, "#/deal/g6206d0f7")
    page.wait_for_selector(".team")
    cols = {c.locator(".team-kind").text_content(): c.text_content() for c in page.locator(".team-col").all()}
    assert "Nextons" in cols.get("Со стороны эмитента", ""), cols
    assert "VERBA" in cols.get("Со стороны организаторов и кредиторов", ""), cols
    assert "Сторона не уточнена" not in cols, cols
    # Финансирование: подпись колонки — по типу сделки, «(не кредитор)» — не кредитор
    visit(page, base_url, "#/deal/ga46c5b15")
    page.wait_for_selector(".team")
    cols = {c.locator(".team-kind").text_content(): c.text_content() for c in page.locator(".team-col").all()}
    assert "Orion" in cols.get("Со стороны инвестора", ""), cols
    assert "ККМП" in cols.get("Со стороны получателя финансирования", ""), cols
    assert "Со стороны покупателя" not in cols, cols


def test_feed_search_suggests_by_first_letters_and_hides_filters_behind_a_button(page, base_url):
    """Просьба владельца 31 августа 2026: «предлагать должно по первым
    буквам», а категории — за кнопкой «Фильтры», а не на виду.
    3 сентября 2026: «в разделе сделок пусть поиск ищет именно по сделкам,
    а в разделе компаний именно по компаниям» — над лентой подсказки только
    из карточек сделок (и уводят на карточку), в каталоге — только профили."""
    visit(page, base_url, "#/deals")
    page.wait_for_selector("#feedq")
    assert page.inner_text("#advtoggle").strip() == "Фильтры"
    page.fill("#feedq", "Магн")
    page.wait_for_selector("#feedac .ac-item", timeout=5000)
    items = [x.inner_text() for x in page.locator("#feedac .ac-item").all()]
    # Подпись справа («сделка · дата»), а не весь текст: в заголовке сделки
    # слово «компания» встречается само по себе.
    notes = [x.inner_text() for x in page.locator("#feedac .ac-note").all()]
    assert notes and all(n.startswith("сделка") for n in notes), notes
    assert any("Магнит" in x for x in items), items
    assert len(items) <= 6
    # подсказки рисуются поверх ленты, а не под ней
    z = page.evaluate("getComputedStyle(document.querySelector('.feed-search')).zIndex")
    assert z not in ("auto", "0"), z
    page.locator("#feedac .ac-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(500)
    h = page.evaluate("location.hash")
    assert h.startswith("#/deal/") and "undefined" not in h, h
    assert not page.crashes

    visit(page, base_url, "#/companies")
    page.wait_for_selector("#coq")
    try:
        page.fill("#coq", "Магн")
        page.wait_for_selector("#coac .ac-item", timeout=5000)
        items = [x.inner_text() for x in page.locator("#coac .ac-item").all()]
        assert items and any("Магнит" in x for x in items), items
        assert not any("сделка ·" in x for x in items), items  # это компании, не карточки сделок
        assert not any("0 сделок" in x for x in items), items  # без сделок — «компания», а не «0 сделок»
        assert any("Магнит" in x and "сделок" in x for x in items), items  # id компании — ключ словаря, не поле профиля
        page.locator("#coac .ac-item").first.dispatch_event("mousedown")
        page.wait_for_timeout(500)
        h = page.evaluate("location.hash")
        assert h.startswith("#/companies/") and "undefined" not in h, h
    finally:
        # `coQuery` — глобальная переменная, хешем не сбрасывается (см. урок
        # «переход по хешу — не перезагрузка страницы для теста»).
        page.evaluate("coQuery = ''")
    assert not page.crashes


def test_company_cards_on_a_phone_keep_the_group_badge_inside_the_card(browser, base_url):
    """«Кривой формат» (владелец, 31 августа 2026, список компаний с телефона):
    бейдж «Группа компаний» стоял вне потока и срезался верхом карточки, а
    фиксированные высоты имени и описания оставляли пустые дыры в одной
    колонке. Проверяем на узком экране: бейдж внутри карточки целиком, имя
    из одной строки не тянет 60px, переполнения нет."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    try:
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base_url + "/#/companies", wait_until="networkidle")
        pg.wait_for_selector(".co-card")
        pg.wait_for_timeout(700)
        card = pg.locator(".co-card").first
        badge = card.locator(".co-group-badge")
        assert badge.count() == 1, "первая карточка (Сбербанк) должна быть группой"
        cb, bb = card.bounding_box(), badge.bounding_box()
        assert bb["y"] >= cb["y"] and bb["y"] + bb["height"] <= cb["y"] + cb["height"], (cb, bb)
        assert bb["x"] + bb["width"] <= cb["x"] + cb["width"]
        h3 = card.locator("h3").bounding_box()
        assert h3["height"] < 45, f"имя в одну строку занимает {h3['height']}px — фиксированная высота осталась"
        actions = card.locator(".co-actions").bounding_box()
        assert actions["height"] < 45, "кнопки должны стоять в ряд, а не столбиком"
        labels = [x.text_content() for x in card.locator(".co-nums .label").all()]
        for x in card.locator(".co-nums .label").all():
            assert x.bounding_box()["height"] < 22, f"подпись {x.text_content()!r} переносится на две строки"
        assert pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        assert not errors
    finally:
        ctx.close()


def test_deal_lenses_split_advisors_by_kind(page, base_url):
    """«В экономисте надо делать финансовых консультантов, в юристе
    юридических; если нажать юриста, то Алор брокера нет — надо чтобы
    соответствовало» (владелец, 31 августа 2026). Один список на карточку,
    по вкладкам — по виду консультанта, а не по полю, где он лежал."""
    visit(page, base_url, "#/deal/g64a94e27")
    page.click(".lens [data-l='law']")
    page.wait_for_timeout(400)
    law = page.locator("#app").text_content()
    assert "LEVEL Legal Services" in law and "АЛРУД" in law
    assert "Aspring" not in law and "Алор" not in law, "финансовые консультанты попали к юристу"
    page.click(".lens [data-l='eco']")
    page.wait_for_timeout(400)
    eco = page.locator("#app").text_content()
    assert "Aspring Capital" in eco and "Алор брокер" in eco
    assert "Финансовые консультанты" in eco
    # юридическая фирма у экономиста может встретиться только в списке источников, не в показателях
    assert "Юридический консультант" not in eco


# Даты — от РЕАЛЬНОГО "сейчас", а не зашитая дата: раньше здесь стояла
# буквальная строка "2026-09-03T08:00:00", и тест ломался сам собой, как
# только настенное время переваливало за полночь этой даты (группа
# "сегодня" превращалась в "вчера" без единой правки продукта или данных).
_STUB_TODAY = datetime.utcnow().strftime("%Y-%m-%dT08:00:00")
_STUB_TODAY_PLUS5S = datetime.utcnow().strftime("%Y-%m-%dT08:00:05")
_STUB_EARLIER = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%dT08:00:00")

THREADS_STUB = json.dumps([
    {"id": 1, "title": "Сделки Сбербанка за 2025 год", "context_type": "general",
     "context_id": None, "updated_at": _STUB_TODAY},
    {"id": 2, "title": "Кто консультировал Ленту", "context_type": "general",
     "context_id": None, "updated_at": _STUB_EARLIER},
])


THREAD_STUB = json.dumps({
    "id": 1, "title": "Сделки Сбербанка за 2025 год", "context_type": "general", "context_id": None,
    "messages": [
        {"role": "user", "body": "Что покупал Сбербанк в 2025 году?", "mode": "base",
         "created_at": _STUB_TODAY},
        {"role": "assistant", "body": "В базе «Компаса» за 2025 год — три сделки Сбербанка.",
         "mode": "base", "created_at": _STUB_TODAY_PLUS5S},
    ],
})


def _assistant_page(browser, base_url, width, height=844, signed_in=False, threads=None):
    """Отдельный контекст под экран ассистента: у страницы два состояния шапки
    (гость и вошедший) и своя раскладка на каждой ширине. Историю диалогов
    подменяем ответом сервера: без ключей к модели /api/ask диалоги не пишет,
    и живого списка в тестах взяться неоткуда."""
    ctx = browser.new_context(viewport={"width": width, "height": height},
                              is_mobile=width < 700, has_touch=width < 700)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
    if signed_in:
        email = f"chat-{uuid.uuid4().hex[:10]}@ui.test"
        r = pg.request.post(base_url + "/api/auth/register",
                            data={"email": email, "password": "secret123", "full_name": "Артем Тест"})
        assert r.status == 200, r.text()
    if threads is not None:
        pg.route("**/api/assistant/threads", lambda route: route.fulfill(
            status=200, content_type="application/json", body=threads))
        pg.route("**/api/assistant/threads/*", lambda route: route.fulfill(
            status=200, content_type="application/json", body=THREAD_STUB))
    pg.goto(base_url + "/#/assistant", wait_until="networkidle")
    pg.wait_for_selector("#chatShell")
    pg.wait_for_timeout(700)
    return ctx, pg, errors


def test_assistant_is_a_two_column_workspace_on_the_desktop(browser, base_url):
    """Партнёр 3 сентября 2026: «сейчас это довольно поганое окошко на одной
    странице… сделать как в клоде/чат гпт, с диалогами слева». На компьютере
    раздел занимает весь экран: слева панель диалогов, справа лента и поле
    ввода; футера на этой странице нет (он мешал бы ленте), но на соседних
    экранах он обязан остаться."""
    ctx, pg, errors = _assistant_page(browser, base_url, 1280, 1000)
    try:
        side = pg.locator(".chat-side").bounding_box()
        main = pg.locator(".chat-main").bounding_box()
        assert side and main, "панель диалогов или лента не отрисовались"
        assert side["x"] + side["width"] <= main["x"] + 1, "колонки наложились друг на друга"
        assert side["height"] > 400 and main["height"] > 400, "рабочее место не во всю высоту"
        assert pg.locator("#newThread").is_visible(), "кнопки «Новый диалог» не видно в панели"
        assert not pg.locator("footer").is_visible(), "футер занимает место у полноэкранной ленты"
        # Прокручивается лента, а не вся страница.
        assert pg.evaluate("getComputedStyle(document.getElementById('chatbox')).overflowY") == "auto"
        assert pg.evaluate(
            "document.documentElement.scrollHeight - window.innerHeight") <= 2, "страница выше окна"
        # Плашка сравнения компаний висит внизу экрана (position:fixed) и на
        # обычной странице просто лежит поверх её конца — здесь конец страницы
        # это поле ввода, и она накрыла бы его целиком.
        pg.evaluate("localStorage.setItem('kompas_compare_companies_v1',"
                    " JSON.stringify(Object.keys(COMPANIES).slice(0,2)))")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1200)
        tray = pg.locator(".compare-tray")
        assert tray.count() == 0 or not tray.is_visible(), "плашка сравнения накрыла поле ввода"
        pg.fill("#q", "проверка")
        assert pg.input_value("#q") == "проверка", "в поле ввода не напечатать"
        # Уходим с раздела — футер и плашка возвращаются, класс страницы снят.
        pg.goto(base_url + "/#/companies", wait_until="networkidle")
        pg.wait_for_timeout(2000)
        assert pg.locator("footer").is_visible(), "футер не вернулся на соседнем экране"
        assert pg.locator(".compare-tray").is_visible(), "плашка сравнения не вернулась"
        assert not pg.evaluate("document.body.classList.contains('chat-page')")
        assert not errors, errors
    finally:
        ctx.close()


@pytest.mark.parametrize("width", (360, 390))
def test_assistant_on_the_phone_is_one_column_with_a_drawer(browser, base_url, width):
    """На телефоне колонка одна, список диалогов — выдвижной ящик по кнопке
    «Диалоги». Закрытое и открытое состояния меряем ОБА (скрытые состояния
    проверяются отдельно): ящик не должен уметь толкать страницу вбок."""
    ctx, pg, errors = _assistant_page(browser, base_url, width, 780)
    try:
        over = lambda: pg.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth")
        side = pg.locator(".chat-side").bounding_box()
        assert side and side["x"] < -10, f"панель не спрятана за краем (x={side['x'] if side else None})"
        assert over() == 0, f"{width}px: горизонтальное переполнение при закрытом ящике"
        pg.click("#chatBurger")
        pg.wait_for_timeout(500)
        side = pg.locator(".chat-side").bounding_box()
        assert side and side["x"] >= -1, "ящик не выехал"
        assert pg.locator("#newThread").is_visible(), "в ящике не видно «Новый диалог»"
        assert over() == 0, f"{width}px: горизонтальное переполнение при открытом ящике"
        pg.click("#chatSideClose")
        pg.wait_for_timeout(500)
        side = pg.locator(".chat-side").bounding_box()
        assert side and side["x"] < -10, "ящик не закрылся"
        assert not errors, errors
    finally:
        ctx.close()


def test_assistant_guest_is_invited_to_sign_in_instead_of_the_thread_list(browser, base_url):
    """Гостю сохранять нечего — на месте списка диалогов приглашение войти."""
    ctx, pg, errors = _assistant_page(browser, base_url, 1280, 1000)
    try:
        assert pg.locator("#chatSignin").count() == 1
        assert "Войдите" in pg.inner_text("#chatSignin")
        assert pg.locator(".chat-thread").count() == 0
        assert not errors, errors
    finally:
        ctx.close()


def test_saved_dialogs_are_listed_in_the_side_panel_for_a_signed_in_user(browser, base_url):
    """У вошедшего в панели — его диалоги, сгруппированные по времени. Время
    сервер отдаёт по UTC без буквы Z; без её подстановки вечерний диалог
    оказался бы в «завтрашней» группе."""
    ctx, pg, errors = _assistant_page(browser, base_url, 1280, 1000,
                                      signed_in=True, threads=THREADS_STUB)
    try:
        assert pg.locator("#chatSignin").count() == 0, "вошедшему не нужно приглашение войти"
        titles = pg.locator(".chat-thread").all_inner_texts()
        assert len(titles) == 2, titles
        assert "Сделки Сбербанка за 2025 год" in titles[0]
        groups = [g.strip().lower() for g in pg.locator(".chat-group").all_inner_texts()]
        assert groups and groups[0] == "сегодня", groups
        # Диалог из списка открывается в ленте: реплики на месте, счётчик тоже.
        pg.locator(".chat-thread").first.click()
        pg.wait_for_timeout(600)
        stream = pg.inner_text("#chatbox")
        assert "Что покупал Сбербанк" in stream and "три сделки Сбербанка" in stream, stream[:200]
        # Открытый диалог отмечен в списке — это и есть «где я сейчас».
        # Строки состояния под лентой больше нет (владелец, 3 сентября 2026:
        # «снизу тоже убрать»), поэтому проверяем список, а не подпись.
        assert pg.locator(".chat-thread.on").count() == 1
        assert not errors, errors
    finally:
        ctx.close()


def test_new_dialog_button_lives_above_the_thread_list_and_resets_the_conversation(browser, base_url):
    """Пятый заход на «Новый диалог» (30, 31 августа, дважды 3 сентября).
    Кнопка стоит НАД СПИСКОМ ДИАЛОГОВ — там, где виден её эффект, и там, где
    её ждут в любом привычном чате; на телефоне список открывает кнопка
    «Диалоги» в шапке раздела. Под лентой не осталось ничего, кроме поля
    вопроса: ни строки состояния, ни второй кнопки «Начать заново» (просьба
    владельца 3 сентября 2026). Нажатие не прокручивает страницу и не ставит
    курсор в поле — иначе на телефоне откроется клавиатура (уроки 30-31
    августа). Модели в тестах нет, /api/ask сам отдаёт точный ответ по базе."""
    for width, height in ((390, 844), (1280, 1000)):
        ctx, pg, errors = _assistant_page(browser, base_url, width, height)
        try:
            assert pg.locator("#chatState").count() == 0, "строка состояния вернулась под ленту"
            assert pg.locator("#chatReset").count() == 0, "вторая кнопка сброса вернулась под ленту"
            pg.fill("#q", "Самые крупные сделки 2025 года")
            pg.click("#send")
            pg.wait_for_selector(".chat-stream .msg.ai:not(.wait)", timeout=20000)
            assert pg.locator("#chatState").count() == 0

            if width < 700:
                # На телефоне список уехал за левый край экрана (ящик закрыт) —
                # Playwright считает такой узел «видимым», поэтому меряем бокс,
                # а не is_visible(). Открывает ящик кнопка «Диалоги».
                assert pg.locator("#threadPanel").bounding_box()["x"] < 0
                pg.click("#chatBurger")
                pg.wait_for_timeout(500)
            assert pg.locator("#threadPanel").bounding_box()["x"] >= -1
            assert pg.locator("#newThread").is_visible()

            y0 = pg.evaluate("window.scrollY")
            pg.click("#newThread")
            pg.wait_for_timeout(600)
            assert abs(pg.evaluate("window.scrollY") - y0) < 10, "нажатие прокрутило страницу"
            if width < 700:
                assert pg.evaluate("document.activeElement && document.activeElement.id") != "q"
            assert "Начат новый диалог" in pg.inner_text("#chatbox")
            assert not errors, errors
        finally:
            ctx.close()


@pytest.mark.parametrize("width", WIDTHS)
def test_nav_items_are_centred_on_the_logo_for_a_signed_in_user(browser, base_url, width):
    """«Сверху криво» (партнёр, 3 сентября 2026, профиль Сбербанка с
    телефона); владелец: «разделы по центру логотипу, а не выше, на всех
    устройствах». Проявлялось ТОЛЬКО у вошедшего: кружок-аватар 26px в
    последнем пункте тянул все ссылки до своей высоты (align-items:stretch),
    а текст в них оставался у верхнего края — на 3–4px выше центра
    «КОМПАС». Меряем центр самих букв (Range), а не боксов ссылок: боксы
    были центрированы и до починки."""
    ctx = browser.new_context(viewport={"width": width, "height": 844},
                              is_mobile=width < 700, has_touch=width < 700)
    try:
        pg = ctx.new_page()
        email = f"nav-centre-{width}@ui.test"
        r = pg.request.post(base_url + "/api/auth/register",
                            data={"email": email, "password": "secret123", "full_name": "Тест Навигации"})
        if r.status != 200:
            r = pg.request.post(base_url + "/api/auth/login", data={"email": email, "password": "secret123"})
        assert r.status == 200, r.text()
        pg.goto(base_url + "/#/companies/g300b9ead", wait_until="networkidle")
        pg.wait_for_selector("#navAccount .avatar-dot", timeout=10000)
        pg.wait_for_timeout(300)
        m = pg.evaluate("""() => {
          const mid = b => (b.top + b.bottom) / 2;
          const glyph = e => { const r = document.createRange(); r.selectNodeContents(e); return mid(r.getBoundingClientRect()); };
          const logo = mid(document.querySelector('.top .wordmark').getBoundingClientRect());
          return {links: [...document.querySelectorAll('#nav a:not(#navAccount)')].map(a => glyph(a) - logo),
                  dot: mid(document.querySelector('#navAccount .avatar-dot').getBoundingClientRect()) - logo};
        }""")
        assert all(abs(d) <= 1.5 for d in m["links"]), m
        assert abs(m["dot"]) <= 1.5, m
    finally:
        ctx.close()


def test_company_links_are_hidden_while_the_data_is_incomplete(page, base_url):
    """Владелец, 3 сентября 2026: «все связи сейчас лучше убрать (под
    контролем, в группу входит и портфель) — информация неполная и
    misleading, добавим, когда будет полная». Строки связей не рендерятся у
    профилей, где раньше стояли все их виды; данные и код остались за
    константой SHOW_COMPANY_LINKS. «Собственники» (доля с датой и
    источником) остаются — на этот блок ссылается вкладка «Участники»."""
    if _company_links_shown(page):
        pytest.skip("SHOW_COMPANY_LINKS=true — связи снова показываются, этот тест не о том состоянии")
    labels = ("контроль у", "под контролем", "входит в группу", "в группу входит", "портфель")
    for company_id in ("ugmkinvest", "g3a8fb04f", "gc2792a44", "g00f14033", "g300b9ead"):
        visit(page, base_url, f"#/companies/{company_id}")
        assert page.locator("#app h1").count() == 1
        heads = [t.lower() for t in page.evaluate("[...document.querySelectorAll('#app .d-head b, #app .d-head .tag')].map(e => e.textContent)")]
        for label in labels:
            assert not any(h.startswith(label) for h in heads), (company_id, label, heads)
        assert "структура и связи" not in page.inner_text("#app .d-head").lower(), company_id
        assert page.locator("#group-members, #portfolio-members").count() == 0, company_id
    visit(page, base_url, "#/companies/g69c88bc7")  # МТС: собственники с долей и источником остаются
    body = page.inner_text("#app").lower()
    assert "собственники" in body and "42,085%" in page.inner_text("#app")


def test_access_gate_shows_login_screen_until_the_owner_approves(gated_url, browser):
    """Вход по заявке (ACCESS_GATE, 2 сентября 2026). Гость видит экран
    «Войти / Запросить доступ» вместо любого раздела; заявка создаёт
    неодобренный аккаунт; вход до одобрения — отказ; одобрение приходит
    вебхуком (кнопка acc:<id>:ok от разрешённого from.id); после входа
    открывается ТОТ адрес, на который человек шёл. Проверяется на трёх
    ширинах: нет pageerror, нет горизонтального переполнения, экран
    действительно отрисован (свой элемент #gateScreen, а не «нет ошибок»)."""
    from db.models import User
    from db.session import get_session

    ctx = browser.new_context()
    try:
        pg = ctx.new_page()
        crashes = []
        pg.on("pageerror", lambda e: crashes.append(f"pageerror: {e}"))
        pg.on("console", lambda m: crashes.append(f"console: {m.text}") if m.type == "error" else None)
        for w in WIDTHS:
            pg.set_viewport_size({"width": w, "height": 900})
            # goto на ТОТ ЖЕ адрес с тем же хешем — переход по фрагменту, а не
            # перезагрузка: скрипт не переисполняется, и на экране осталась бы
            # форма заявки с прошлой итерации. Перезагружаем явно.
            pg.goto(gated_url + "/#/companies", wait_until="networkidle")
            pg.reload(wait_until="networkidle")
            pg.wait_for_selector("#gateScreen", timeout=10000)
            assert pg.locator("#gateLoginForm").is_visible()
            assert "Компании" not in pg.inner_text("#app") or "приглашённых" in pg.inner_text("#app")
            over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert over <= 0, f"гейт (вход) переполняет экран на {w}px: {over}px"
            pg.click("#gateToRegister")
            pg.wait_for_selector("#gateRegisterForm")
            over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert over <= 0, f"гейт (заявка) переполняет экран на {w}px: {over}px"
        assert not crashes, crashes[:3]
        # Шапка над гейтом — светлая: тёмный режим героя главной здесь не к месту.
        pg.goto(gated_url + "/#/", wait_until="networkidle")
        pg.reload(wait_until="networkidle")
        pg.wait_for_selector("#gateScreen")
        assert not pg.evaluate("document.querySelector('.top').classList.contains('on-hero')")

        email = f"gate{int(time.time()*1000)}@example.com"
        # Смена хеша за закрытой дверью форму не трогает (нельзя стирать
        # введённое, когда приезжает база) — только запоминает адрес.
        pg.goto(gated_url + "/#/companies", wait_until="networkidle")
        pg.wait_for_selector("#gateLoginForm")
        pg.click("#gateToRegister")
        pg.fill("#gateFullName", "Тест Гейтов")
        pg.fill("#gateCompany", "ООО Ромашка")
        pg.fill("#gatePosition", "Партнёр")
        pg.fill("#gateRegEmail", email)
        pg.fill("#gateRegPassword", "password-123")
        pg.fill("#gateRegPasswordConfirm", "password-123")
        pg.click("#gateRegisterForm button[type=submit]")
        pg.wait_for_selector("#gateDone", timeout=10000)
        assert "Заявка отправлена" in pg.inner_text("#gateCard")

        db = get_session()
        try:
            user = db.query(User).filter_by(email=email).one()
            uid, approved = user.id, user.approved
        finally:
            db.close()
        assert approved is False, "заявка должна создавать неодобренный аккаунт"

        pg.click("#gateToLogin")
        pg.fill("#gateEmail", email)
        pg.fill("#gatePassword", "password-123")
        pg.click("#gateLoginForm button[type=submit]")
        pg.wait_for_timeout(800)
        assert "доступ откроем после проверки" in pg.inner_text("#gateMsg")
        assert pg.locator("#gateScreen").count() == 1

        # Чужой from.id одобрить не может, разрешённый — может.
        for from_id in (999, 111):
            r = pg.request.post(gated_url + "/api/telegram/webhook/ui-secret",
                                data={"callback_query": {"id": "1", "data": f"acc:{uid}:ok", "from": {"id": from_id}}})
            assert r.status == 200
            pg.click("#gateLoginForm button[type=submit]")
            pg.wait_for_timeout(1200)
            if from_id == 999:
                assert pg.locator("#gateScreen").count() == 1, "посторонний открыл доступ"
        assert pg.locator("#gateScreen").count() == 0, "после одобрения дверь не открылась"
        assert pg.evaluate("location.hash") == "#/companies", "после входа потерян адрес, на который шёл человек"
        assert "Компании" in pg.inner_text("#app")
        assert pg.locator("#navAccount .avatar-dot").count() == 1
        # Два входа до одобрения намеренно получили 403 — браузер пишет об этом
        # в консоль («Failed to load resource: 403»), и это ожидаемый ответ, а
        # не поломка. Падений страницы (pageerror) быть не должно вовсе.
        assert not [c for c in crashes if c.startswith("pageerror")], crashes[:3]
        console_errors = [c for c in crashes if c.startswith("console:")]
        assert len(console_errors) == 2 and all("403" in c for c in console_errors), console_errors
    finally:
        ctx.close()


def test_search_finds_latin_named_company_typed_in_cyrillic(page, base_url):
    """«VK» находится буквами «вк» — и в подсказках, и в каталоге компаний.

    Просьба владельца 3 сентября 2026 («Vk пусть находится буквами вк, и другие
    компании тоже»): имя компании в базе записано так, как её пишут источники,
    а ищут её с русской раскладки. Держит побуквенную транслитерацию
    (translitKey в static/index.html) — не «похожее написание», а таблицу
    буква-в-букву, поэтому у теста три примера, а не один.
    """
    visit(page, base_url, "#/companies")
    # `page` — общий на весь файл, а смена хеша не перезапускает скрипт: фильтр
    # отрасли мог остаться от соседнего теста, и тогда поиск ищет внутри него
    # (урок «переход по хешу — не перезагрузка страницы для теста»).
    page.evaluate("() => { coInd = 'Все'; coQuery = ''; coShown = 60; renderCompanies(); }")
    page.wait_for_timeout(400)
    for query, expected in (("вк", "VK"), ("озон", "Ozon"), ("лента", "Лента")):
        page.fill("#coq", query)
        page.wait_for_timeout(800)
        names = page.eval_on_selector_all(
            ".co-grid > *", "els => els.slice(0, 8).map(e => e.innerText)")
        assert any(expected.lower() in (n or "").lower() for n in names), \
            f"запрос «{query}» не нашёл {expected}: {[n.split(chr(10))[1] if n else n for n in names[:5]]}"
    # И подсказки под строкой поиска знают ту же таблицу.
    page.fill("#coq", "вк")
    page.wait_for_timeout(800)
    hints = page.eval_on_selector_all("#coac .ac-item .ac-text", "els => els.map(e => e.textContent)")
    assert "VK" in hints, hints


def test_bank_profile_names_the_legal_entity_it_shows(page, base_url):
    """У банка на экране названо ЮРЛИЦО, о котором идут цифры.

    Владелец 3 сентября 2026: «в втб даже нигде не видно полное наименование».
    Полное наименование приезжает со страницы формы 806 ЦБ вместе с балансом
    (pipeline/cbr_sync_bank_finance.py) — раньше лежало в данных и не
    показывалось. ЕГРЮЛ-блок банка проверить этим тестом нельзя: он приходит
    из боевой базы, которой у дымового прогона нет.
    """
    visit(page, base_url, "#/companies/gcafc31dc")   # ВТБ
    page.wait_for_timeout(1500)
    text = page.inner_text("#app")
    assert "ВТБ" in text and "акционерное общество" in text, text[:400]
    assert "регистрационный номер в Банке России 1000" in text, \
        "не назван регистрационный номер банка, по которому взяты цифры"


def _open_economist_lens(pg, base_url):
    """Открыть карточку с длинными абзацами и перейти на вкладку «Экономист».
    Карточка выбирается по данным, а не по вбитому id: сделки сливаются и
    исчезают, а тест должен пережить это."""
    pg.goto(base_url + "/#/deals", wait_until="networkidle")
    pg.wait_for_function("() => DEALS.length > 100", timeout=15000)
    deal_id = pg.evaluate(
        "() => (DEALS.find(d => d.eco && (d.eco.rationale || '').length > 200) || {}).id || null")
    assert deal_id, "в базе не нашлось сделки с длинным абзацем «Цель сделки»"
    pg.goto(base_url + "/#/deal/" + deal_id, wait_until="networkidle")
    pg.wait_for_timeout(900)
    for btn in pg.locator(".lens button").all():
        if "эконом" in (btn.text_content() or "").strip().lower():
            btn.click()
            break
    pg.wait_for_timeout(500)
    return deal_id


def test_deal_paragraphs_are_not_justified_on_a_phone(browser, base_url):
    """Скриншот владельца 4 сентября 2026: на айфоне у абзацев «Цель сделки» и
    «Контекст» в каждой строке срезано по букве-две справа, а между словами
    дыры. Выключка по ширине придумана для меры в 72 знака (компьютер); на
    телефоне в строку влезает вдвое меньше, и она же выталкивает последнее
    слово за край карточки.

    Меряем не бокс, а САМИ СТРОКИ ТЕКСТА (Range) — тот же приём, что уже
    понадобился для центровки шапки: бокс может стоять в границах, пока текст
    из него вылезает, и проверка по `getBoundingClientRect` элемента этого не
    видит."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    try:
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        _open_economist_lens(pg, base_url)
        para = pg.locator(".spec-v-text").first
        assert para.count() > 0, "на «Экономисте» не нашлось ни одного абзаца"
        align = pg.evaluate("() => getComputedStyle(document.querySelector('.spec-v-text')).textAlign")
        assert align != "justify", "на телефоне абзацы не выключаются по ширине"
        far = pg.evaluate("""() => {
            let far = 0;
            document.querySelectorAll('.spec-v').forEach(v => v.childNodes.forEach(n => {
                if (n.nodeType !== 3) return;
                const rg = document.createRange();
                rg.selectNodeContents(n);
                for (const b of rg.getClientRects()) far = Math.max(far, b.right);
            }));
            return Math.round(far);
        }""")
        assert far <= 390, f"строка текста уходит за край экрана: правый край {far} при ширине 390"
        assert pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0
        assert not errors
    finally:
        ctx.close()


def test_deal_paragraphs_stay_justified_on_the_desktop(browser, base_url):
    """Обратная половина того же правила: выключка по ширине — сознательное
    решение владельца от 18 августа, и на компьютере, где мера в 72 знака
    реальна, она обязана остаться. Иначе «починка телефона» тихо отменит её
    везде."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    try:
        pg = ctx.new_page()
        _open_economist_lens(pg, base_url)
        align = pg.evaluate("() => getComputedStyle(document.querySelector('.spec-v-text')).textAlign")
        assert align == "justify", f"на компьютере абзац должен быть выключен по ширине, а стоит {align}"
    finally:
        ctx.close()


def test_long_stalled_negotiations_get_a_hover_hint(page, base_url):
    """Заметка владельца 4 сентября 2026 («Медскан»/«Сова»): статус
    «Обсуждается», который держится больше двух лет без подтверждения, —
    не то же самое, что свежие переговоры, и читателю стоит намекнуть на
    это без изменения самого статуса. Карточка выбирается по данным
    (recent негативный случай — тоже), не по вбитому id: и старая, и
    свежая сделка в статусе переговоров могут исчезнуть при слиянии."""
    stale_id = page.evaluate("""() => {
        const d = DEALS.find(d => stageKind(d.status) === 'negotiations'
            && d.date && d.date !== 'unknown'
            && (new Date() - new Date(/^\\d{4}$/.test(d.date) ? d.date + '-01-01' : d.date)) / 86400000 > 730);
        return d ? d.id : null;
    }""")
    assert stale_id, "в базе не нашлось карточки в переговорах старше двух лет"
    visit(page, base_url, "#/deal/" + stale_id)
    hint = page.query_selector(".stalled-hint")
    assert hint, f"{stale_id}: подсказка не показана у старых переговоров"
    title = hint.get_attribute("title")
    assert title and "обсужд" in title.lower() and "не состоялась" in title.lower(), title

    fresh_id = page.evaluate("""() => {
        const d = DEALS.find(d => stageKind(d.status) === 'negotiations'
            && d.date && d.date !== 'unknown'
            && (new Date() - new Date(/^\\d{4}$/.test(d.date) ? d.date + '-01-01' : d.date)) / 86400000 < 700);
        return d ? d.id : null;
    }""")
    if fresh_id:
        visit(page, base_url, "#/deal/" + fresh_id)
        assert not page.query_selector(".stalled-hint"), \
            f"{fresh_id}: подсказка не должна показываться у свежих переговоров"


def test_analytics_top_sums_exclude_soft_prices_currency_and_ipo(page, base_url):
    """Аудит перед бетой (5 сентября 2026): в «Крупнейших сделках по
    раскрытой сумме» стояли «300 млрд ₽ (неофициально)» и «около 500 млрд ₽
    (допэмиссия ВТБ)», «$3,2 млрд» считалось как 3,2 млрд ₽, а IPO
    Совкомбанка с оценкой компании 200–219 млрд ₽ соседствовало с покупками.
    Правила суммы — одни на «Аналитику» и страницу отрасли."""
    visit(page, base_url, "#/analytics")
    page.wait_for_selector(".an-c-topsum")
    page.wait_for_function('typeof DEALS!=="undefined" && DEALS.length>1000', timeout=60000)
    rows = [x.inner_text() for x in page.locator(".an-c-topsum .an-deal").all()]
    # список крупнейших — только сделки с прочитанной в источнике ценой; пока
    # таких нет, блок честно говорит об этом, а не показывает непрочитанные
    if not page.evaluate("DEALS.some(countsAsTopPurchase)"):
        assert not rows and "ждёт проверки" in page.inner_text(".an-c-topsum")
    else:
        assert rows
    sums = [x.inner_text() for x in page.locator(".an-c-topsum .an-deal .an-deal-s").all()]
    assert len(sums) == len(rows)
    for row, total in zip(rows, sums):
        low = row.lower()
        # «около» ищется по границе слова: в «у Артема Соколова» оно тоже есть
        for bad in (r"неофициально", r"допэмисси", r"(?:^|[^а-яё])около", r"по оценке", r"(?:^|[^a-zа-яё])ipo(?![a-zа-яё])",
                    r"под залог", r"структурн[а-яё]* сделк"):
            assert not re.search(bad, low), row
        # диапазон «30–40 млрд ₽» — оценка, а не цена, названная сторонами
        assert not re.search(r"\d\s*[–—-]\s*\d", total), row
        assert "₽" in total, row  # валютная сумма считается только через рублёвый эквивалент в скобках
    # допуск к суммам и к списку крупнейших — из facts, а не из текста
    checks = page.evaluate("""() => {
      const inTop = DEALS.filter(countsAsTopPurchase);
      return {top_read: inTop.every(d => ["read","verified"].includes(priceFact(d).basis)),
              top_subset: inTop.every(countsAsPrice),
              ipo: DEALS.filter(d => d.type === "IPO").some(countsAsPrice)};
    }""")
    assert checks["top_read"] and checks["top_subset"], checks
    assert checks["ipo"] is False


def test_gold_rows_agree_with_client_rules(page, base_url):
    """Контрольная выборка pipeline/gold/analytics_gold.json против КЛИЕНТСКИХ
    копий правил (sumBasis, countsAsPrice/isSoftSum, _dealMultipleSumRub):
    серверные копии проверяет test_gold_analytics.py, здесь — что клиент
    говорит то же самое на тех же живых карточках. Ожидания зафиксированы
    чтением, а не кодом."""
    gold = json.loads((Path(__file__).parent / "pipeline" / "gold" / "analytics_gold.json").read_text(encoding="utf-8"))
    visit(page, base_url, "#/analytics")
    page.wait_for_function('typeof DEALS!=="undefined" && DEALS.length>1000', timeout=60000)
    got = page.evaluate("""(rows) => rows.map(r => {
      const d = DEALS.find(x => x.id === r.id);
      if(!d) return {id: r.id, missing: true};
      const target = d.target || d.asset_id;
      return {id: r.id, basis: sumBasis(d), top: countsAsPrice(d),
              admitted: !!(d.facts && d.facts.admitted && d.facts.admitted.purchase_sums),
              reason: d.facts && d.facts.reasons ? d.facts.reasons.purchase_sums : null,
              multiple: target ? _dealMultipleSumRub(d, target) !== null : false,
              priceBasis: target ? ((_dealMultiplePrice(d, target)||{}).basis || null) : null,
              type: d.type};
    })""", gold["deals"])
    problems = []
    for row, g in zip(gold["deals"], got):
        if g.get("missing"):
            continue  # карточки раньше 2022 года на клиент не грузятся
        # Строка, помеченная `pending`, говорит правду, которой карточка пока
        # не соответствует (или два чтения разошлись и вопрос ждёт человека).
        # Требовать её здесь нечего: за неё отвечает строгий xfail в
        # test_gold_analytics.py — он покраснеет, когда вопрос решат.
        if row.get("pending"):
            continue
        if g["basis"] != row["sum_basis"]:
            problems.append((row["id"], "sumBasis", g["basis"], row["sum_basis"]))
        # Клиент обязан читать допуск ровно так, как его посчитал сервер, —
        # а сам допуск (in_top_purchases в выборке — про ПРАВИЛА, при
        # прочитанной цене) сверяет test_gold_analytics.py: непрочитанная
        # цена на клиенте честно не считается, и это не расхождение правил.
        if g["top"] != g["admitted"]:
            problems.append((row["id"], "top≠admitted", g["top"], g["admitted"]))
        if row["in_top_purchases"] and g["reason"] not in ("ok", "price_not_read", "stale"):
            problems.append((row["id"], "top", g["reason"], row["in_top_purchases"]))
        if not row["in_top_purchases"] and g["top"]:
            problems.append((row["id"], "top", g["top"], row["in_top_purchases"]))
        # клиент показывает мультипликатор только для сделки с подтверждёнными
        # чтением фактами — это ПОДМНОЖЕСТВО текстового допуска выборки
        if g["multiple"] and not row["in_multiples"]:
            problems.append((row["id"], "multiple", g["multiple"], row["in_multiples"]))
        # Числитель: клиент обязан пересчитывать цену пакета на 100% ровно там
        # же, где это делает сервер (deal_multiples.implied_full_price), —
        # иначе на карточке и в блоке «Аналитики» будут разные ×.
        if g["priceBasis"] and (g["priceBasis"] == "scaled") != bool(row.get("price_scaled")):
            problems.append((row["id"], "price_basis", g["priceBasis"], row.get("price_scaled")))
    assert not problems, problems


def test_compare_shows_bank_of_russia_data_for_a_bank(page, base_url):
    """Аудит перед бетой: сравнение писало Сбербанку «Подтверждённая БФО пока
    не загружена», хотя на его профиле стоит блок «По данным Банка России»
    (bank_finance.json). Сравнение обязано читать тот же источник, а у АО
    называть учредителей при регистрации, не «текущих участников»."""
    visit(page, base_url, "#/advisors")
    page.wait_for_function("typeof DEALS !== 'undefined' && DEALS.length > 100")
    page.evaluate("() => localStorage.setItem(COMPARE_KEY, JSON.stringify(['g28ff15bb','yandex']))")
    visit(page, base_url, "#/compare")
    page.wait_for_selector(".compare-card", timeout=10000)
    page.wait_for_timeout(1500)
    cards = [c.inner_text() for c in page.locator(".compare-card").all()]
    sber = next(c for c in cards if "Сбербанк" in c)
    assert "По данным Банка России" in sber and "Активы" in sber, sber
    assert "БФО пока не загружена" not in sber
    assert "Текущие участники" not in sber, sber
    page.evaluate("() => localStorage.removeItem(COMPARE_KEY)")
