# -*- coding: utf-8 -*-
"""Клиент API-ФНС и нормализация ЕГРЮЛ/БФО.

Интеграция изолирована от остального приложения: после покупки доступа нужно
задать API_FNS_KEY и запустить pipeline/sync_fns.py. Исходные ответы сохраняются
в БД, а интерфейс читает только нормализованные поля.
"""
from __future__ import annotations

import json
import os
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
        self.client = client or httpx.Client(
            timeout=self.config.timeout,
            transport=httpx.HTTPTransport(retries=2),
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
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
        try:
            response = self.client.get(url, params=clean)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ApiFnsError(f"API-ФНС {method}: {exc}") from exc
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
