# -*- coding: utf-8 -*-
"""ФНС и финансы: ЕГРЮЛ, отчетность, собственники, докачка по реестру,
мультипликаторы и скрининг (docs/server_layout.md)."""
import json
import os
import pathlib
import re
import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

import assistant_retrieval
import company_finance
import deal_catalog
import deal_multiples
from company_catalog import get_company_profile, load_company_catalog
from db.models import (
    FinancialReport,
    FnsSyncRun,
    LegalEntity,
    LegalEntityMatchStatus,
    OwnershipSnapshot,
    OwnershipStake,
    RegistryEvent,
    User,
    UserTier,
)
from db.session import get_session
from fns_client import ApiFnsClient, ApiFnsError, change_text, full_lines_payload
from pipeline.fns_registry import by_company_id as fns_registry_by_company_id
from sqlalchemy import select

from app.core import BASE_DIR, get_db, logger, _current_user, _plain

router = APIRouter()


# Докачка ФНС по git-реестру (pipeline/fns_registry.py) — механика,
# COMPANY_FINANCE_BRIEF.md, раздел «Суждение — в git-реестре, механика — на
# боевом хосте»: суждение «какой ИНН чей» уже принято чтением и лежит в
# реестре, здесь только подтверждается и докачивается отчетность. В отдельном
# потоке — это живые запросы к api-fns.ru (до 25 с таймаута на каждый по
# fns_client.py), и сайт не должен ждать их, чтобы начать отвечать на
# обычные запросы. Ключа нет — тихо пропускаем: это НЕ сбой (ключ на боевом
# хосте может быть еще не добавлен, локальная разработка — тем более).
def _sync_fns_from_registry():
    if not os.environ.get("API_FNS_KEY"):
        return
    # PYTEST_CURRENT_TEST — переменная, которую сам pytest выставляет на
    # время каждого теста: без этой защиты КАЖДЫЙ TestClient(main.app) в
    # тестах бил бы по живому api-fns.ru и тратил платную квоту прогоном
    # тестов — а этот ключ в среде разработки реально задан (см. П0).
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    def _attempt(label):
        db = get_session()
        try:
            _fns_sync_once(db)
        except Exception as e:  # сеть/квота/что угодно — сайт не должен упасть из-за этого
            logger.error("не удалось докачать ФНС из реестра (%s): %s", label, e)
        finally:
            db.close()

    def _run():
        if FNS_STARTUP_SYNC:
            # Пауза до первой живой работы: платформа проверяет живость
            # запросом к сайту, и она должна получить ответ раньше, чем
            # начнется докачка (см. FNS_STARTUP_DELAY_SECONDS выше).
            time.sleep(FNS_STARTUP_DELAY_SECONDS)
            _attempt("при старте")
        else:
            logger.info("ФНС: докачка при старте выключена (FNS_STARTUP_SYNC=0)")
        # Старт процесса перестал быть надежным событием (см. комментарий к
        # _seconds_until_next_fns_window): пока в реестре есть бэклог, докачка
        # повторяется раз в сутки сама, сразу после сброса дневного потолка.
        while FNS_DAILY_RESYNC:
            time.sleep(_seconds_until_next_fns_window())
            _attempt("суточная докачка")

    threading.Thread(target=_run, daemon=True).start()


