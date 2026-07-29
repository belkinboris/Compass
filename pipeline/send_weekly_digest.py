#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Еженедельная сводка новых и обновлённых сделок.

Запускается cron раз в неделю. Даже без SMTP/Telegram уведомление появится в
личном кабинете; внешние каналы включатся автоматически после настройки.
"""
from __future__ import annotations
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from db.models import User
from db.session import SessionLocal
from deal_catalog import load_deals
from notification_service import create_notification, get_preferences


def _deal_date(item):
    try:
        return date.fromisoformat(str(item.get("date") or "")[:10])
    except ValueError:
        return None


def main() -> int:
    since = date.today() - timedelta(days=7)
    deals = [d for d in load_deals().values() if (_deal_date(d) or date.min) >= since]
    deals.sort(key=lambda d: str(d.get("date") or ""), reverse=True)
    if not deals:
        print("За неделю новых карточек нет; рассылка не создана.")
        return 0
    top = deals[:12]
    lines = [f"За последние 7 дней в «Компасе»: {len(deals)} новых или обновлённых карточек."]
    for deal in top:
        lines.append(f"• {deal.get('title')} — {deal.get('status') or 'статус не раскрыт'}")
    if len(deals) > len(top):
        lines.append(f"И ещё {len(deals)-len(top)} карточек в базе.")
    base = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")
    with SessionLocal() as db:
        users = list(db.scalars(select(User).order_by(User.id)).all())
        sent = 0
        for user in users:
            pref = get_preferences(db, user.id)
            if not pref.weekly_digest:
                continue
            create_notification(db, user, title="Что произошло на рынке сделок за неделю",
                                body="\n".join(lines), link=f"{base}/#/deals", kind="weekly_digest")
            sent += 1
    print(f"Сводка создана для {sent} пользователей.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
