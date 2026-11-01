# Устройство сервера: main.py и пакет app/

> **Когда читать:** добавляете или правите маршрут API, фоновый поток или шаг
> старта сервера; пишете тест, который подменяет серверную функцию; ищете, в
> каком файле живет обработчик адреса.
>
> Заведено 1 ноября 2026 (бэклог H7): до этого весь сервер был одним
> `main.py` на 8540 строк — 91 маршрут, 8 `on_event("startup")` и пять
> фоновых потоков вперемешку. Выкладка, сервер и окружение — `docs/release.md`;
> код интерфейса — `docs/site_code.md`; здесь только раскладка серверного кода.

> **Баги этой подсистемы:** `known_issues/ops.md` — открыть, когда чините ее.

## Что где лежит

`main.py` (130 строк) — точка входа: `app = FastAPI(lifespan=…)`, сжатие,
статика, два middleware (редирект с www, защита базы от скачивания) и
`include_router` по областям. Логики в нем нет. Маршруты — в `app/`:

| модуль | что внутри | адреса |
|---|---|---|
| `app/core.py` | журнал, `BASE_DIR`/`STATIC_DIR`, `get_db`, `_current_user`, `ACCESS_GATE`, `COOKIE_SECURE`, `SITE_URL`, общий HTTP-клиент `_http`, `_read_json`, проверка токена моста `_moderation_token_ok`, адреса консоли (`_review_chat_ids`, `_channel_chat_ids`, `_chat_is_channel`, `_console_thread_id`, имена тем) | нет маршрутов |
| `app/fns.py` | ЕГРЮЛ, отчетность, собственники, докачка по git-реестру (`_sync_fns_from_registry`, дневной потолок), скрининг, мультипликаторы, `_bank_finance` | `/api/fns/*`, `/api/companies/{id}/fns*`, `/api/finance/*`, `/api/analytics/*` |
| `app/assistant.py` | `/api/ask` и лимит мест, вызов модели `call_llm`, чистка ответа `_polish_answer`, стенд моделей, обратная связь, история диалогов, «Анализ Компаса» на карточке (оценка цены, анализ, контекст) | `/api/ask`, `/api/assistant/*`, `/api/deals/{id}/price-estimate`, `/analysis`, `/context-analysis` |
| `app/accounts.py` | регистрация и вход, кабинет, подписки, уведомления, комментарии, правки от посетителей, кабинет компании; таблицы на старте (`_create_account_tables`), сверка подписок, сводка за неделю | `/api/auth/*`, `/api/me*`, `/api/subscriptions*`, `/api/notifications*`, `/api/deals/{id}/watch`, `/comments`, `/corrections`, `/api/claims*`, `/api/ops/claims*` |
| `app/ops.py` | `/health` с отпечатком сборки, дашборд основателей, активность и посещаемость, состояние подтягивания данных, сводка притока в 18:00 | `/health`, `/ops*`, `/api/ops/*` (кроме claims и milestone), `/api/t`, `/api/data/status` |
| `app/console.py` | вебхук и опрос Telegram, разбор обновлений (`_handle_telegram_update`), кнопки решений, темы форума, тема «Клод», очередь карточек, мост к рутинам | `/api/telegram/*`, `/api/moderation/*`, `/api/access/*`, `/api/claude/*`, `/api/ops/channel-edits`, `/api/ops/milestone-draft` |
| `app/site.py` | robots, отдача базы по токену, вебинары, PDF-выгрузки, значки, страницы для поисковиков, ловилка всех адресов | `/robots.txt`, `/api/data/*`, `/api/webinars`, `/api/deals/{id}/export`, `/deal/*`, `/company/*`, `/sitemap.xml`, `/{всё остальное}` |
| `app/reexport.py` | имена модулей читаются через `main.<имя>`, подмена через `main` запрещена (см. «Как подменять в тестах») | — |

Где обработчик адреса: `grep -n '"/api/…"' app/*.py`.

## Слои и импорты: цикла нет

Модули выстроены в ряд, и каждый импортирует только тех, кто левее:

    core ← fns ← assistant ← accounts ← ops ← console ← site

`core` не импортирует ничего из `app/`. Так разнесено нарочно: взаимные
импорты между областями работали бы в Python, но ломались бы при первом же
обращении к соседу на уровне модуля, и ошибка зависела бы от того, кто
импортирован первым. Если новой функции нужен сосед справа — она стоит не
в том модуле (или общая часть должна уехать в `core`). Поэтому, например,
«Анализ Компаса» на карточке лежит в `assistant`, а не в `fns`: ему нужна
модель, а `fns` левее `assistant`.

Общий HTTP-клиент `_http` и `_read_json` — в `core`, хотя первым пользуется
в основном ассистент: их зовут три модуля, и тесты их подменяют.

## Как добавить маршрут

1. Выбрать модуль по таблице; в нем уже есть `router = APIRouter()` —
   пишется `@router.get("/api/…")`, `db=Depends(get_db)` и `Depends(_current_user)`
   берутся из `app.core`.
2. Новая область — новый `app/<область>.py` со своим `router`, строкой в
   `main.py` (`for _r in (…)`), **до `site.router`**: там ловилка всех адресов
   и значки по шаблону `/{icon_name}.ico`, они обязаны идти последними.
   Статика монтируется до роутеров по той же причине.
3. `GET`-маршрут, который спрашивает не человек, объявляется
   `@router.api_route(..., methods=["GET", "HEAD"])` — платформа проверяет
   живость методом HEAD (`docs/release.md`, «Маршруты, которые спрашивает не человек»).