def _seconds_until_next_fns_window(now: datetime | None = None) -> float:
    """Сколько ждать до следующего окна суточной докачки — пять минут после
    полуночи UTC, когда `_fns_requests_today()` начинает считать с нуля.

    Почему окно вообще нужно. Докачка по реестру шла ТОЛЬКО при старте
    процесса, а процесс на Timeweb перезапускается только пересборкой — с
    3 сентября 2026 пересборку дает лишь пуш кода в `release`, данные едут
    мимо. 5 сентября 2026 /api/fns/status показал: бэклог реестра 278 строк
    (кампания по сторонам сделок 2024 года), три старта за день истратили
    532 запроса при потолке 400, и подтвержденный ИНН «МорТехПрома» из
    свежего поста канала остался несопоставленным — а следующий старт
    случился бы только с очередным пушем кода, которого в выходные может
    не быть вовсе. Раз в сутки после сброса потолка — естественное окно:
    бэклог тает по 60 работ в день без единого деплоя, а при пустом
    бэклоге попытка стоит один проход по реестру без живых запросов."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    window = now.replace(hour=0, minute=5, second=0, microsecond=0)
    if window <= now:
        window += timedelta(days=1)
    return max(60.0, (window - now).total_seconds())


def _fns_sync_once(db) -> dict | None:
    """Одна попытка докачки ФНС по реестру — вынесена из `_run()` отдельной
    функцией, чтобы ее можно было проверить тестом напрямую, без потока и
    без обхода env-гварда `_sync_fns_from_registry()`. Возвращает `stats`
    при реальной попытке синка, `None` при пропуске (потолок достигнут).

    Потолок — самонастраивающийся (Этап 13, П1): при большом бэклоге
    неподтвержденных/несвежих confirmed-строк реестра (кампания
    самопроверки ИНН может разом подтвердить сотни новых) действует
    повышенный `FNS_DAILY_REQUEST_CAP_HIGH`, иначе — обычный
    `FNS_DAILY_REQUEST_CAP`. Не нужно помнить «вернуть лимит обратно»:
    как только бэклог рассосется, потолок сам вернется к обычному."""
    from pipeline.sync_fns import sync_from_registry, registry_backlog
    from fns_client import ApiFnsClient

    backlog = registry_backlog(db)
    cap = (FNS_DAILY_REQUEST_CAP_HIGH if backlog > FNS_BACKLOG_THRESHOLD_FOR_HIGH_CAP
           else FNS_DAILY_REQUEST_CAP)
    used_today = _fns_requests_today(db)
    if used_today >= cap:
        logger.warning(
            "ФНС: дневной потолок запросов достигнут (%d/%d, бэклог реестра %d) — "
            "старт пропускает докачку, до завтра", used_today, cap, backlog)
        return None
    with ApiFnsClient() as client:
        stats = sync_from_registry(db, client, limit=FNS_STARTUP_SYNC_LIMIT)
    logger.info("ФНС из реестра при старте: %s", stats)
    db.add(FnsSyncRun(
        mode="startup",
        companies_total=stats.get("confirmed_now", 0) + stats.get("synced", 0)
        + stats.get("skipped_fresh", 0),
        matched=stats.get("confirmed_now", 0) + stats.get("synced", 0),
        errors=stats.get("errors", 0),
        details_json=json.dumps(stats),
    ))
    db.commit()
    return stats


def _fns_requests_today(db) -> int:
    """Сумма `requests` из FnsSyncRun за текущие календарные сутки (UTC).

    П5''' (COMPANY_FINANCE_BRIEF.md, этап 3): защита не от нехватки квоты
    (ее достаточно — см. «Открытие, которое меняет бюджет» в CLAUDE.md), а
    от петли или бага, который перезапускал бы процесс много раз подряд и
    каждый раз бил по api-fns.ru заново. Счетчик обязан пережить сам
    перезапуск, из-за которого его завели, — поэтому он не переменная
    процесса (умирает вместе с ним), а строка в БД, которая переживает
    рестарт (тот же принцип, что уже применен к `fns_asked` на профиле
    компании — штамп в постоянном хранилище, а не в памяти одного запуска).
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    rows = db.scalars(select(FnsSyncRun).where(FnsSyncRun.started_at >= today_start)).all()
    total = 0
    for row in rows:
        try:
            total += json.loads(row.details_json or "{}").get("requests", 0)
        except (ValueError, TypeError):
            continue
    return total


# «Компания сегодня» не показывает отчетность старше этого числа лет от
# текущего года — правило владельца от 18 августа 2026 после жалобы на
# видимые на сайте показатели банков за 2020-2021 год.
FNS_REPORT_MAX_AGE_YEARS = 2

# ВРЕМЕННО, по прямой просьбе владельца 22 августа 2026: «давай сначала все
# сделаем бесплатно, чтобы я видел как работает». Финансовый блок компании
# показывает полную историю (все отчетные годы, все события ЕГРЮЛ, полный
# состав участников) всем посетителям, не только платным. Когда владелец
# увидит витрину целиком и решит границу бесплатного (см.
# pipeline/COMPANY_FINANCE_BRIEF.md, раздел П6) — выключить флагом здесь,
# без другой правки кода. Скачивание живой БФО (bo_file) остается только для
# вошедших: это не про платность, а про то, что каждый клик — платный запрос
# к API-ФНС (бюджет 3000/год), и открывать его анонимно нельзя ни в каком
# режиме бесплатности.
FNS_ALL_FREE = True


# Медианы мультипликаторов (общая и по отраслям) на «Аналитике» — скрыты до
# утверждения методики оценщиком (разбор рецензента, 6 сентября 2026): сделки
# проходят правила допуска, но их сопоставимость между собой не подтверждена,
# и одна цифра по десятку сделок читается как ориентир рынка. Список сделок с
# ценой и показателем и текст методики показываются по-прежнему. Включить —
# SHOW_MULTIPLE_MEDIANS=1 в окружении боевого хоста.
SHOW_MULTIPLE_MEDIANS = os.environ.get("SHOW_MULTIPLE_MEDIANS", "0") == "1"

# Сколько подтвержденных профилей (pipeline/fns_registry.py) докачивать за
# ОДИН старт процесса. COMPANY_FINANCE_BRIEF.md, раздел П2: расписания нет —
# новые решения реестра появляются деплоем, и старт после деплоя уже и есть
# то самое естественное событие (тот же прием, что и у сверки подписок ниже).
# Потолок — на РЕАЛЬНУЮ работу (sync_from_registry считает limit после
# проверки свежести с 23 августа, не как срез списка), а не на просмотр
# строк реестра: уже свежие профили лимит не тратят вовсе. 23 августа
# 2026 обнаружено, что квота на самом деле по-методная (3000/год на каждый
# метод отдельно, а bo/egr/changes — «по организациям», повторный запрос
# той же организации в год бесплатен) — прежняя осторожность в 30 была
# рассчитана на неверную модель «3000 на все». Поднято до 60, чтобы реестр
# (растет партиями по 50-60) догонял прод за один-два деплоя, а не тянулся
# неделями за счет частоты рестартов процесса.
FNS_STARTUP_SYNC_LIMIT = 60

# Докачка при старте — ВЫКЛЮЧАЕМАЯ и ОТЛОЖЕННАЯ, потому что она стоит на пути
# загрузки живого сайта. 7 сентября 2026 сайт не отвечал полчаса, и в журнале
# приложения последним, что происходило, была именно она. Причину (переполнение
# колонки на Postgres) починили, но урок шире одной ошибки: у шага, который
# ходит в чужой платный API десятками запросов сразу после старта, обязан быть
# выключатель в переменной окружения (FNS_STARTUP_SYNC=0) и пауза, чтобы сайт
# успел начать отвечать до того, как начнется тяжелая работа. Суточное окно
# (_seconds_until_next_fns_window) все равно догонит бэклог без этого шага.
FNS_STARTUP_SYNC = os.environ.get("FNS_STARTUP_SYNC", "1") != "0"
FNS_STARTUP_DELAY_SECONDS = float(os.environ.get("FNS_STARTUP_DELAY_SECONDS", "60"))

# Суточная докачка по реестру внутри процесса (см. _seconds_until_next_fns_window):
# выключается FNS_DAILY_RESYNC=0, если понадобится оставить только старт.
FNS_DAILY_RESYNC = os.environ.get("FNS_DAILY_RESYNC", "1") == "1"

# Дневной потолок живых запросов к api-fns.ru (П5''', этап 3). НЕ от нехватки
# квоты — ее достаточно (см. «Открытие, которое меняет бюджет» в CLAUDE.md),
# а от петли или бага: если что-то заставит процесс перезапускаться много раз
# подряд (сбойный деплой, крэш-луп), каждый старт без этой защиты бил бы по
# api-fns.ru заново. _fns_requests_today() считает по FnsSyncRun за текущие
# сутки UTC — строка в БД переживает сам рестарт, из-за которого счетчик
# понадобился. 200 — с большим запасом над одним нормальным стартом
# (FNS_STARTUP_SYNC_LIMIT=60 работ ~ до 180 запросов в худшем случае), но
# далеко от годовой квоты (3000/год на метод) — цель поймать петлю, а не
# экономить бюджет по запросу.
FNS_DAILY_REQUEST_CAP = 200

