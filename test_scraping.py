# -*- coding: utf-8 -*-
"""Защита базы от легкого скачивания (scrape_guard.py, docs/scraping_protection.md)."""
import time

import pytest
from fastapi.testclient import TestClient

import main
import scrape_guard

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SCRAPE_GUARD", "1")
    monkeypatch.setenv("DATA_TOKEN_SECRET", "test-secret")
    monkeypatch.delenv("MODERATION_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    scrape_guard.reset()
    c = TestClient(main.app, headers={"User-Agent": BROWSER_UA})
    yield c
    scrape_guard.reset()


def test_page_sets_token_and_data_loads_with_it(client):
    page = client.get("/")
    assert page.status_code == 200
    assert scrape_guard.COOKIE_NAME in page.cookies
    r = client.get(scrape_guard.DATA_PATH)
    assert r.status_code == 200
    assert len(r.json()["deals"]) > 100
    assert "private" in r.headers["cache-control"]
    # повторный запрос с ETag — 304, без 11 МБ
    again = client.get(scrape_guard.DATA_PATH, headers={"If-None-Match": r.headers["etag"]})
    assert again.status_code == 304


def test_no_token_is_refused(client):
    r = client.get(scrape_guard.DATA_PATH)
    assert r.status_code == 401


def test_old_static_path_closed_but_other_static_open(client):
    assert client.get("/static/data/deals_promoted.json").status_code == 404
    assert client.get("/static/data/pending.json").status_code == 200


def test_robot_user_agents_refused_even_with_cookie(client):
    for ua in ("", "curl/8.4.0", "python-requests/2.31", "Wget/1.21", "Scrapy/2.11",
               "python-httpx/0.27", "Go-http-client/1.1", "GPTBot/1.0"):
        client.cookies.clear()
        # токен, выписанный ровно на этот UA: отказ — из-за UA, а не токена
        client.cookies.set(scrape_guard.COOKIE_NAME, scrape_guard.make_token(ua))
        r = client.get(scrape_guard.DATA_PATH, headers={"User-Agent": ua})
        assert r.status_code == 403, ua


def test_search_engines_still_get_the_html_page(client):
    for ua in ("Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
               "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"):
        r = client.get("/", headers={"User-Agent": ua})
        assert r.status_code == 200 and "<html" in r.text.lower()


def test_foreign_referer_refused_missing_referer_allowed(client):
    client.get("/")
    assert client.get(scrape_guard.DATA_PATH,
                      headers={"Referer": "https://evil.example/page"}).status_code == 403
    assert client.get(scrape_guard.DATA_PATH,
                      headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.get(scrape_guard.DATA_PATH,
                      headers={"Referer": "http://testserver/#/deals",
                               "Sec-Fetch-Site": "same-origin"}).status_code == 200
    assert client.get(scrape_guard.DATA_PATH).status_code == 200


def test_token_bound_to_user_agent_and_expires(client, monkeypatch):
    tok = scrape_guard.make_token(BROWSER_UA)
    assert scrape_guard.check_token(tok, BROWSER_UA)
    assert not scrape_guard.check_token(tok, BROWSER_UA + " other")
    assert not scrape_guard.check_token(tok[:-1] + ("0" if tok[-1] != "0" else "1"), BROWSER_UA)
    old = scrape_guard.make_token(BROWSER_UA, now=time.time() - 7 * 3600)
    assert not scrape_guard.check_token(old, BROWSER_UA)
    monkeypatch.setenv("DATA_TOKEN_SECRET", "another")
    assert not scrape_guard.check_token(tok, BROWSER_UA)


def test_token_ip_binding_optional(monkeypatch):
    monkeypatch.setenv("DATA_TOKEN_SECRET", "s")
    monkeypatch.setenv("DATA_TOKEN_BIND_IP", "1")
    tok = scrape_guard.make_token(BROWSER_UA, "8.8.8.8")
    assert scrape_guard.check_token(tok, BROWSER_UA, "8.8.8.8")
    assert not scrape_guard.check_token(tok, BROWSER_UA, "1.1.1.1")


def test_session_endpoint_renews_token(client):
    r = client.post("/api/data/session")
    assert r.status_code == 204 and scrape_guard.COOKIE_NAME in r.cookies
    assert client.get(scrape_guard.DATA_PATH).status_code == 200
    assert client.post("/api/data/session", headers={"User-Agent": "curl/8"}).status_code == 403


def test_service_key_for_routines(client, monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "bridge-key")
    bare = TestClient(main.app, headers={"User-Agent": "python-httpx/0.27"})
    assert bare.get(scrape_guard.DATA_PATH, headers={"X-Data-Key": "bridge-key"}).status_code == 200
    assert bare.get(scrape_guard.DATA_PATH, headers={"X-Data-Key": "wrong"}).status_code == 403
    assert bare.get("/static/data/deals_promoted.json",
                    headers={"X-Data-Key": "bridge-key"}).status_code == 200


def test_rate_limit_per_public_address(client, monkeypatch):
    monkeypatch.setenv("RATE_DATA_PER_10MIN", "3")
    client.get("/")
    ip = {"X-Forwarded-For": "77.88.8.7"}
    codes = [client.post("/api/data/session", headers=ip).status_code for _ in range(4)]
    assert codes == [204, 204, 204, 429]
    # другой адрес не задет
    assert client.post("/api/data/session", headers={"X-Forwarded-For": "77.88.8.8"}).status_code == 204


def test_rate_limit_uses_rightmost_public_forwarded_address(client, monkeypatch):
    """Левые значения X-Forwarded-For подставляет сам посетитель — по ним лимит
    обходился бы сменой заголовка."""
    monkeypatch.setenv("RATE_ASSISTANT_PER_10MIN", "2")
    codes = []
    for i in range(3):
        h = {"X-Forwarded-For": "5.255.255.%d, 77.88.8.9, 10.0.0.1" % i}
        codes.append(client.post("/api/assistant/lookup", json={"question": "Сбер"}, headers=h).status_code)
    assert codes[-1] == 429 and 429 not in codes[:2]


def test_no_public_address_means_no_limit(client, monkeypatch):
    """За прокси без X-Forwarded-For все посетители выглядят одним адресом —
    ограничивать по нему значит положить сайт для всех."""
    monkeypatch.setenv("RATE_DATA_PER_10MIN", "1")
    for _ in range(3):
        assert client.post("/api/data/session").status_code == 204


def test_client_ip_parsing():
    h = {"x-forwarded-for": "1.2.3.4, 5.6.7.8, 10.1.1.1"}
    assert scrape_guard.client_ip(h, "10.0.0.5") == "5.6.7.8"
    assert scrape_guard.client_ip({}, "127.0.0.1") is None
    assert scrape_guard.client_ip({}, "testclient") is None
    assert scrape_guard.client_ip({}, "8.8.4.4") == "8.8.4.4"


def test_switch_off_restores_old_behaviour(client, monkeypatch):
    monkeypatch.setenv("SCRAPE_GUARD", "0")
    bare = TestClient(main.app, headers={"User-Agent": "curl/8"})
    assert bare.get(scrape_guard.DATA_PATH).status_code == 200
    assert bare.get("/static/data/deals_promoted.json").status_code == 200
    assert scrape_guard.COOKIE_NAME not in bare.get("/").cookies


def test_robots_txt_closes_data_endpoints(client):
    body = client.get("/robots.txt").text
    assert "Disallow: /api/data/" in body and "Disallow: /static/data/" in body


def test_browser_ua_not_mistaken_for_robot():
    for ua in (BROWSER_UA,
               "Mozilla/5.0 (Linux; Android 13; CUBOT X30) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
               "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1",
               "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/128 YaBrowser/24.10 Safari/537.36",
               "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/129 Safari/537.36"):
        assert not scrape_guard.is_robot(ua), ua