4. Функция, которую будут подменять тесты, вызывается из других модулей
   через атрибут модуля: `assistant.call_llm(...)`, `core._review_chat_ids(db)`,
   `fns._sector_multiples(db)`, а не `from app.assistant import call_llm`.
   Иначе подмена в модуле-владельце до вызова не дойдет. Внутри своего
   модуля — обычное имя.
5. Выложить: `app/*.py` — код, `release.py` его видит (`test_docs.py`), а
   `/health` отдает отпечаток папки (ниже).

## Один lifespan вместо восьми on_event

Порядок старта — функция `lifespan` в `main.py`, и он тот же, что был у
восьми `@app.on_event("startup")`: таблицы аккаунтов и миграция колонок →
сверка подписок → сводка за неделю → подтягивание данных (`data_refresh`) →
докачка ФНС → индекс ассистента → опрос Telegram → сводка притока в 18:00.
Сами функции старта живут в модулях своих областей (`accounts._start_weekly_digest`,
`console._start_telegram_polling` и т. д.); `_start_data_refresh` остался в
`main.py`, потому что подписывает на смену данных обработчик консоли.

Новый шаг старта — отдельная функция в модуле области и строка в `lifespan`
на своем месте в порядке. Правила прежние: долгое — в поток `daemon`, в
тестах шаг молчит по `PYTEST_CURRENT_TEST`, без ключа в окружении — тихий
пропуск, а не ошибка. Остановки процессу не нужно: потоки `daemon`, и
обработчик `shutdown`, гасивший процесс сам, снят еще 8 сентября 2026
(`docs/release.md`, «Когда сайт лёг»).

`with TestClient(main.app) as c:` запускает `lifespan`; `TestClient(main.app)`
без `with` — нет (таблиц в свежей тестовой базе тогда не будет).

## Как подменять в тестах

До разнесения тесты делали `monkeypatch.setattr(main, "call_llm", …)` и
`main.X = …`. Теперь имена живут в модулях, и подмена копии в `main` не
изменила бы ничего: роутер зовет настоящую функцию, а тест молча проверял
бы не то. Поэтому:

- **Читать через `main` можно**: `main._polish_answer(...)`, `main.SYSTEM_BASE`,
  `inspect.getsource(main._create_account_tables)` работают — `app/reexport.py`
  копирует в `main` все имена всех модулей (первый владелец слева главный).
- **Подменять — в модуле-владельце**: `from app import assistant` и
  `monkeypatch.setattr(assistant, "call_llm", …)`. Владельцы самых частых
  подмен: `assistant` — `call_llm`, `yandex_search`, `_ask_slots`,
  `ASK_QUEUE_WAIT`; `core` — `_http`, `_read_json`, `_review_chat_ids`,
  `_console_thread_id`, `_CHAT_IS_CHANNEL`, `ACCESS_GATE`, `_in_background`;
  `fns` — `get_company_profile`, `fns_registry_by_company_id`, `FNS_*`,
  `_fns_requests_today`, `_sector_multiples`; `console` — `_handle_telegram_update`,
  `_console_answer`, `_already_on_site`, `_answered_decisions`,
  `_milestone_already_out`, `CLAUDE_ACK_QUIET_SECONDS`; `site` — `DEAL_EXPORT_*`.
- **Подмена через `main` падает** с `AttributeError`, в котором назван
  модуль-владелец, — это нарочно, чтобы устаревший тест не стал зеленым
  молча. Исключение — имена, которые `main.py` импортирует сам (`logger`,
  `STATIC_DIR`); их не подменяют.
- Тест, читающий **текст файла** (регэксп кнопки, умолчание переменной),
  читает файл модуля: `Path(console.__file__)`, `app/core.py`, а не `main.py`.
- Подмена `main.notification_service.tg_api`, `main.httpx.post`,
  `main.threading.Thread` меняет сам сторонний модуль — работает как раньше.

## Отпечаток сборки и выкладка

`/health` отдает `build` с тремя ключами: `main.py`, `static/index.html` и
`app/` — один отпечаток по всем `app/*.py` (имя и содержимое, по алфавиту).
Третий ключ появился вместе с пакетом: правка роутера не трогает `main.py`,
и без него `pipeline/check_deploy.py` не увидел бы, что сайт отстал. Расчет
в `app/ops.py` (`build_fingerprint`) и в `check_deploy.py` (`local_fingerprint`)
один и тот же; разойдутся — `test_health_carries_a_build_fingerprint`.
Сайт со старым кодом отдает два ключа — `check_deploy` считает это отставанием,
и это правда.

## Замер 1 ноября 2026

До: `main.py` 8540 строк, 91 маршрут и 2 middleware в одном файле, 8
`on_event("startup")`, 5 фоновых потоков, тесты подменяли 26 разных имен
через `main`. После: `main.py` 130 строк; `app/` — core 251, fns 786,
assistant 3290, accounts 1083, ops 635, console 2308, site 335 строк;
маршрутов столько же (96 записей в `app.routes` вместе со статикой), ни одной
правки поведения; полный `pytest` зеленый. Лимит одновременных вопросов
(`ASK_MAX_CONCURRENT`, ответ с intent `busy`) сделан 31 октября; на экране
такой ответ — мягкая плашка без подсказок и «Ответ помог?», вопрос
возвращается в поле ввода (`test_busy_assistant_answer_is_a_soft_note_not_a_model_answer`).