# Этап 13, П1 (COMPANY_FINANCE_BRIEF.md): повышенный потолок на время
# большого бэклога реестра. Кампания самопроверки ИНН подтверждает разом
# сотни новых записей — при обычных 200/день и лимите старта 60 догон
# растягивался бы на недели деплоев. Порог и повышенный потолок — оба с
# запасом над одним стартом (FNS_STARTUP_SYNC_LIMIT=60 работ ~ до 180
# запросов), но далеко от годовой квоты метода (3000/год) — цель ускорить
# добор, а не заново упереться в лимит.
FNS_BACKLOG_THRESHOLD_FOR_HIGH_CAP = 120
FNS_DAILY_REQUEST_CAP_HIGH = 400


_BANK_FINANCE_PATH = pathlib.Path(BASE_DIR) / "static" / "data" / "bank_finance.json"
_bank_finance_cache: dict = {}


def _bank_finance() -> dict:
    try:
        mtime = _BANK_FINANCE_PATH.stat().st_mtime
        if _bank_finance_cache.get("mtime") != mtime:
            _bank_finance_cache.update(mtime=mtime, data=json.loads(_BANK_FINANCE_PATH.read_text("utf-8")))
        return _bank_finance_cache.get("data") or {}
    except (OSError, ValueError):
        return {}


# ==================== ФНС: ЕГРЮЛ, БФО, история изменений ====================


def _entity_payload(entity: LegalEntity) -> dict:
    fields = (
        "id", "company_id", "legal_name", "short_name", "inn", "ogrn", "kpp",
        "legal_form", "status", "registration_date", "termination_date", "address",
        "region_code", "okved_code", "okved_name", "charter_capital_rub",
        "director_name", "director_title", "director_since", "source_provider",
        "source_updated_at", "fetched_at", "match_confidence", "manually_verified",
        "is_primary",
    )
    return {field: _plain(getattr(entity, field)) for field in fields}


