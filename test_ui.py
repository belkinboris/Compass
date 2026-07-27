"""Дымовые тесты интерфейса: экраны открываются, ничего не падает, не переполняет.

Ловят ровно тот класс дефектов, который дважды проходил мимо ручных проверок:
страница фирмы не отрисовывалась из-за исключения в рендере (прошлый прогон), а
панель фильтров переполняла экран на 100px, но только в открытом виде.

ВАЖНО: слушаем `pageerror`, а не только `console`. Необработанное исключение в
консоль не попадает — «ошибок в консоли 0» без этого ничего не доказывает.

Запуск: python3 -m pytest test_ui.py -q
Пропускается, если не установлен Playwright (тогда гоняются только остальные).
"""
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="playwright не установлен")
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parent
CHROMIUM = "/opt/pw-browsers/chromium"
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
        br = p.chromium.launch(executable_path=CHROMIUM)
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
