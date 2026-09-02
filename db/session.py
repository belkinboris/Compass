import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./kompas.db")

# check_same_thread нужен только SQLite — на Postgres (Timeweb) этот аргумент
# просто не передаём.
# check_same_thread нужен только SQLite. Для Postgres — connect_timeout: старт
# сайта синхронно ходит в базу (миграции колонок, сверка подписок), и пока
# соединение не установлено, uvicorn не начинает принимать запросы — Caddy
# отдаёт 502. Без предела ожидания недоступная база вешала бы сайт на
# неопределённое время; с пределом старт продолжается через 10 секунд, а
# ошибка уходит в лог (ветки startup уже обёрнуты в try). pool_pre_ping —
# чтобы оборванное соединение из пула не превращалось в 500 на первом
# запросе после простоя. Записано 3 сентября 2026 после ночного простоя
# сайта (502 больше 20 минут при исправном коде на main).
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    _engine_kwargs = {}
else:
    _connect_args = {"connect_timeout": 10}
    _engine_kwargs = {"pool_pre_ping": True}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Session:
    return SessionLocal()
