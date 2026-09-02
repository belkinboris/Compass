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
