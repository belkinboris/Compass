# -*- coding: utf-8 -*-
"""Сайт: robots, отдача базы по токену, вебинары, PDF-выгрузки, значки,
страницы для поисковиков и ловилка всех адресов — ее роутер подключается
ПОСЛЕДНИМ (docs/server_layout.md)."""
import os
import re

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

import scrape_guard
import seo_pages
from company_catalog import get_company_profile
from deal_catalog import get_deal
from deal_export import render_companies_pdf, render_deal_pdf
from db.models import FinancialReport, LegalEntity, LegalEntityMatchStatus, User, UserTier, Webinar
from sqlalchemy import select

from app.core import STATIC_DIR, get_db, _current_user, _plain, SITE_URL

router = APIRouter()


@router.get("/robots.txt", include_in_schema=False)
def robots_txt():
    """Данные и API — не для роботов. База отдается сайтом одним файлом
    (`/static/data/deals_promoted.json`); файл robots.txt — первое, что
    посмотрит добросовестный сборщик, и единственное, что увидит
    индексатор. Юридическая опора — раздел «Права на базу данных»
    пользовательского соглашения (см. LEGAL_DOCS в static/index.html)."""
    body = ("User-agent: *\n"
            "Disallow: /static/data/\n"
            "Disallow: /api/\n"
            "Disallow: /api/data/\n"
            "Allow: /\n"
            "\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")
    return Response(body, media_type="text/plain; charset=utf-8")


def _data_access_denied(request: Request) -> JSONResponse | None:
    """Общие проверки для базы и для выдачи токена: робот, чужой сайт."""
    if scrape_guard.is_robot(request.headers.get("user-agent", "")):
        scrape_guard.bump("robot")
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if scrape_guard.foreign_origin(request.headers, request.headers.get("host", "")):
        scrape_guard.bump("foreign_origin")
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return None


@router.api_route("/api/data/session", methods=["GET", "POST"], include_in_schema=False)
def data_session(request: Request):
    """Новый токен для базы — страница зовет это, если ее токен истек
    (вкладка открыта дольше срока, index.html пришел из кэша браузера)."""
    resp = Response(status_code=204)
    if scrape_guard.enabled():
        denied = _data_access_denied(request)
        if denied:
            return denied
        scrape_guard.issue_cookie(resp, request)
    return resp


@router.get(scrape_guard.DATA_PATH, include_in_schema=False)
def data_base_file(request: Request, token: str = ""):
    """База сделок для страницы. Раньше — публичный /static/data/deals_promoted.json."""
    path = os.path.join(STATIC_DIR, "data", "deals_promoted.json")
    if scrape_guard.enabled() and not scrape_guard.service_key_ok(request.headers, token):
        denied = _data_access_denied(request)
        if denied:
            return denied
        ip = scrape_guard.client_ip(request.headers, request.client.host if request.client else None)
        if not scrape_guard.check_token(request.cookies.get(scrape_guard.COOKIE_NAME, ""),
                                        request.headers.get("user-agent", ""), ip):
            scrape_guard.bump("no_token")
            return JSONResponse({"error": "token required"}, status_code=401)
    try:
        st = os.stat(path)
    except OSError:
        return JSONResponse({"error": "not found"}, status_code=404)
    etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
    headers = {"Cache-Control": "private, no-cache", "ETag": etag, "X-Robots-Tag": "noindex"}
    if etag in (request.headers.get("if-none-match") or ""):
        return Response(status_code=304, headers=headers)
    scrape_guard.bump("served")
    return FileResponse(path, media_type="application/json", headers=headers)

# Таблицы аккаунтов (db/models.py) — заготовка лежала не подключенной с 22
# июля, main.py по-прежнему читает static/data/*.json напрямую для сделок и
# компаний. create_all создает только НЕДОСТАЮЩИЕ таблицы и никогда не трогает
# существующие данные — безопасно и на пустой sqlite для разработки, и на
# уже заполненном Postgres на Timeweb.