def _report_payload(row: FinancialReport) -> dict:
    fields = (
        "year", "reporting_standard", "revenue_rub", "gross_profit_rub",
        "operating_profit_rub", "profit_before_tax_rub", "net_profit_rub",
        "assets_rub", "non_current_assets_rub", "current_assets_rub", "cash_rub",
        "receivables_rub", "inventory_rub", "equity_rub",
        "long_term_liabilities_rub", "short_term_liabilities_rub", "borrowings_rub",
        "payables_rub", "fetched_at",
    )
    payload = {field: _plain(getattr(row, field)) for field in fields}
    # Этап 8, П3-8: «не только эти показатели, а все из БФО» — raw_lines_json
    # уже несет полный набор строк с самого начала (sync_fns.py сохраняет
    # его как есть), просто на экран шла только выжимка из 15 полей выше.
    try:
        raw_lines = json.loads(row.raw_lines_json) if row.raw_lines_json else {}
    except (TypeError, ValueError):
        raw_lines = {}
    payload["full_lines"] = full_lines_payload(raw_lines)
    # Оборотный капитал, долговая нагрузка, рентабельность — считаются здесь,
    # на сервере, и едут готовыми числами с готовыми подписями (просьба Дани
    # 19 сентября 2026). Клиентских копий формул нет намеренно: две копии
    # правил в Python и JS уже разъезжались, см. «Слой фактов» в CLAUDE.md.
    payload["derived"] = company_finance.derive(payload)
    return payload


# ИНН 7702235133 — Банк России; в ЕГРЮЛ учредителем Сбербанка записан этот
# ИНН, а API-ФНС резолвит его в имя одного из расчетно-кассовых центров
# ЦБ (у РКЦ тот же ИНН, свой ОГРН): на сравнении Сбербанк «принадлежал»
# «РКЦ Г. КУРИЛЬСКА» (аудит перед бетой, 5 сентября 2026). Имя по ИНН
# надежнее имени филиала.
OWNER_NAME_BY_INN = {"7702235133": "Банк России"}


def _owner_payload(row: OwnershipStake) -> dict:
    return {
        "key": row.owner_key,
        "name": OWNER_NAME_BY_INN.get(str(row.inn or ""), row.owner_name),
        "type": row.owner_type,
        "inn": row.inn,
        "ogrn": row.ogrn,
        "country": row.country,
        "share_percent": _plain(row.share_percent),
        "nominal_value_rub": _plain(row.nominal_value_rub),
    }


def _is_ao_entity(entity: LegalEntity) -> bool:
    """ЕГРЮЛ хранит для акционерных обществ не текущих владельцев, а список
    УЧРЕДИТЕЛЕЙ на момент регистрации (реестр акционеров ведет не ФНС, а
    сам регистратор/депозитарий) — в отличие от ООО, где участники в ЕГРЮЛ
    действительно актуальны. Определяем форму по `legal_form`/`short_name`:
    один и тот же regex для обеих веток `_ownership_payload` (раньше
    работал только когда снапшотов не было вовсе — П1''''', этап 5)."""
    form = f"{entity.legal_form or ''} {entity.short_name or ''}".lower()
    return bool(re.search(r"(?:^|\s)(?:пао|ао|оао|зао)(?:\s|$)|акционерн", form))


def _dedupe_owners(owners: list[dict]) -> list[dict]:
    """Одно лицо в ЕГРЮЛ иногда встречается в снапшоте дважды — записью с
    ИНН и записью без (два разных блока исходной выписки слиты в один
    снапшот при разборе). Схлопываем по нормализованному имени, предпочитая
    запись с ИНН — иначе на экране одно и то же лицо дублируется (П1''''',
    этап 5: «Горбатовский Александр Иванович» ×2, «Зубов Дмитрий Львович» ×2)."""
    by_key: dict[str, dict] = {}
    order: list[str] = []
    for owner in owners:
        key = re.sub(r"\s+", " ", str(owner.get("name") or "").strip().lower())
        if key not in by_key:
            by_key[key] = owner
            order.append(key)
        elif owner.get("inn") and not by_key[key].get("inn"):
            by_key[key] = owner
    return [by_key[k] for k in order]


