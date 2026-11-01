"""КОМПАС — точка входа сервера.

Здесь только сборка приложения FastAPI: порядок старта (lifespan), сжатие,
статика, два middleware и подключение роутеров из пакета `app/`. Маршруты
и логика живут по областям (docs/server_layout.md):

    app/core.py       общее: журнал, пути, сессия БД, вход, адреса консоли
    app/fns.py        ФНС и финансы компаний, мультипликаторы
    app/assistant.py  /api/ask, модель, чистка ответа, стенд, отзывы, диалоги
    app/accounts.py   вход, кабинет, подписки, уведомления, правки, кабинет компании
    app/ops.py        /health с отпечатком сборки, дашборд, посещаемость, сводки
    app/console.py    Telegram-консоль: вебхук, опрос, кнопки, мост к рутинам
    app/site.py       robots, отдача базы, PDF, значки, SEO-страницы, ловилка адресов

Имена всех модулей читаются через `main.<имя>` (тесты, скрипты), подменяются —
в модуле-владельце (app/reexport.py). До 1 ноября 2026 все это лежало в одном
файле на 8,5 тыс. строк с восемью `on_event("startup")` (H7).
"""
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import data_refresh
import scrape_guard
from app import accounts, assistant, console, core, fns, ops, site
from app import reexport as _reexport
from app.core import STATIC_DIR, logger


@asynccontextmanager
async def lifespan(_app):
    """Один порядок старта вместо восьми `on_event("startup")`: таблицы
    аккаунтов, сверка подписок, сводка за неделю, подтягивание данных,
    докачка ФНС, индекс ассистента, опрос Telegram, сводка притока. Все
    долгое — в своих потоках (daemon), поэтому на остановке делать нечего."""
    accounts._create_account_tables()
    accounts._match_subscriptions_against_new_deals()
    accounts._start_weekly_digest()
    _start_data_refresh()
    fns._sync_fns_from_registry()
    assistant._warm_assistant_index()
    console._start_telegram_polling()
    ops._start_intake_summary()
    yield


app = FastAPI(title="КОМПАС", lifespan=lifespan)

# Сжатие ответов. База сделок — 4,6 МБ текста, и до этого она уезжала в браузер
# как есть: 4695 КБ по сети на каждый первый заход. JSON сжимается в шесть раз,
# так что это самая дешевая правка из возможных — одна строка вместо дробления
# файла на части и переписывания загрузчика.
# minimum_size: мелочь сжимать дороже, чем отдать как есть.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Шрифт фирменной карточки каталога (static/fonts/*.woff2): на хостинге
# Python не знал этого расширения и отдавал шрифт как text/plain (6 октября
# 2026) — браузеры терпят, но тип должен быть честным.
mimetypes.add_type("font/woff2", ".woff2")
# Статика монтируется ДО роутеров: иначе ловилка всех адресов (site) заберет
# /static/... себе и отдаст index.html вместо шрифта.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Роутеры — в порядке областей. Порядок важен только для site: там ловилка
# всех адресов и значки по шаблону, они обязаны идти последними.
for _r in (fns.router, assistant.router, accounts.router, ops.router, console.router, site.router):
    app.include_router(_r)


# --------------------------------------------------------------------------
# Защита базы от легкого скачивания (16 октября 2026, scrape_guard.py,
# docs/scraping_protection.md). Выключатель — SCRAPE_GUARD=0.
# --------------------------------------------------------------------------
# www.projectcompass.ru отдавал ту же копию сайта со статусом 200 — для
# поисковика это два одинаковых сайта, и вес в выдаче делится (23 октября 2026,
# подключение Яндекс Вебмастера). Постоянный редирект на основной адрес.
@app.middleware("http")
async def www_to_apex_middleware(request: Request, call_next):
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host.startswith("www."):
        target = f"https://{host[4:]}{request.url.path}"
        if request.url.query:
            target += "?" + request.url.query
        return RedirectResponse(target, status_code=301)
    return await call_next(request)


@app.middleware("http")
async def scrape_guard_middleware(request: Request, call_next):
    if not scrape_guard.enabled():
        return await call_next(request)
    path = request.url.path
    # Старый публичный адрес базы закрыт снаружи. Сервер, тесты и скрипты
    # pipeline читают файл С ДИСКА — их это не касается. Служебный ключ
    # пускает и сюда: рутины со старым кодом не должны ослепнуть.
    if path == scrape_guard.STATIC_DATA_PATH and not scrape_guard.service_key_ok(
            request.headers, request.query_params.get("token", "")):
        scrape_guard.bump("static_path_closed")
        return JSONResponse({"error": "not found"}, status_code=404)
    group = scrape_guard.group_of(path, request.method)
    if group and not scrape_guard.service_key_ok(request.headers, request.query_params.get("token", "")):
        ip = scrape_guard.client_ip(request.headers, request.client.host if request.client else None)
        if ip:
            wait = scrape_guard.too_many(group[0], group[1], ip)
            if wait:
                scrape_guard.bump("rate_" + group[0])
                logger.warning("частые запросы: группа %s, адрес %s", group[0], ip)
                return JSONResponse({"error": "Слишком много запросов подряд. Попробуйте через несколько минут."},
                                    status_code=429, headers={"Retry-After": str(int(wait))})
    return await call_next(request)


# Свежая база без пересборки: рутины коммитят данные 4–5 раз в час, и каждый
# такой пуш до 3 сентября 2026 перезапускал сайт (три пуша за минуту дали 502
# на девять минут). Почему так и что качается — docstring data_refresh.py.
def _start_data_refresh():
    data_refresh.ON_CHANGE.append(console._console_after_refresh)
    data_refresh.start()


# ИМЕНА ДЛЯ ТЕСТОВ И СКРИПТОВ. Все, что раньше жило в main.py, читается через
# `main.<имя>` по-прежнему. Подменять (monkeypatch) нужно в модуле-владельце:
# `app.assistant.call_llm`, а не `main.call_llm` — иначе роутер подмены не
# увидит. Попытка подменить через main падает с подсказкой, где владелец.
_reexport.install(globals(), (core, fns, assistant, accounts, ops, console, site))
