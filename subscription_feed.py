# -*- coding: utf-8 -*-
"""Сверка подписок с новыми сделками — на стороне САЙТА.

ПОЧЕМУ ЗДЕСЬ, А НЕ В ПРИТОКЕ. Приток работает в одноразовом контейнере в
другом облаке, а база пользователей стоит во внутренней сети хостинга
(адрес вида `192.168.x.x` виден только машинам, стоящим там же). Дотянуться
до неё из прогона притока невозможно в принципе — не «не настроили», а
физически нет маршрута. Поэтому подписки сверяет то, что живёт рядом с
базой: сам сайт.

КОГДА ЗАПУСКАТЬ — НЕ НУЖЕН НИ CRON, НИ ПЛАНИРОВЩИК. Новые карточки попадают
на сайт ровно одним способом: деплоем нового `deals_promoted.json`. Значит,
единственный момент, когда есть что сверять, — старт процесса после деплоя,
и проверка висит именно там. Планировщик внутри процесса тут был бы лишней
деталью, которая просыпается 24 раза в сутки, чтобы 23 раза ничего не найти.

ПЕРВЫЙ ПРОГОН НИКОГО НЕ БУДИТ. Пока таблица `deals_seen` пуста, мы не знаем,
что из полутора тысяч карточек «новое», — и честный ответ «всё» означал бы
залп из тысячи уведомлений. Поэтому первый прогон только ЗАПОМИНАЕТ состав
базы и не шлёт ничего (тот же приём, что `seed_telegram_posts_backlog.py` у
канала). Уведомления начинаются со следующего деплоя, который принесёт
карточку, которой в таблице ещё нет.

ЧТО СЧИТАЕТСЯ СОВПАДЕНИЕМ. Условия подписки складываются по И: «отрасль X от
суммы Y» — это про сделки в X дороже Y, а не про объединение двух лент.
Ключевое слово ищется по НАЗВАНИЯМ (заголовок и стороны сделки), а не по
всему тексту карточки: «Сбер» стоит кредитором в десятках чужих сделок, и
поиск по всему тексту превратил бы подписку на компанию в ленту рынка.

ПОРОГ СУММЫ МОЛЧИТ, КОГДА НЕ УВЕРЕН. Сумма — свободный текст («200–550 млн ₽
(по оценке)», «~4,5–5 млрд ₽», «Не раскрыта», «$1,2 млрд»). Если разобрать её
в млн ₽ не удалось, подписка с порогом не срабатывает: лучше не прислать
письмо, чем прислать не по адресу. По той же причине из диапазона берётся
НИЖНЯЯ граница, а валюта не конвертируется — курса в базе нет и выдумывать
его нельзя.
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger("kompas.subscriptions")

KIND = "subscription_match"

# Заглушки суммы. Анкерим с обеих сторон: «не раскрыта (EV оценена в 21 млрд ₽)»
# — это данные, а не пустота.
PLACEHOLDER = re.compile(
    r"^\s*(?:не\s+раскрыт[а-яё]*|публично\s+не\s+сообщал[а-яё]*|"
    r"не\s+привлекал[а-яё]*|нет\s+данных|[—–-])\s*$", re.I)

UNITS = {"тыс": 0.001, "млн": 1.0, "млрд": 1000.0, "трлн": 1000000.0}

# Пробел внутри числа — разделитель разрядов («41 500 млн ₽»), запятая —
# десятичная часть («12,5 млрд»). Значок ₽ обязателен: он и есть признак того,
# что число рублёвое, — у доллара и евро значок стоит ПЕРЕД числом.
NUM = r"\d[\d\s\u00a0]*(?:[.,]\d+)?"
AMOUNT = re.compile(
    r"(" + NUM + r")\s*\+?"                   # число; «300+ млн» — тоже нижняя граница
    r"(?:\s*[–—-]\s*" + NUM + r")?"  # верхняя граница диапазона — не берём
    r"\s*(?:(тыс|млн|млрд|трлн)[а-яё.]*\s*)?"  # единицы может и не быть
    r"₽")                                      # и обязательный значок рубля

# Сумма без единицы — это рубли («450 090 ₽», «1 ₽» у символических сделок).
UNIT_NONE = 1e-6


def amount_mln_rub(text):
    """Сумма карточки в млн ₽ или None, если разобрать нельзя."""
    if not text or PLACEHOLDER.match(text):
        return None
    found = AMOUNT.search(text)
    if not found:
        return None
    raw = re.sub(r"[\s\u00a0]", "", found.group(1)).replace(",", ".")
    try:
        value = float(raw)
    except ValueError:
        return None
    return value * (UNITS[found.group(2)] if found.group(2) else UNIT_NONE)


def self_check():
    """Правило проверяется на себе, а не на глаз (соглашение репозитория)."""
    assert amount_mln_rub("12,5 млрд ₽") == 12500.0
    assert amount_mln_rub("41 500 млн ₽") == 41500.0
    # Из диапазона — нижняя граница; тильда и «(по оценке)» не мешают.
    assert amount_mln_rub("200–550 млн ₽ (по оценке)") == 200.0
    assert amount_mln_rub("~4,5–5 млрд ₽ (по оценке)") == 4500.0
    # Валюта не конвертируется, заглушка — не число.
    assert amount_mln_rub("$1,2 млрд") is None
    assert amount_mln_rub("€800 млн") is None
    assert amount_mln_rub("Не раскрыта") is None
    assert amount_mln_rub("не раскрыта") is None
    # А это не заглушка: сумма названа в скобках и должна читаться.
    assert amount_mln_rub("Не раскрыта (EV оценена в 21 млрд ₽)") == 21000.0
    assert amount_mln_rub("17,7 млрд ₽ (191,5 млн $)") == 17700.0
    # Без единицы значок ₽ значит рубли, а не миллионы.
    assert amount_mln_rub("450 090 ₽") == 0.45009
    assert amount_mln_rub("2 800 000 000 ₽") == 2800.0
    assert amount_mln_rub("1 ₽") == 1e-6
    assert amount_mln_rub("300+ млн ₽") == 300.0
    assert amount_mln_rub("1+ млрд ₽") == 1000.0
    # Числа нет вовсе — молчим, а не угадываем «несколько».
    assert amount_mln_rub("несколько сотен млн ₽ (по оценке)") is None
    assert amount_mln_rub("несколько млрд ₽ (точно не указана)") is None


def company_names(deal, companies):
    """Имена профилей, на которые ссылается карточка."""
    names = []
    for field in ("buyer", "target", "seller_id", "asset_id"):
        profile = (companies or {}).get(deal.get(field) or "")
        if profile and profile.get("name"):
            names.append(profile["name"])
    return names


def haystack(deal, companies):
    """Текст, по которому ищется ключевое слово подписки: только названия."""
    parts = [deal.get("title") or "", deal.get("seller") or "",
             deal.get("buyer_name") or "", deal.get("asset") or ""]
    parts.extend(company_names(deal, companies))
    return " | ".join(parts).lower()


def _num(value):
    return ("%.0f" % value) if abs(value - round(value)) < 1e-9 else ("%.1f" % value)


def match_reason(flt, deal, companies):
    """Почему эта сделка подходит подписке. None — не подходит."""
    reasons = []
    industry = (getattr(flt, "industry", None) or "").strip()
    keyword = (getattr(flt, "keyword", None) or "").strip()
    floor = getattr(flt, "min_amount_mln_rub", None)

    if not industry and not keyword and floor is None:
        return None  # подписки «на всё» не бывает, её не даёт создать и API

    if industry:
        if (deal.get("ind") or "") != industry:
            return None
        reasons.append("отрасль «%s»" % industry)
    if keyword:
        if keyword.lower() not in haystack(deal, companies):
            return None
        reasons.append("упоминание «%s»" % keyword)
    if floor is not None:
        value = amount_mln_rub(deal.get("sum"))
        if value is None or value < float(floor):
            return None
        reasons.append("сумма от %s млн ₽" % _num(float(floor)))
    return ", ".join(reasons)


def notify_new_deals(db, deals, companies, base_url=None):
    """Разослать уведомления по подпискам о переданных карточках.

    Возвращает счётчики; ничего не печатает — за отчёт отвечает вызывающий.
    Повтор отсекается существующей строкой `Notification`: отдельного файла
    состояния «о чём уже сообщали» здесь нет и не нужно.
    """
    from sqlalchemy import select

    import notification_service
    from db.models import Notification, SavedFilter, User

    base = (base_url or os.environ.get("APP_BASE_URL") or "https://projectcompass.ru").rstrip("/")
    filters = list(db.scalars(select(SavedFilter).where(SavedFilter.active.is_(True))).all())
    stats = {"filters": len(filters), "subscribers": len({f.user_id for f in filters}),
             "deals": len(deals), "created": 0, "repeat": 0}

    for deal in deals:
        # Одному человеку — одно уведомление о сделке, даже если совпали две
        # его подписки: читателю важна сделка, а не сколько его фильтров
        # на неё среагировало.
        hits = {}
        for flt in filters:
            reason = match_reason(flt, deal, companies)
            if reason:
                hits.setdefault(flt.user_id, []).append(reason)
        for user_id, reasons in hits.items():
            seen = db.scalar(select(Notification).where(
                Notification.user_id == user_id,
                Notification.deal_id == deal["id"],
                Notification.kind == KIND))
            if seen:
                stats["repeat"] += 1
                continue
            user = db.get(User, user_id)
            if not user:
                continue
            notification_service.create_notification(
                db, user,
                title="Новая сделка по вашей подписке: %s" % (deal.get("title") or deal["id"]),
                body="Совпало: %s." % "; ".join(sorted(set(reasons))),
                link="%s/#/deal/%s" % (base, deal["id"]),
                deal_id=deal["id"], kind=KIND)
            stats["created"] += 1
    return stats


def scan_new_deals(db, deals, companies, base_url=None):
    """Отметить карточки, которых на сайте ещё не было, и разослать по подпискам.

    Первый прогон только запоминает состав базы (см. docstring модуля).
    """
    from db.models import DealSeen

    known = {row for (row,) in db.query(DealSeen.deal_id).all()}
    fresh = [d for d in deals if d.get("id") and str(d["id"]) not in known]
    if not fresh:
        return {"seeded": 0, "fresh": 0, "created": 0, "repeat": 0,
                "filters": 0, "subscribers": 0, "deals": 0}

    for deal in fresh:
        db.add(DealSeen(deal_id=str(deal["id"])))
    db.commit()

    if not known:
        # Первый прогон: база «увидена» целиком, но это не новости.
        return {"seeded": len(fresh), "fresh": 0, "created": 0, "repeat": 0,
                "filters": 0, "subscribers": 0, "deals": 0}

    stats = notify_new_deals(db, fresh, companies, base_url=base_url)
    stats["seeded"] = 0
    stats["fresh"] = len(fresh)
    return stats


def scan_on_startup():
    """Точка входа для старта сайта: читает базу с диска и сверяет подписки.

    Ошибка здесь не должна ронять сайт: без уведомлений он работает, без
    старта — нет. Поэтому всё в try, а результат уходит в лог, а не в ответ.
    """
    try:
        import deal_catalog
        from db.session import get_session

        data = deal_catalog._read(deal_catalog.PROMOTED) or {}
        deals = data.get("deals") or []
        if not deals:
            logger.warning("подписки не сверены: база сделок не прочиталась")
            return None
        db = get_session()
        try:
            stats = scan_new_deals(db, deals, data.get("companies") or {})
        finally:
            db.close()
        if stats["seeded"]:
            logger.info("подписки: первый прогон, запомнили %d карточек, "
                        "уведомления начнутся со следующего деплоя", stats["seeded"])
        elif stats["fresh"]:
            logger.info("подписки: новых карточек %d, уведомлений создано %d",
                        stats["fresh"], stats["created"])
        return stats
    except Exception as exc:  # noqa: BLE001 — сайт важнее рассылки
        logger.error("подписки не сверены: %s", exc)
        return None