def _ownership_payload(db, entity: LegalEntity, paid: bool) -> dict:
    is_ao = _is_ao_entity(entity)
    snapshots = list(db.scalars(select(OwnershipSnapshot).where(
        OwnershipSnapshot.legal_entity_id == entity.id
    ).order_by(OwnershipSnapshot.snapshot_date, OwnershipSnapshot.id)).all())
    if not snapshots:
        return {
            "available": False,
            "current": [],
            "history": [],
            "has_more_history": False,
            "is_ao": is_ao,
            "notice": ("ЕГРЮЛ не раскрывает состав акционеров акционерного общества. "
                       "Если акционеры названы в сообщениях эмитента или источниках сделки, "
                       "они показываются в карточках соответствующих сделок.") if is_ao else
                      "Сведения об участниках в полученных данных ЕГРЮЛ не найдены.",
        }

    enriched = []
    for snap in snapshots:
        stakes = list(db.scalars(select(OwnershipStake).where(
            OwnershipStake.snapshot_id == snap.id
        ).order_by(OwnershipStake.share_percent.desc(), OwnershipStake.owner_name)).all())
        enriched.append((snap, stakes))
    current_pair = next(((snap, stakes) for snap, stakes in reversed(enriched)
                         if snap.source_kind == "current"), enriched[-1])
    current = _dedupe_owners([_owner_payload(x) for x in current_pair[1]])

    def comparable(pair):
        snap, stakes = pair
        if snap.is_complete:
            return True
        return len(stakes) == 1 and float(stakes[0].share_percent or 0) == 100.0

    history = []
    previous = None
    for pair in enriched:
        snap, stakes = pair
        if snap.id == current_pair[0].id and previous is None:
            previous = pair
            continue
        if previous is None:
            previous = pair
            if snap.source_kind != "current":
                for stake in stakes:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "recorded",
                        "owner": _owner_payload(stake), "before_share": None,
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
            continue
        before_snap, before_stakes = previous
        before = {x.owner_key: x for x in before_stakes}
        after = {x.owner_key: x for x in stakes}
        if comparable(previous) and comparable(pair):
            for key, stake in after.items():
                old = before.get(key)
                if old is None:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "joined",
                        "owner": _owner_payload(stake), "before_share": None,
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
                elif _plain(old.share_percent) != _plain(stake.share_percent):
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "share_changed",
                        "owner": _owner_payload(stake), "before_share": _plain(old.share_percent),
                        "after_share": _plain(stake.share_percent),
                        "source_text": snap.source_text, "is_complete": snap.is_complete,
                    })
            for key, stake in before.items():
                if key not in after:
                    history.append({
                        "date": _plain(snap.snapshot_date), "kind": "left",
                        "owner": _owner_payload(stake), "before_share": _plain(stake.share_percent),
                        "after_share": None, "source_text": snap.source_text,
                        "is_complete": snap.is_complete,
                    })
        elif snap.source_kind != "current":
            for stake in stakes:
                history.append({
                    "date": _plain(snap.snapshot_date), "kind": "recorded",
                    "owner": _owner_payload(stake), "before_share": None,
                    "after_share": _plain(stake.share_percent),
                    "source_text": snap.source_text, "is_complete": snap.is_complete,
                })
        previous = pair

    history.sort(key=lambda x: (x.get("date") or "", x.get("kind") or ""), reverse=True)
    shown = history if paid else history[:3]
    # П1''''', этап 5: для АО/ПАО этот снапшот — не «текущий состав», а
    # УЧРЕДИТЕЛИ на момент регистрации (см. _is_ao_entity) — ЕГРЮЛ реестр
    # акционеров вообще не ведет, и показывать список 2002 года под
    # заголовком «Текущий» — не старость данных, а неверная подпись.
    heading = "Учредители при регистрации" if is_ao else "Текущий состав"
    notice = ("Показываем изменения, которые зафиксированы в ЕГРЮЛ. "
              "Для неполных исторических записей не восстанавливаем состав участников догадками.")
    if is_ao:
        notice = ("ЕГРЮЛ не отслеживает акционеров акционерного общества — здесь список "
                  "учредителей на момент регистрации, а не текущие владельцы. Актуальные "
                  "собственники, если раскрыты, — в блоке «Собственники» на странице компании.")
    return {
        "available": bool(current or history),
        "current": current,
        "as_of": _plain(current_pair[0].snapshot_date),
        "heading": heading,
        "is_ao": is_ao,
        "history": shown,
        "has_more_history": len(history) > len(shown),
        "notice": notice,
    }


@router.get("/api/fns/status")
def fns_status(db=Depends(get_db)):
    """Счетчики витрины плюс то, что сделал ФОНОВЫЙ шаг: последние прогоны
    докачки (стартовые сканы) с их статистикой, сколько живых запросов
    потрачено за сутки и какой потолок действует. Без этого «строка реестра
    не доехала до прода» неотличима снаружи от «старт пропустил докачку из-за
    потолка» и от «запрос к ФНС упал» — 5 сентября 2026 подтвержденный ИНН
    «МорТехПрома» два деплоя подряд оставался несопоставленным, а причина
    была видна только в логе приложения на Timeweb (тот же класс, что
    «молчание неотличимо от „нечего делать"»)."""
    from pipeline.sync_fns import registry_backlog
    confirmed = db.query(LegalEntity).filter_by(match_status=LegalEntityMatchStatus.confirmed).count()
    synced = db.query(LegalEntity).filter(LegalEntity.fetched_at.is_not(None)).count()
    runs = db.scalars(select(FnsSyncRun).order_by(FnsSyncRun.started_at.desc()).limit(5)).all()
    backlog = registry_backlog(db)
    return {
        "configured": bool(os.environ.get("API_FNS_KEY")),
        "confirmed_entities": confirmed,
        "synced_entities": synced,
        "provider": "API-ФНС",
        "registry_backlog": backlog,
        "requests_today": _fns_requests_today(db),
        "daily_cap": (FNS_DAILY_REQUEST_CAP_HIGH if backlog > FNS_BACKLOG_THRESHOLD_FOR_HIGH_CAP
                      else FNS_DAILY_REQUEST_CAP),
        "startup_limit": FNS_STARTUP_SYNC_LIMIT,
        "last_runs": [{
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "mode": r.mode, "matched": r.matched, "errors": r.errors,
            "details": _json_or_empty(r.details_json),
        } for r in runs],
    }


