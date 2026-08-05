"""Дымовые тесты интерфейса: экраны открываются, ничего не падает, не переполняет.

Ловят ровно тот класс дефектов, который дважды проходил мимо ручных проверок:
страница фирмы не отрисовывалась из-за исключения в рендере (прошлый прогон), а
панель фильтров переполняла экран на 100px, но только в открытом виде.

ВАЖНО: слушаем `pageerror`, а не только `console`. Необработанное исключение в
консоль не попадает — «ошибок в консоли 0» без этого ничего не доказывает.

Запуск: python3 -m pytest test_ui.py -q
Пропускается, если не установлен Playwright (тогда гоняются только остальные).
"""
import re
import socket
import subprocess
import sys
import time
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


@pytest.fixture(scope="session")
def base_url():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    checks = ["#/", "#/deal/citibank", "#/analytics", "#/industry/Банки",
              "#/ind/Банки", "#/advisors/orion"]
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


def test_account_form_is_visible_after_async_auth_check(page, base_url):
    visit(page, base_url, "#/account")
    assert page.locator("#loginForm").is_visible()
    assert page.locator("#loginEmail").is_visible()
    assert "Войти" in page.locator("#app").inner_text()


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


def test_regulatory_analyzer_defers_to_a_known_approval(page, base_url):
    """Анализатор не спорит с фактом и не предлагает считать то, что известно.

    Замечание владельца: если у сделки ФАС уже получен, а анализатор напишет
    «согласование не требуется», это читается как «сервис плохой» — хотя
    объяснений у расхождения два и оба нормальные (сторона могла подать
    ходатайство из осторожности; основание могло быть не видно из карточки).
    Поэтому там, где согласование НАЗВАНО в карточке, панель начинается с
    этого факта и прямо пишет, что факт сильнее расчёта, а кнопки «проверить»
    на «Обзоре» нет вовсе — нажимать её там значит тратить время читателя.
    """
    visit(page, base_url, "#/")
    with_appr, without = page.evaluate("""() => {
      const has = v => { const t = String(v||'').trim().toLowerCase();
        return !!t && t !== '—' && !/^(не раскры|публично не|не сообщал)/.test(t); };
      const a = DEALS.find(d => has(d.law && d.law.appr));
      const b = DEALS.find(d => !has(d.law && d.law.appr) && d.eco);
      return [a && a.id, b && b.id];
    }""")
    assert with_appr and without, "в базе нет пары карточек для проверки"

    visit(page, base_url, "#/deal/" + without)
    assert page.locator("[data-reg-open]").count() == 1, "нет кнопки там, где про согласования молчат"
    page.locator("[data-reg-open]").first.click()
    page.wait_for_timeout(500)
    panel = page.locator("#reg-panel")
    assert panel.count() == 1, "кнопка не открыла панель — эффект вне экрана"

    visit(page, base_url, "#/deal/" + with_appr)
    assert page.locator("[data-reg-open]").count() == 0, \
        "кнопка предлагает считать то, что уже известно"
    page.evaluate("document.querySelector('[data-l=\"law\"]').click()")
    page.wait_for_timeout(400)
    text = page.locator("#reg-panel").inner_text()
    assert "согласование уже названо в источниках" in text.lower(), \
        "панель не начинается с известного факта"
    assert not page.crashes, f"падения на анализаторе: {page.crashes[:3]}"


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


def test_analytics_names_the_set_it_counts(page, base_url):
    """У числа на экране два свойства: величина и множество.

    В файле 1538 карточек, а на сайте показаны только сделки с 2022 года —
    191 запись скрыта. Подпись «вся база» над отфильтрованным числом была бы
    арифметически верной и всё равно врала.
    """
    visit(page, base_url, "#/analytics")
    shown = page.evaluate("() => DEALS.length")
    head = page.inner_text(".sec-head")
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
