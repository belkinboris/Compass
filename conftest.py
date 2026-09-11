# -*- coding: utf-8 -*-
"""Своя БД для тестов аккаунтов.

`main.py` и `db/session.py` читают `DATABASE_URL` один раз, при первом
импорте, — поэтому переменная должна быть выставлена ДО того, как pytest
соберёт первый тестовый модуль. conftest.py гарантированно загружается раньше
любого test_*.py, независимо от порядка сбора. Без этого прогон тестов писал
бы в рабочий `kompas.db` и результат зависел бы от того, какой тестовый файл
импортировал `main` первым.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_accounts.db")
os.environ.setdefault("COOKIE_SECURE", "false")  # TestClient ходит по http
# Вход по заявке (ACCESS_GATE, main.py) по умолчанию ВКЛЮЧЁН — для тестов
# выключаем, иначе каждый экран и каждая регистрация оказались бы за дверью.
# Тесты самого гейта включают его явно: monkeypatch.setattr(main, "ACCESS_GATE",
# True) или отдельный сервер с ACCESS_GATE=1 (test_ui.py).
os.environ.setdefault("ACCESS_GATE", "0")
# Ключ API-ФНС в контейнере сессии — боевой: сервер тестов на старте запускал
# бы платную докачку реестра в тестовую SQLite и полминуты отвечал с задержкой
# (6 сентября 2026: таймауты Playwright и приёмочного скрипта нашлись по логу
# сервера). Тестам ключ не нужен вовсе — гасим, а не setdefault.
os.environ["API_FNS_KEY"] = ""
os.environ.setdefault("FNS_DAILY_RESYNC", "0")
os.environ.setdefault("DATA_REFRESH_ENABLED", "0")
# Тот же класс, что и API_FNS_KEY выше: секреты консоли/бота в контейнере
# сессии — боевые. `send_telegram.channel_address()` и `approve.
# fetch_decisions()` делают живой сетевой запрос к projectcompass.ru всякий
# раз, когда `MODERATION_TOKEN`/`TELEGRAM_WEBHOOK_SECRET` заданы, — НЕЗАВИСИМО
# от того, есть ли `TELEGRAM_BOT_TOKEN` (найдено 6 сентября 2026: тест
# `test_main_without_token_never_touches_network_or_writes` завис на несколько
# минут в SSL-хендшейке через прокси, потому что unset был только у
# TELEGRAM_BOT_TOKEN/TELEGRAM_CHANNEL_ID). Тестам, которым нужен путь «с
# токеном», ставят его сами через monkeypatch.setenv — он подменяет это
# значение только на время теста.
# Страховка «пост не уходит раньше карточки» (send_telegram.
# deals_missing_on_site, 11 сентября 2026) спрашивает боевой сайт, какие
# карточки он уже отдаёт. В тестах карточки выдуманные — на сайте их нет по
# определению, и без выключателя страховка отсекала бы каждый тестовый пост.
# Тест самой страховки включает её обратно через monkeypatch.setenv.
os.environ["PUBLISH_WAIT_FOR_SITE"] = "0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHANNEL_ID"] = ""
os.environ["TELEGRAM_WEBHOOK_SECRET"] = ""
os.environ["MODERATION_TOKEN"] = ""
