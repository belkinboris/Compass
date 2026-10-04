#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сводка за неделю: новые сделки в базе — на сайт (раздел «Уведомления»),
в Telegram, если он подключён, и на почту, когда она настроена.

С 4 октября 2026 рассылку делает сам сайт, по понедельникам в 10:00 МСК
(`main._start_weekly_digest`); до этого скрипт не запускал никто, а
переключатель «Еженедельная сводка» в кабинете висел с подписью «Скоро».
Ручной запуск остался для проверки: без ключа — только текст сводки.

    python3 pipeline/send_weekly_digest.py           # показать текст
    python3 pipeline/send_weekly_digest.py --write   # разослать
"""
from __future__ import annotations
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TITLE = "Сводка «Компаса» за неделю"
SHOWN = 10


def _plural(n, one, few, many):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def is_listing(deal) -> bool:
    """Лот на торгах без покупателя — новость, но не сделка (решение
    владельца 3 октября 2026); в сводке он считается отдельно."""
    return deal.get("type") == "Продажа с торгов" and deal.get("status") != "Закрыта"


def digest_body(deals, today: date) -> str | None:
    """Текст сводки или None, если за неделю в базе не появилось ничего.
    Неделя — по дате появления карточки в «Компасе» (`added`), а не по дате
    сделки: читателю важно, что нового у нас, а не когда стороны подписали."""
    since = (today - timedelta(days=7)).isoformat()
    fresh = [d for d in deals if str(d.get("added") or d.get("date") or "")[:10] >= since]
    real = sorted((d for d in fresh if not is_listing(d)),
                  key=lambda d: (str(d.get("added") or ""), str(d.get("date") or "")), reverse=True)
    lots = [d for d in fresh if is_listing(d)]
    if not real and not lots:
        return None
    lines = []
    if real:
        n = len(real)
        lines.append("За неделю в «Компасе» %d %s:" % (
            n, _plural(n, "новая сделка", "новые сделки", "новых сделок")))
        for deal in real[:SHOWN]:
            status = str(deal.get("status") or "").strip()
            lines.append("• %s%s" % (str(deal.get("title") or "").strip(),
                                     " — %s" % status.lower() if status else ""))
        if n > SHOWN:
            lines.append("И ещё %d — на сайте." % (n - SHOWN))
    if lots:
        k = len(lots)
        lines.append("%s%d %s на торги." % ("" if not real else "\n", k, _plural(
            k, "лот выставлен", "лота выставлены", "лотов выставлено")))
    return "\n".join(lines)


def send_digest(db, deals, today: date, base_url: str) -> int:
    """Разослать всем, у кого включена сводка. Возвращает число адресатов."""
    from sqlalchemy import select
    from db.models import User
    from notification_service import create_notification, get_preferences

    body = digest_body(deals, today)
    if not body:
        return 0
    sent = 0
    for user in db.scalars(select(User).order_by(User.id)).all():
        if not get_preferences(db, user.id).weekly_digest:
            continue
        create_notification(db, user, title=TITLE, body=body,
                            link="%s/#/deals" % base_url.rstrip("/"), kind="weekly_digest")
        sent += 1
    return sent


def main(argv) -> int:
    from deal_catalog import load_deals
    deals = list(load_deals().values())
    today = date.today()
    if "--write" not in argv:
        print(digest_body(deals, today) or "За неделю новых карточек нет.")
        return 0
    from db.session import SessionLocal
    base = os.environ.get("APP_BASE_URL", "https://projectcompass.ru")
    with SessionLocal() as db:
        print("Сводка разослана: %d адресатов." % send_digest(db, deals, today, base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