# ВРЕМЕННО, по прямой просьбе владельца 3 сентября 2026: «разрешить
# авторизованным пользователям скачивать PDF без платной подписки, пока ее
# нет». Карточку сделки в PDF (export_deal) может скачать любой вошедший;
# гостю — по-прежнему 401 (вход нужен, чтобы выгрузка не была анонимной).
# Когда подписка появится — поставить False, и скачивание снова станет
# только для тарифа paid, без другой правки кода и интерфейса.
DEAL_EXPORT_ALL_FREE = True

# 5 сентября 2026, владелец: «разрешим пдф скачивать всем, даже тем, кто не
# платил». Вход для карточки в PDF больше не нужен: гость получает файл так
# же, как вошедший (текст PDF собирается из нашей же базы, ничьих секретов в
# нем нет). Живая отчетность ФНС (bo_file) под это не попадает — каждый ее
# клик тратит платную квоту API-ФНС. Когда появится подписка — поставить
# False, и гостю снова вернется 401 без правки интерфейса (там ветка есть).
DEAL_EXPORT_GUESTS = True


class DealExportIn(BaseModel):
    # Поле оставлено для обратной совместимости с будущим редактором, но сервер
    # формирует PDF из своей базы и не доверяет присланному HTML/тексту.
    title: str | None = None


# ==================== Вебинары ====================

@router.get("/api/webinars")
def list_webinars(db=Depends(get_db)):
    rows = list(db.scalars(select(Webinar).where(Webinar.published.is_(True))
                           .order_by(Webinar.starts_at.desc(), Webinar.id.desc())).all())
    return [{
        "id": row.id, "title": row.title, "summary": row.summary,
        "starts_at": row.starts_at.isoformat() if row.starts_at else None,
        "speaker": row.speaker, "registration_url": row.registration_url,
        "recording_url": row.recording_url, "status": row.status,
    } for row in rows]


# ==================== Экспорт сделки ====================

def _export_finance(deal: dict, db) -> list[dict]:
    """Финансовый контекст сделки для PDF — то же, что блок на карточке.

    Просьба Ксюши (19 сентября 2026): в выгрузке этого раздела не было вовсе,
    а на карточке он есть. Отчет уходит из рук в руки, и «за сколько купили»
    без «сколько эта компания зарабатывает» — половина разговора.

    Берем показатели ЗА ПОСЛЕДНИЙ ГОД ДО СДЕЛКИ (как и на экране): показывать
    в отчете о сделке 2023 года отчетность за 2025-й значило бы отвечать не на
    тот вопрос. Юрлицо и год называются прямо — отчетность сдается по юрлицу,
    а сделка заключается по группе, и подменять одно другим нельзя.
    """
    year_cap = None
    date = str(deal.get("date") or "")
    if len(date) >= 4 and date[:4].isdigit():
        year_cap = int(date[:4])
    rows: list[dict] = []
    for key, role in (("target", "Покупаемая компания"), ("buyer", "Покупатель")):
        company_id = deal.get(key)
        if not company_id:
            continue
        entity = db.scalar(select(LegalEntity).where(
            LegalEntity.company_id == company_id,
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
        ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id))
        if not entity:
            continue
        query = select(FinancialReport).where(FinancialReport.legal_entity_id == entity.id)
        if year_cap:
            query = query.where(FinancialReport.year <= year_cap)
        report = db.scalar(query.order_by(FinancialReport.year.desc()))
        if not report:
            continue
        profile = get_company_profile(company_id) or {}
        rows.append({
            "role": role,
            # Имя из профиля базы, а не из ЕГРЮЛ: «ПУБЛИЧНОЕ АКЦИОНЕРНОЕ
            # ОБЩЕСТВО "ВЫМПЕЛ-КОММУНИКАЦИИ"» капсом — нарушение правила
            # «язык для людей», уже разобранное для экрана мультипликаторов.
            "name": profile.get("name") or entity.short_name or entity.legal_name,
            "legal_name": entity.legal_name,
            "inn": entity.inn,
            "year": report.year,
            "revenue_rub": _plain(report.revenue_rub),
            "net_profit_rub": _plain(report.net_profit_rub),
            "assets_rub": _plain(report.assets_rub),
            "equity_rub": _plain(report.equity_rub),
        })
    return rows