def _json_or_empty(text):
    try:
        return json.loads(text or "{}")
    except (ValueError, TypeError):
        return {}


# ВИДЫ ЗАПИСЕЙ ЕГРЮЛ — для фильтра «покажи только лицензии» (просьба Ксюши,
# 19 сентября 2026). Собственного поля «тип» у записи нет: замер по проду
# показал, что `event_type` пуст у 330 записей из 334. Зато человеческая
# фраза внутри записи начинается с узнаваемого оборота, и вид выводится из
# нее. Порядок важен: первое совпадение и есть вид.
CHANGE_KINDS = (
    ("license", "Лицензии", ("лиценз",)),
    ("charter", "Учредительные документы", ("учредительн", "устав")),
    ("registry", "Сведения в ЕГРЮЛ", ("сведений о юридическом лице", "сведения, содержащиеся в едином")),
    ("tax", "Налоговый учет", ("налогов",)),
    ("funds", "Страховые взносы", ("страхователя", "пенсионн", "социальн", "страховани")),
)


def _change_kind(text) -> str:
    """Вид записи ЕГРЮЛ одним словом — или пусто, если фраза незнакомая.
    Незнакомая фраза НЕ приписывается к «прочему»: выдуманная категория в
    фильтре хуже ее отсутствия."""
    low = change_text(text).lower()
    if not low:
        return ""
    for key, _label, cues in CHANGE_KINDS:
        if any(cue in low for cue in cues):
            return key
    return ""


