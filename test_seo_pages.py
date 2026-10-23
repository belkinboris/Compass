# -*- coding: utf-8 -*-
"""Открытые страницы для поисковиков и ИИ (seo_pages.py, 23 октября 2026)."""
import re

import pytest
from fastapi.testclient import TestClient

import base_data
import main
import seo_pages

UA = "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app, headers={"User-Agent": UA})


@pytest.fixture(scope="module")
def data():
    return base_data.promoted()


def _shown(deals):
    return [d for d in deals if seo_pages._shown(d)]


def test_deal_page_is_the_site_page_with_the_deal_written_in(client, data):
    """Поисковик видит сделку без скрипта, но только в объёме поста канала:
    разбор экономиста и юриста остаётся в приложении (решение владельца)."""
    deal = next(d for d in data["deals"] if d["id"] == "g0b187624")
    r = client.get("/deal/g0b187624")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    page = r.text
    assert "<h1>«Северсталь» приобрела «Дмитровский металлоцентр»</h1>" in page
    assert '<link rel="canonical" href="https://projectcompass.ru/deal/g0b187624">' in page
    assert "Северсталь" in page and "ООО «Металлстандарт»" in page
    assert "<title>«Северсталь» приобрела «Дмитровский металлоцентр» — Компас</title>" in page
    # Человек видит обычную карточку сайта: это та же страница приложения,
    # а ранний скрипт переводит адрес в #/deal/<id> (владелец 23 октября 2026).
    assert '<main class="wrap" id="app"><article class="seo-snapshot">' in page
    assert "history.replaceState" in page.split("</head>")[0]
    for field in ("context", "target_fin", "rationale"):
        text = str((deal.get("eco") or {}).get(field) or "")
        if len(text) > 40:
            assert text[:40] not in page, field
    assert "t.me/LawFirms" not in page          # агрегатор — не источник


def test_merged_and_missing_addresses(client, data):
    old, new = next(iter(data["merged"].items()))
    r = client.get(f"/deal/{old}", follow_redirects=False)
    if seo_pages.resolve_deal(old)[0] == "moved":
        assert r.status_code == 301 and r.headers["location"].endswith(f"/deal/{seo_pages.resolve_deal(old)[1]}")
    assert client.get("/deal/no-such-deal").status_code == 404
    assert client.get("/company/no-such-company").status_code == 404


def test_old_deals_stay_off_the_open_pages_like_on_the_site(client, data):
    old = next((d for d in data["deals"] if str(d.get("date") or "")[:4].isdigit()
                and int(str(d["date"])[:4]) < seo_pages.SITE_MIN_YEAR), None)
    if old:
        assert client.get(f"/deal/{old['id']}").status_code == 404


def test_company_page_lists_its_deals(client):
    r = client.get("/company/g4e2d0a88")
    assert r.status_code == 200
    assert 'href="/deal/g0b187624"' in r.text
    assert '<link rel="canonical" href="https://projectcompass.ru/company/g4e2d0a88">' in r.text


def test_sitemap_lists_every_shown_deal_and_robots_points_to_it(client, data):
    xml = client.get("/sitemap.xml")
    assert xml.status_code == 200 and "xml" in xml.headers["content-type"]
    locs = re.findall(r"<loc>([^<]+)</loc>", xml.text)
    deal_locs = [u for u in locs if "/deal/" in u]
    assert len(deal_locs) == len(_shown(data["deals"])) == len(set(deal_locs))
    assert len(locs) < 50000                    # предел одного файла карты
    assert "Sitemap: https://projectcompass.ru/sitemap.xml" in client.get("/robots.txt").text


def test_llms_txt_describes_the_site(client):
    r = client.get("/llms.txt")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert r.text.startswith("# Компас")
    assert "/deal/<id>" in r.text and "sitemap.xml" in r.text
    assert "%d+ сделок" % seo_pages.rounded_count() in r.text


def test_home_page_description_counts_the_deals_live(client, data):
    page = client.get("/").text
    n = seo_pages.rounded_count()
    assert n <= len(_shown(data["deals"])) < n + 100
    for tag in re.findall(r'<meta (?:name="description"|property="og:description") content="[^"]*"', page):
        assert "%d+ сделок" % n in tag, tag
        assert "линза" not in tag


def test_yandex_webmaster_verification_file(client):
    """Владелец подтверждает права в Яндекс Вебмастере HTML-файлом: текст
    сверяется дословно, а catch-all отдал бы index.html."""
    r = client.get("/yandex_c76538994d1a82ce.html")
    assert r.status_code == 200
    assert "<body>Verification: c76538994d1a82ce</body>" in r.text
    assert '<meta name="yandex-verification" content="c76538994d1a82ce">' in client.get("/").text