@router.post("/api/deals/{deal_id}/export")
def export_deal(deal_id: str, _payload: DealExportIn | None = None,
                user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user and not DEAL_EXPORT_GUESTS:
        return JSONResponse({"error": "войдите, чтобы скачать карточку"}, status_code=401)
    if user and not DEAL_EXPORT_ALL_FREE and user.tier != UserTier.paid:
        return JSONResponse({"error": "скачивание карточек доступно по подписке"}, status_code=403)
    deal = get_deal(deal_id)
    if not deal:
        return JSONResponse({"error": "сделка не найдена"}, status_code=404)
    enriched = dict(deal)
    for key, out in (("buyer", "buyer_name"), ("target", "target_name"), ("seller_id", "seller_name")):
        company_id = deal.get(key)
        profile = get_company_profile(company_id) if company_id else None
        if profile and not enriched.get(out):
            enriched[out] = profile.get("name")
    enriched["finance"] = _export_finance(deal, db)
    pdf = render_deal_pdf(enriched)
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", deal_id)[:80] + ".pdf"
    return StreamingResponse(iter([pdf]), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


class CompaniesExportIn(BaseModel):
    """Сравнение собрано на экране, оттуда и приходит: сервер не пересобирает
    его заново — иначе в PDF попало бы не то, что человек видел."""
    companies: list[dict] = []


@router.post("/api/companies/export")
def export_companies(payload: CompaniesExportIn,
                      user: User | None = Depends(_current_user)):
    """PDF сравнения компаний. Ксюша 19 сентября 2026: «сделала сравнение
    компаний — могу получить пдф»."""
    if not user and not DEAL_EXPORT_GUESTS:
        return JSONResponse({"error": "войдите, чтобы скачать сравнение"}, status_code=401)
    rows = [r for r in (payload.companies or []) if isinstance(r, dict) and r.get("name")]
    if not rows:
        return JSONResponse({"error": "нечего выгружать: компании не выбраны"}, status_code=400)
    if len(rows) > 3:
        rows = rows[:3]
    pdf = render_companies_pdf(rows)
    return StreamingResponse(iter([pdf]), media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="compass-companies.pdf"'})


# Иконки по корневым адресам, которые браузеры запрашивают САМИ, не читая
# <link> в <head>: Safari на iPhone просит /favicon.ico для значка закладки
# (SVG-фавикон в data: он не понимает вовсе) и /apple-touch-icon.png для
# экрана «Домой». До 5 сентября 2026 эти адреса ловил catch-all ниже и
# отдавал index.html со статусом 200 — Safari получал HTML вместо картинки,
# не считал это ошибкой и рисовал вместо логотипа букву «K» (скриншот
# владельца: окно «Add Bookmark»). Правильный ответ здесь — файл картинки,
# а не «страница не найдена».
ROOT_ICONS = {
    "favicon.ico": ("favicon.ico", "image/x-icon"),
    "apple-touch-icon.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-precomposed.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-180x180.png": ("apple-touch-icon.png", "image/png"),
    "apple-touch-icon-180x180-precomposed.png": ("apple-touch-icon.png", "image/png"),
}


@router.get("/{icon_name}.ico")
@router.get("/{icon_name}.png")
def root_icon(icon_name: str, request: Request):
    name = request.url.path.lstrip("/")
    if name not in ROOT_ICONS:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    filename, media_type = ROOT_ICONS[name]
    return FileResponse(os.path.join(STATIC_DIR, "icons", filename), media_type=media_type,
                        headers={"Cache-Control": "public, max-age=86400"})


# Открытые страницы для поисковиков и ИИ-ассистентов (seo_pages.py, 23 октября
# 2026): сделка и компания в объеме поста канала, карта сайта, описание для ИИ.
# Стоят ДО catch-all ниже, иначе их адреса получили бы index.html.
# Это та же страница сайта (index.html), только с заголовком и текстом сделки,
# вписанными для поисковика, — поэтому и токен базы, как у index() ниже.
def _app_page(content: str, request: Request, status_code: int = 200) -> HTMLResponse:
    resp = HTMLResponse(content, status_code=status_code)
    if scrape_guard.enabled():
        resp.headers["Cache-Control"] = "no-cache"
        scrape_guard.issue_cookie(resp, request)
    return resp


@router.api_route("/deal/{deal_id}", methods=["GET", "HEAD"], include_in_schema=False)
def seo_deal(deal_id: str, request: Request):
    state, value = seo_pages.resolve_deal(deal_id)
    if state == "moved":
        return RedirectResponse(f"/deal/{value}", status_code=301)
    if state == "missing":
        return _app_page(seo_pages.missing_html(SITE_URL), request, 404)
    return _app_page(seo_pages.deal_html(value, SITE_URL), request)


@router.api_route("/company/{company_id}", methods=["GET", "HEAD"], include_in_schema=False)
def seo_company(company_id: str, request: Request):
    state, value = seo_pages.resolve_company(company_id)
    if state == "moved":
        return RedirectResponse(f"/company/{value}", status_code=301)
    if state == "missing":
        return _app_page(seo_pages.missing_html(SITE_URL), request, 404)
    return _app_page(seo_pages.company_html(company_id, value, SITE_URL), request)


# Подтверждение прав на сайт в Яндекс Вебмастере (владелец, 23 октября 2026):
# Яндекс скачивает этот файл и сверяет текст дословно. Без маршрута адрес
# ловил catch-all и отдавал index.html — «В HTML-файле неправильное содержимое».
YANDEX_VERIFICATION = "c76538994d1a82ce"


@router.api_route(f"/yandex_{YANDEX_VERIFICATION}.html", methods=["GET", "HEAD"], include_in_schema=False)
def yandex_verification():
    body = ('<html>\n    <head>\n        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
            f'    </head>\n    <body>Verification: {YANDEX_VERIFICATION}</body>\n</html>\n')
    return HTMLResponse(body)


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
def seo_sitemap():
    return Response(seo_pages.sitemap_xml(SITE_URL), media_type="application/xml; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.api_route("/llms.txt", methods=["GET", "HEAD"], include_in_schema=False)
def seo_llms():
    return Response(seo_pages.llms_txt(SITE_URL), media_type="text/plain; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600"})


# Тот же HEAD: этот маршрут ловит «/» и любой адрес одностраничного
# приложения — именно сюда приходит проверка живости хостинга.
# FileResponse на HEAD сам не отправляет тело, только заголовки.
@router.api_route("/{full_path:path}", methods=["GET", "HEAD"])
def index(full_path: str, request: Request):
    # Число сделок в описании страницы (meta description, og:description) —
    # живое: «1300+» в файле устарело на четыре сотни, а поисковик и превью
    # ссылки в мессенджере показывают именно его.
    resp = HTMLResponse(seo_pages.index_html(os.path.join(STATIC_DIR, "index.html")))
    # Токен для базы (scrape_guard): страница получает его вместе с собой.
    # no-cache — браузер переспрашивает страницу (304 дешев) и заодно
    # получает свежий токен, а не берет из кэша страницу с истекшим.
    if scrape_guard.enabled():
        resp.headers["Cache-Control"] = "no-cache"
        scrape_guard.issue_cookie(resp, request)
    return resp