@router.get("/api/companies/{company_id}/fns")
def company_fns(company_id: str, as_of_year: int | None = None, user: User | None = Depends(_current_user), db=Depends(get_db)):
    profile = get_company_profile(company_id)
    entities = list(db.scalars(select(LegalEntity).where(
        LegalEntity.company_id == company_id,
        LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
    ).order_by(LegalEntity.is_primary.desc(), LegalEntity.id)).all())
    # Этап 6: `category` нужна фронтенду в ОБОИХ исходах — не только когда
    # юрлицо не сопоставлено вовсе (ветка ниже), но и когда LegalEntity УЖЕ
    # есть (часть банков когда-то была сопоставлена с ИНН до того, как для
    # них завели решение "bank" — коммерческие поля БФО у них пустые, а
    # категория раньше терялась). Без нее фронтенд не мог отличить банк от
    # обычной компании с пустой отчетностью и не мог решить, показывать ли
    # вместо ФНС-грида блок Банка России.
    registry_entry = fns_registry_by_company_id().get(company_id)
    registry_category = registry_entry["decision"] if registry_entry else None
    if not entities:
        # П5 (COMPANY_FINANCE_BRIEF.md): «нашли/не нашли» — не одно честное
        # состояние, а минимум шесть разных судеб (реестр pipeline/
        # fns_registry.py). Профиль без записи в реестре — тот же старый
        # «еще не сопоставлено», ничего не меняется для большинства базы.
        decision = registry_category
        category_reasons = {
            "bank": "Кредитная организация — бухгалтерскую отчетность в общем "
                    "порядке банки не сдают, только по отдельной форме перед "
                    "Банком России.",
            "foreign": "Иностранное юридическое лицо — российской отчетности "
                       "ЕГРЮЛ/ФНС для него не существует.",
            "state_org": "Государственный орган или государственная корпорация — "
                         "бухгалтерскую отчетность в общем порядке не сдает.",
            "person": "Сторона сделки — физическое лицо, а не юридическое.",
            "lot": "Сторона сделки — несколько юридических лиц под одним "
                   "названием, а не одна компания.",
        }
        # person/lot — блок не рендерится вовсе (родня правилу «вкладка без
        # данных не показывается», CLAUDE.md), не пустое состояние с текстом.
        hidden = decision in ("person", "lot")
        return {
            "available": False,
            "hidden": hidden,
            "company_id": company_id,
            "company_name": profile.get("name") if profile else None,
            "configured": bool(os.environ.get("API_FNS_KEY")),
            "category": decision,
            "reason": category_reasons.get(decision, "Юридическое лицо еще не сопоставлено с ЕГРЮЛ"),
        }
    paid = FNS_ALL_FREE or bool(user and user.tier == UserTier.paid)
    result = []
    for entity in entities:
        all_reports = list(db.scalars(select(FinancialReport).where(
            FinancialReport.legal_entity_id == entity.id
        ).order_by(FinancialReport.year.desc())).all())
        # Для карточки сделки показываем последний отчетный год ДО года сделки,
        # а не текущие показатели, появившиеся спустя несколько лет.
        stale_latest_year = None
        if as_of_year is not None:
            reports = [row for row in all_reports if row.year < as_of_year]
        else:
            # «Компания сегодня» не должна выглядеть моложе своей последней
            # отчетности на много лет: старше двух лет от текущего года —
            # честнее не показывать вовсе, чем выдавать за актуальное (владелец,
            # 18 августа — устаревшие 2020-2021 годы у банков/АФК «Система»
            # читались как обман). На историю сделки (as_of_year задан) это
            # правило не распространяется — там старый год того же периода,
            # что и сама сделка, и есть ровно то, что нужно показать.
            cutoff_year = datetime.now(timezone.utc).year - FNS_REPORT_MAX_AGE_YEARS
            reports = [row for row in all_reports if row.year >= cutoff_year]
            # Отличаем «отчетности нет вовсе» от «есть, но старше порога» —
            # это разные честные состояния и разный текст на экране.
            if not reports and all_reports:
                stale_latest_year = all_reports[0].year
        events = list(db.scalars(select(RegistryEvent).where(
            RegistryEvent.legal_entity_id == entity.id
        ).order_by(RegistryEvent.event_date.desc(), RegistryEvent.id.desc())).all())
        shown_reports = reports if paid else reports[:1]
        shown_events = events if paid else events[:3]
        result.append({
            "entity": _entity_payload(entity),
            "reports": [_report_payload(row) for row in shown_reports],
            "report_years": [row.year for row in reports],
            "stale_latest_year": stale_latest_year,
            # `change_text` чистит и УЖЕ СОХРАНЕННЫЕ записи: до 19 сентября 2026
            # в базу уезжал машинный слепок `{"СПВЗ": "…"}`, и читатель видел
            # его на странице компании. Перекачивать ЕГРЮЛ ради этого не нужно
            # — разбираем при отдаче; новые записи приходят уже чистыми.
            "events": [{
                "id": row.id,
                "date": _plain(row.event_date),
                # `type` остается как есть (человеческий текст или пусто), а
                # машинный ключ вида едет отдельным полем `kind`: подставить
                # его сюда значило бы вывести на экран слово «license» —
                # ровно тот дефект, ради которого все это и чинилось.
                "type": row.event_type,
                "text": change_text(row.text),
                "kind": _change_kind(row.text),
            } for row in shown_events],
            "ownership": _ownership_payload(db, entity, paid),
            "has_more_reports": len(reports) > len(shown_reports),
            "has_more_events": len(events) > len(shown_events),
        })
    return {
        "available": True,
        "company_id": company_id,
        "company_name": profile.get("name") if profile else None,
        "category": registry_category,
        "entities": result,
        "access": {"paid": paid, "full_history": paid, "downloads": paid},
        "as_of_year": as_of_year,
        "disclaimer": "Показатели относятся к указанному юридическому лицу по РСБУ и могут не отражать консолидированные показатели всей группы.",
    }


@router.get("/api/finance/screening")
def finance_screening(db=Depends(get_db)):
    """Массовый company_id -> {year, revenue_rub} для финансового фильтра
    ленты (Этап 16, П2). Один запрос вместо сотен: лента не может себе
    позволить дергать /api/companies/{id}/fns для каждой видимой карточки —
    это тот же список, что уже показывает досье компании (тот же порог
    свежести, FNS_REPORT_MAX_AGE_YEARS), просто агрегированный за раз."""
    cutoff_year = datetime.now(timezone.utc).year - FNS_REPORT_MAX_AGE_YEARS
    rows = db.execute(
        select(LegalEntity.company_id, FinancialReport.year, FinancialReport.revenue_rub)
        .join(FinancialReport, FinancialReport.legal_entity_id == LegalEntity.id)
        .where(
            LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
            LegalEntity.company_id.is_not(None),
            FinancialReport.revenue_rub.is_not(None),
            FinancialReport.year >= cutoff_year,
        )
    ).all()
    companies: dict[str, dict] = {}
    for company_id, year, revenue_rub in rows:
        cur = companies.get(company_id)
        if not cur or year > cur["year"]:
            companies[company_id] = {"year": year, "revenue_rub": float(revenue_rub)}
    return {"companies": companies}


