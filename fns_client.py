# -*- coding: utf-8 -*-
"""Клиент API-ФНС и нормализация ЕГРЮЛ/БФО.

Интеграция изолирована от остального приложения: после покупки доступа нужно
задать API_FNS_KEY и запустить pipeline/sync_fns.py. Исходные ответы сохраняются
в БД, а интерфейс читает только нормализованные поля.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx


class ApiFnsError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApiFnsConfig:
    key: str
    base_url: str = "https://api-fns.ru/api"
    timeout: float = 25.0

    @classmethod
    def from_env(cls) -> "ApiFnsConfig":
        return cls(
            key=os.environ.get("API_FNS_KEY", "").strip(),
            base_url=os.environ.get("API_FNS_BASE_URL", "https://api-fns.ru/api").rstrip("/"),
            timeout=float(os.environ.get("API_FNS_TIMEOUT", "25")),
        )


class ApiFnsClient:
    def __init__(self, config: ApiFnsConfig | None = None, client: httpx.Client | None = None):
        self.config = config or ApiFnsConfig.from_env()
        if not self.config.key:
            raise ApiFnsError("не задан API_FNS_KEY")
        self._owns_client = client is None
        self._min_interval = max(0.0, float(os.environ.get("API_FNS_MIN_INTERVAL", "0.15")))
        self._last_request_at = 0.0
        self.client = client or httpx.Client(
            timeout=self.config.timeout,
            transport=httpx.HTTPTransport(retries=2),
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
            # httpx.Client без заголовков шлёт User-Agent вида "python-httpx/0.2x" —
            # некоторые защитные прокси (Qrator/DDoS-Guard и подобные, обычные
            # для российского хостинга) блокируют явно нечеловеческий UA ещё до
            # того, как запрос вообще дойдёт до самого API-ФНС: с ключевого
            # прогона 18 августа 2026 все восемь запросов egr вернули 403
            # Forbidden сразу, без тела ошибки от самого api-fns.ru — похоже
            # именно на такую блокировку на уровне прокси/CDN, а не на отказ
            # тарифа (тариф на 3000 запросов в панели значился активным).
            headers={"User-Agent": "Mozilla/5.0 (compatible; KompasDeals/1.0; "
                                    "+https://projectcompass.ru)"},
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "ApiFnsClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def _request(self, method: str, params: dict[str, Any], *, expect_json: bool = True) -> Any:
        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        clean["key"] = self.config.key
        url = f"{self.config.base_url}/{method}"
        response = None
        for attempt in range(4):
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            try:
                response = self.client.get(url, params=clean)
                self._last_request_at = time.monotonic()
                if response.status_code == 429 or response.status_code in {502, 503, 504}:
                    if attempt < 3:
                        retry_after = response.headers.get("retry-after")
                        try:
                            delay = float(retry_after) if retry_after else 0.8 * (2 ** attempt)
                        except ValueError:
                            delay = 0.8 * (2 ** attempt)
                        time.sleep(min(max(delay, 0.2), 8.0))
                        continue
                response.raise_for_status()
                break
            except httpx.HTTPError as exc:
                if attempt < 3 and isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout)):
                    time.sleep(0.8 * (2 ** attempt))
                    continue
                raise ApiFnsError(f"API-ФНС {method}: {exc}") from exc
        if response is None:
            raise ApiFnsError(f"API-ФНС {method}: пустой ответ")
        if not expect_json:
            return response
        try:
            data = response.json()
        except ValueError as exc:
            raise ApiFnsError(f"API-ФНС {method}: ответ не является JSON") from exc
        if isinstance(data, dict):
            error = data.get("error") or data.get("Ошибка") or data.get("message")
            if error and not data.get("items"):
                raise ApiFnsError(f"API-ФНС {method}: {error}")
        return data

    def search(self, query: str, *, page: int = 1, active_only: bool = True) -> dict:
        filters = "active+onlyul" if active_only else "onlyul"
        return self._request("search", {"q": query, "page": page, "filter": filters})

    def egr(self, inn_or_ogrn: str) -> dict:
        return self._request("egr", {"req": inn_or_ogrn})

    def bo(self, inn_or_ogrn: str) -> dict:
        return self._request("bo", {"req": inn_or_ogrn})

    def changes(self, inn_or_ogrn: str, since: str | None = None) -> dict:
        return self._request("changes", {"req": inn_or_ogrn, "dat": since})

    def extract_pdf(self, inn_or_ogrn: str) -> httpx.Response:
        return self._request("vyp", {"req": inn_or_ogrn}, expect_json=False)

    def bo_file(self, inn_or_ogrn: str, year: int, *, xls: bool = False) -> httpx.Response:
        return self._request(
            "bo_file", {"req": inn_or_ogrn, "year": year, "xls": 1 if xls else None},
            expect_json=False,
        )


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _num(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _rub_from_thousands(value: Any) -> Decimal | None:
    n = _num(value)
    return n * 1000 if n is not None else None


def _walk_find(obj: Any, keys: tuple[str, ...]) -> Any:
    """Первое непустое значение по ключу, в том числе во вложенных объектах."""
    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] not in (None, "", [], {}):
                return obj[key]
        for value in obj.values():
            found = _walk_find(value, keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _walk_find(value, keys)
            if found not in (None, "", [], {}):
                return found
    return None


def _unwrap_items(data: Any) -> list[dict]:
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    return [x for x in items if isinstance(x, dict)] if isinstance(items, list) else []


def unwrap_legal_entity(data: dict) -> dict | None:
    for item in _unwrap_items(data):
        if isinstance(item.get("ЮЛ"), dict):
            return item["ЮЛ"]
    if isinstance(data.get("ЮЛ"), dict):
        return data["ЮЛ"]
    return None


def normalize_search_results(data: dict) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _unwrap_items(data):
        entity = item.get("ЮЛ") if isinstance(item.get("ЮЛ"), dict) else None
        if not entity:
            continue
        rows.append({
            "inn": entity.get("ИНН"),
            "ogrn": entity.get("ОГРН"),
            "short_name": entity.get("НаимСокрЮЛ"),
            "legal_name": entity.get("НаимПолнЮЛ") or entity.get("НаимСокрЮЛ"),
            "registration_date": parse_date(entity.get("ДатаОГРН") or entity.get("ДатаРег")),
            "status": entity.get("Статус"),
            "address": entity.get("АдресПолн") or _walk_find(entity.get("Адрес"), ("АдресПолн",)),
            "okved_name": entity.get("ОснВидДеят") if isinstance(entity.get("ОснВидДеят"), str) else _walk_find(entity.get("ОснВидДеят"), ("Текст",)),
            "raw": entity,
        })
    return rows


def normalize_egr(data: dict) -> dict[str, Any] | None:
    entity = unwrap_legal_entity(data)
    if not entity:
        return None
    activity = entity.get("ОснВидДеят") if isinstance(entity.get("ОснВидДеят"), dict) else {}
    address = entity.get("Адрес") if isinstance(entity.get("Адрес"), dict) else {}
    director_block = _walk_find(entity, ("СведДолжнФЛ", "Руководитель", "СвРукОрг"))
    director_name = _walk_find(director_block, ("ФИОПолн", "ФИО", "НаимПолн")) if director_block else None
    director_title = _walk_find(director_block, ("НаимДолжн", "Должность", "НаимДолжности")) if director_block else None
    director_since = parse_date(_walk_find(director_block, ("Дата", "ДатаНач", "ДатаНазначения"))) if director_block else None
    capital = _walk_find(entity, ("СумКап", "УстКап", "УставКапитал", "РазмерУстКап"))
    return {
        "inn": entity.get("ИНН"),
        "ogrn": entity.get("ОГРН"),
        "kpp": entity.get("КПП"),
        "short_name": entity.get("НаимСокрЮЛ"),
        "legal_name": entity.get("НаимПолнЮЛ") or entity.get("НаимСокрЮЛ"),
        "legal_form": _walk_find(entity, ("ПолнНаимОПФ", "НаимОПФ", "ОПФ")),
        "status": entity.get("Статус"),
        "registration_date": parse_date(entity.get("ДатаРег") or entity.get("ДатаОГРН")),
        "termination_date": parse_date(entity.get("ДатаПрекр")),
        "address": address.get("АдресПолн") or entity.get("АдресПолн") or _walk_find(address, ("АдресПолн",)),
        "region_code": address.get("КодРегион") or _walk_find(address, ("КодРегион",)),
        "okved_code": activity.get("Код") or _walk_find(activity, ("Код",)),
        "okved_name": activity.get("Текст") or _walk_find(activity, ("Текст",)),
        "charter_capital_rub": _num(capital),
        "director_name": director_name,
        "director_title": director_title,
        "director_since": director_since,
        "source_updated_at": parse_date(entity.get("СтатусДата") or _walk_find(entity, ("ДатаВып", "ДатаАкт"))),
        "raw": entity,
    }


BO_LINES = {
    "revenue_rub": "2110",
    "gross_profit_rub": "2100",
    "operating_profit_rub": "2200",
    "profit_before_tax_rub": "2300",
    "net_profit_rub": "2400",
    "assets_rub": "1600",
    "non_current_assets_rub": "1100",
    "current_assets_rub": "1200",
    "cash_rub": "1250",
    "receivables_rub": "1230",
    "inventory_rub": "1210",
    "equity_rub": "1300",
    "long_term_liabilities_rub": "1400",
    "short_term_liabilities_rub": "1500",
    "payables_rub": "1520",
}


def normalize_bo(data: dict, inn_or_ogrn: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    root: Any = data
    if inn_or_ogrn and isinstance(data.get(str(inn_or_ogrn)), dict):
        root = data[str(inn_or_ogrn)]
    elif len(data) == 1 and isinstance(next(iter(data.values())), dict):
        root = next(iter(data.values()))
    if not isinstance(root, dict):
        return []
    reports: list[dict[str, Any]] = []
    for year_text, lines in root.items():
        if not str(year_text).isdigit() or not isinstance(lines, dict):
            continue
        row: dict[str, Any] = {"year": int(year_text), "raw_lines": lines}
        for field, code in BO_LINES.items():
            row[field] = _rub_from_thousands(lines.get(code))
        lt_borrow = _rub_from_thousands(lines.get("1410")) or Decimal(0)
        st_borrow = _rub_from_thousands(lines.get("1510")) or Decimal(0)
        row["borrowings_rub"] = (lt_borrow + st_borrow) if (lines.get("1410") is not None or lines.get("1510") is not None) else None
        reports.append(row)
    return sorted(reports, key=lambda x: x["year"])


def normalize_changes(data: dict) -> list[dict[str, Any]]:
    entity = unwrap_legal_entity(data)
    if not entity:
        return []
    changes = entity.get("Изменения") or _walk_find(entity, ("Изменения",))
    rows: list[dict[str, Any]] = []
    if isinstance(changes, dict):
        iterable = changes.items()
    elif isinstance(changes, list):
        iterable = [(None, item) for item in changes]
    else:
        iterable = []
    for maybe_date, item in iterable:
        if not isinstance(item, dict):
            continue
        event_date = parse_date(maybe_date) or parse_date(item.get("Дата"))
        event_type = item.get("Тип") or item.get("Статус") or item.get("Вид")
        text = item.get("Текст") or item.get("Описание") or item.get("Статус")
        if not text:
            text = json.dumps(item, ensure_ascii=False, sort_keys=True)
        rows.append({"event_date": event_date, "event_type": event_type, "text": str(text), "raw": item})
    return rows

# ---------------------------------------------------------------- ownership ---

_OWNER_BLOCKS = (
    ("УчрЮЛ", "Российское юридическое лицо"),
    ("УчрФЛ", "Физическое лицо"),
    ("УчрИН", "Иностранное юридическое лицо"),
    ("УчрПИФ", "ПИФ"),
    ("УчрРФ", "Российская Федерация"),
    ("УчрСубРФ", "Субъект Российской Федерации"),
    ("УчрМО", "Муниципальное образование"),
)


def _as_owner_wrappers(value: Any) -> list[dict[str, Any]]:
    """Приводит разные формы блока участников API-ФНС к списку обёрток.

    В методе ``egr`` участники могут лежать в общем поле ``Учредители`` или
    отдельными массивами ``УчрЮЛ``/``УчрФЛ``. В ``changes`` тип участника и
    его доля нередко находятся прямо в записи конкретной даты. Поддерживаем
    все эти формы, чтобы после подключения ключа не зависеть от одного
    частного примера ответа.
    """
    if isinstance(value, list):
        rows: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            nested = _as_owner_wrappers(item)
            rows.extend(nested or [item])
        return rows
    if not isinstance(value, dict):
        return []

    owner_keys = [key for key, _ in _OWNER_BLOCKS if key in value]
    if owner_keys:
        rows: list[dict[str, Any]] = []
        meta_keys = (
            "Процент", "ДоляПроцент", "СуммаУК", "НоминСтоим", "Доля",
            "Дата", "ДатаНач", "ДатаОконч", "ДатаКон",
        )
        for key in owner_keys:
            blocks = value.get(key)
            blocks = blocks if isinstance(blocks, list) else [blocks]
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                # Иногда элемент массива уже является полной обёрткой.
                if any(owner_key in block for owner_key, _ in _OWNER_BLOCKS):
                    rows.extend(_as_owner_wrappers(block))
                    continue
                wrapper: dict[str, Any] = {key: block}
                for meta in meta_keys:
                    if meta in value:
                        wrapper[meta] = value[meta]
                    if meta in block:
                        wrapper[meta] = block[meta]
                rows.append(wrapper)
        return rows

    rows: list[dict[str, Any]] = []
    for nested in value.values():
        if isinstance(nested, (dict, list)):
            rows.extend(_as_owner_wrappers(nested))
    return rows


def _owner_name(block: dict[str, Any], owner_type: str) -> str | None:
    if owner_type == "Физическое лицо":
        return block.get("ФИОПолн") or block.get("ФИО")
    if owner_type == "Российская Федерация":
        return block.get("НаимПолн") or "Российская Федерация"
    if owner_type == "Субъект Российской Федерации":
        return block.get("НаимПолн") or block.get("НаимСубРФ")
    if owner_type == "Муниципальное образование":
        return block.get("НаимПолн") or block.get("НаимМО")
    return (
        block.get("НаимСокрЮЛ") or block.get("НаимПолнЮЛ") or
        block.get("НаимПолн") or block.get("Наименование") or
        block.get("НаимПИФ")
    )


def normalize_owners(value: Any) -> list[dict[str, Any]]:
    """Нормализует текущих или исторических участников из блока API-ФНС."""
    owners: list[dict[str, Any]] = []
    for wrapper in _as_owner_wrappers(value):
        owner_block = None
        owner_type = None
        for key, label in _OWNER_BLOCKS:
            if isinstance(wrapper.get(key), dict):
                owner_block = wrapper[key]
                owner_type = label
                break
        if owner_block is None:
            # Некоторые ответы отдают поля участника прямо в объекте.
            owner_block = wrapper
            owner_type = "Участник"
        name = _owner_name(owner_block, owner_type) or _walk_find(
            owner_block, ("ФИОПолн", "НаимСокрЮЛ", "НаимПолнЮЛ", "НаимПолн")
        )
        if not name:
            continue
        inn = owner_block.get("ИНН") or owner_block.get("ИННЮЛ") or owner_block.get("ИННФЛ")
        ogrn = owner_block.get("ОГРН") or owner_block.get("ОГРНЮЛ")
        share = _num(wrapper.get("Процент") or wrapper.get("ДоляПроцент") or _walk_find(wrapper.get("Доля"), ("Процент",)))
        nominal = _num(wrapper.get("СуммаУК") or wrapper.get("НоминСтоим") or _walk_find(wrapper.get("Доля"), ("НоминСтоим", "СуммаУК")))
        country = owner_block.get("ОКСМ") or owner_block.get("Страна")
        key = str(inn or ogrn or str(name).strip().lower())[:520]
        owners.append({
            "owner_key": key,
            "owner_name": str(name).strip(),
            "owner_type": owner_type,
            "inn": str(inn) if inn else None,
            "ogrn": str(ogrn) if ogrn else None,
            "country": str(country) if country else None,
            "share_percent": share,
            "nominal_value_rub": nominal,
            "start_date": parse_date(wrapper.get("Дата") or wrapper.get("ДатаНач")),
            "end_date": parse_date(wrapper.get("ДатаОконч") or wrapper.get("ДатаКон")),
            "raw": wrapper,
        })
    # В одной записи иногда дублируется участник в сокращённом и полном виде.
    dedup: dict[str, dict[str, Any]] = {}
    for row in owners:
        old = dedup.get(row["owner_key"])
        if old is None or (old.get("share_percent") is None and row.get("share_percent") is not None):
            dedup[row["owner_key"]] = row
    return list(dedup.values())


def normalize_ownership(data: dict, changes_data: dict | None = None) -> list[dict[str, Any]]:
    """Возвращает исторические срезы состава участников.

    Текущий состав из egr считается полным. Запись метода changes считается
    полной только когда API явно вернул массив участников; одиночный объект
    хранится как частичный исторический срез и в интерфейсе не выдаётся за
    исчерпывающий состав общества.
    """
    entity = unwrap_legal_entity(data)
    if not entity:
        return []
    current_raw = entity.get("Учредители")
    if current_raw is None and any(key in entity for key, _ in _OWNER_BLOCKS):
        current_raw = entity
    current_all = normalize_owners(current_raw)
    # В расширенных ответах рядом с действующими участниками могут приходить
    # бывшие с заполненной ДатаОконч. Они нужны для истории, но не должны
    # попадать в блок «Текущий состав».
    current = [owner for owner in current_all if owner.get("end_date") is None]
    current_date = parse_date(entity.get("СтатусДата") or _walk_find(entity, ("ДатаВып", "ДатаАкт")))
    if current_date is None:
        owner_dates = []
        for wrapper in _as_owner_wrappers(current_raw):
            dt = parse_date(wrapper.get("Дата"))
            if dt:
                owner_dates.append(dt)
        current_date = max(owner_dates) if owner_dates else date.today()
    rows: list[dict[str, Any]] = []
    if current:
        rows.append({
            "snapshot_date": current_date,
            "source_kind": "current",
            "is_complete": True,
            "source_text": "Текущий состав участников по ЕГРЮЛ",
            "owners": current,
            "raw": current_raw,
        })

    changes_entity = unwrap_legal_entity(changes_data or {}) if changes_data else None
    changes = (changes_entity or {}).get("Изменения") if changes_entity else None
    if isinstance(changes, dict):
        for date_text, item in changes.items():
            if not isinstance(item, dict):
                continue
            raw = item.get("Учредители")
            direct_owner = any(key in item for key, _ in _OWNER_BLOCKS)
            if raw is None and direct_owner:
                raw = item
            if raw is None:
                continue
            owners = normalize_owners(raw)
            if not owners:
                continue
            rows.append({
                "snapshot_date": parse_date(date_text) or parse_date(item.get("Дата")),
                "source_kind": "changes",
                # Запись конкретного изменения обычно содержит одного участника,
                # а не весь состав общества. Полной считаем только явный массив
                # в общем поле ``Учредители``.
                "is_complete": isinstance(item.get("Учредители"), list),
                "source_text": item.get("СПВЗ") or "Изменение сведений об участниках",
                "owners": owners,
                "raw": item,
            })
    rows.sort(key=lambda x: (x.get("snapshot_date") or date.min, x.get("source_kind") == "current"))
    return rows