@router.get("/api/analytics/multiples")
def analytics_multiples(db=Depends(get_db)):
    """Мультипликаторы сделок (EV/Выручка) — Этап 16, П1.

    Методика и ее обоснование — deal_multiples.py (модуль обвешан тестами
    на каждую ловушку, найденную пилотом Этапа 15). Здесь только сборка:
    свои сделки, свой реестр ФНС, свои профили компаний — по одному разу
    на запрос, без кэша (тот же стиль, что и у остальных эндпоинтов сайта:
    файлы маленькие, а мгновенная согласованность после деплоя важнее
    микросекунд ответа)."""
    deals = deal_catalog.load_deals()
    registry = fns_registry_by_company_id()
    # Лоты из нескольких юрлиц — одним чтением справочника, а не профиль за профилем.
    lot_ids = {cid for cid, row in load_company_catalog().items() if row.get("lot")}
    out = deal_multiples.compute_market_multiples(db, deals, registry, get_company_profile, lot_ids)
    out["show_medians"] = SHOW_MULTIPLE_MEDIANS
    return out


# Таблица «Мультипликаторы по отраслям» (19 октября 2026, deal_multiples.
# compute_sector_table): страница «Аналитика», блок на карточке сделки и
# ассистент читают ОДИН расчет. Кэш на минуту — ассистент и карточка зовут
# его чаще, чем меняется база; ключ — отпечаток файла базы.
_sector_cache: dict = {}
_SECTOR_TTL_SECONDS = 60


def _sector_multiples(db=None) -> dict:
    deals_path = pathlib.Path(BASE_DIR) / "static" / "data" / "deals_promoted.json"
    try:
        stamp = deals_path.stat().st_mtime
    except OSError:
        stamp = None
    hit = _sector_cache.get("value")
    if hit is not None and _sector_cache.get("stamp") == stamp \
            and time.monotonic() - _sector_cache.get("at", 0) < _SECTOR_TTL_SECONDS:
        return hit
    own = db is None
    session = get_session() if own else db
    try:
        value = deal_multiples.compute_sector_table(session, deal_catalog.load_deals(),
                                                    get_company_profile, _bank_finance())
    finally:
        if own:
            session.close()
    _sector_cache.update(value=value, stamp=stamp, at=time.monotonic())
    return value


@router.get("/api/analytics/sector-multiples")
def analytics_sector_multiples(db=Depends(get_db)):
    return _sector_multiples(db)


# Ассистент отвечает на «какой мультипликатор в ритейле» цифрой из той же таблицы.
assistant_retrieval.SECTOR_MULTIPLES_PROVIDER = _sector_multiples


def _confirmed_entity(db, company_id: str, entity_id: int | None = None) -> LegalEntity | None:
    query = select(LegalEntity).where(
        LegalEntity.company_id == company_id,
        LegalEntity.match_status == LegalEntityMatchStatus.confirmed,
    )
    if entity_id is not None:
        query = query.where(LegalEntity.id == entity_id)
    return db.scalar(query.order_by(LegalEntity.is_primary.desc(), LegalEntity.id))


@router.get("/api/companies/{company_id}/fns/extract")
def company_fns_extract(company_id: str, entity_id: int | None = None,
                        user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы скачать выписку"}, status_code=401)
    entity = _confirmed_entity(db, company_id, entity_id)
    if not entity or not (entity.inn or entity.ogrn):
        return JSONResponse({"error": "юридическое лицо не сопоставлено"}, status_code=404)
    try:
        with ApiFnsClient() as client:
            response = client.extract_pdf(entity.inn or entity.ogrn)
    except ApiFnsError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    filename = f"egrul-{entity.inn or entity.ogrn}.pdf"
    return StreamingResponse(iter([response.content]), media_type=response.headers.get("content-type", "application/pdf"),
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/api/companies/{company_id}/fns/bo/{year}")
def company_fns_bo_file(company_id: str, year: int, entity_id: int | None = None, xls: bool = False,
                        user: User | None = Depends(_current_user), db=Depends(get_db)):
    if not user:
        return JSONResponse({"error": "войдите, чтобы скачать отчетность"}, status_code=401)
    if not FNS_ALL_FREE and user.tier != UserTier.paid:
        return JSONResponse({"error": "скачивание полной отчетности доступно по подписке"}, status_code=403)
    entity = _confirmed_entity(db, company_id, entity_id)
    if not entity or not (entity.inn or entity.ogrn):
        return JSONResponse({"error": "юридическое лицо не сопоставлено"}, status_code=404)
    try:
        with ApiFnsClient() as client:
            response = client.bo_file(entity.inn or entity.ogrn, year, xls=xls)
    except ApiFnsError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    ext = "xlsx" if xls else "pdf"
    filename = f"bfo-{entity.inn or entity.ogrn}-{year}.{ext}"
    media = response.headers.get("content-type", "application/octet-stream")
    return StreamingResponse(iter([response.content]), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


