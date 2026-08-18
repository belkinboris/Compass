# -*- coding: utf-8 -*-
"""Клиент SOAP-сервиса Банка России CreditOrgInfo.asmx — отчётность банков.

Заведён 18 августа 2026 по прямой просьбе владельца: для банков ФНС/ГИР БО
не даёт коммерческую отчётность (см. урок в CLAUDE.md про Сбербанк/ВТБ), а
банки обязаны публично раскрывать отчётность именно перед ЦБ. Это бесплатный,
не требующий ключа веб-сервис (WSDL:
https://www.cbr.ru/CreditInfoWebServ/CreditOrgInfo.asmx?WSDL), но он НЕ
доступен из среды разработки Claude Code (исходящий доступ к cbr.ru здесь
закрыт политикой прокси) — весь протокол реверс-инжинирен вживую через
терминал владельца 18 августа 2026, методы ниже проверены реальными
запросами и реальными ответами для Сбербанка (рег. номер 1481).

ЧТО ПРОВЕРЕНО И РАБОТАЕТ ЧИСТО:
- `data102f_xml` (форма 102, прибыли и убытки) — ответ уже несёт человеко-
  читаемое название строки (`symname`) при каждом числе, ничего досчитывать
  не нужно. Сверено с независимой сводкой МСФО (Сбербанк, 995 млрд ₽ прибыли
  РСБУ за 7 месяцев 2026 против 1019 млрд ₽ МСФО за 6 месяцев — тот же
  порядок, ожидаемо чуть больше за более длинный период).

ЧТО РАБОТАЕТ, НО НЕ ДОСЧИТАНО:
- `data101fnew_xml` (форма 101, оборотная ведомость) отдаёт реальные остатки
  по счетам, но БЕЗ готового итога «Активы»/«Капитал» и без пометки
  актив/пассив у самого счёта — у счетов первого порядка (например, 301
  «Корреспондентские счета») внутри перемешаны счета ВТОРОГО порядка разных
  знаков (30102 А, 30109 П — см. действующее Положение Банка России от
  24.11.2022 N 809-П «О Плане счетов бухгалтерского учета для кредитных
  организаций», Раздел 3; заменило собой Положение 579-П от 27.02.2017 с
  1 января 2023 года — план счетов переиздаётся целиком, а не патчится,
  ссылаться нужно строго на действующую редакцию), а этот метод отдаёт уже
  свёрнутый до первого порядка остаток. Готовая, официально свёрнутая форма
  0409806 («Всего активов», «Всего источников собственных средств»)
  существует как отдельный метод (`GetF806Xml`/`GetF806Data`), но на
  практике отдаёт только шапку строк, ни одного числа — проверено на двух
  разных датах. Табличка `pipeline/cbr_account_types.py` — черновик
  классификации счетов первого порядка по действующему 809-П (разделы 2-4
  проверены построчно, раздел 1 и 5-9 — только по смыслу названия счёта),
  НЕ довалидирована на полном наборе счетов реального банка — используйте
  `pipeline/cbr_debug_balance_classification.py`, а не эти цифры напрямую.

Идентификатор банка — регистрационный/лицензионный номер (`CredorgNumber`,
маленькое целое, например 1481 у Сбербанка), а НЕ «IntCode» из
`BicToIntCode`/`RegNumToIntCode` (это большое число, переполняет поля
`s:int`, которые ждут `Data101FNewXML`/`Data102FXML`/`GetDatesForF10x`).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

BASE_URL = "https://www.cbr.ru/CreditInfoWebServ/CreditOrgInfo.asmx"
NS = "http://web.cbr.ru/"


class CbrClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class CbrConfig:
    base_url: str = BASE_URL
    timeout: float = 25.0


def _envelope(method: str, params: dict[str, Any]) -> str:
    body = "".join(f"<{k}>{v}</{k}>" for k, v in params.items() if v is not None)
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
        f'<soap:Body><{method} xmlns="{NS}">{body}</{method}></soap:Body>'
        '</soap:Envelope>'
    )


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1]


class CbrCreditOrgClient:
    """SOAP-клиент CreditOrgInfo.asmx. Сеть недоступна из среды разработки —
    методы ниже не выполнялись этим клиентом напрямую, только вручную через
    curl владельца; протокол (конверт, заголовки, имена методов и типы
    параметров) сверен с реальными успешными запросами день в день."""

    def __init__(self, config: CbrConfig | None = None, client: httpx.Client | None = None):
        self.config = config or CbrConfig()
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=self.config.timeout)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "CbrCreditOrgClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def _call(self, method: str, params: dict[str, Any]) -> ET.Element:
        body = _envelope(method, params)
        resp = self.client.post(
            self.config.base_url,
            content=body.encode("utf-8"),
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        )
        resp.raise_for_status()
        return ET.fromstring(resp.text)

    def data102f_xml(self, credorg_number: int, on_date: date) -> list[dict]:
        """Форма 102 (прибыли и убытки), нарастающим итогом с начала года.
        Возвращает список строк с уже человекочитаемым `symname`."""
        root = self._call("Data102FXML", {
            "CredorgNumber": credorg_number,
            "dt": on_date.isoformat(),
        })
        rows = []
        for el in root.iter():
            if _strip_ns(el.tag) == "F102":
                rows.append({_strip_ns(c.tag): c.text for c in el})
        return rows

    def data101fnew_xml(self, credorg_number: int, on_date: date) -> list[dict]:
        """Форма 101 (оборотная ведомость), свёрнутая до счетов первого
        порядка — БЕЗ пометки актив/пассив, см. предупреждение в докстроке
        модуля. Не используйте для прямого показа «Активы»/«Капитал» без
        `pipeline/cbr_account_types.py` и сверки на нескольких банках."""
        root = self._call("Data101FNewXML", {
            "CredorgNumber": credorg_number,
            "Dt": on_date.isoformat(),
        })
        rows = []
        for el in root.iter():
            if _strip_ns(el.tag) == "F101":
                rows.append({_strip_ns(c.tag): c.text for c in el})
        return rows

    def dates_for_f101(self, credorg_number: int) -> list[str]:
        root = self._call("GetDatesForF101", {"CredprgNumber": credorg_number})
        return [el.text for el in root.iter() if _strip_ns(el.tag) == "dateTime" and el.text]

    def dates_for_f102(self, credorg_number: int) -> list[str]:
        root = self._call("GetDatesForF102", {"CredprgNumber": credorg_number})
        return [el.text for el in root.iter() if _strip_ns(el.tag) == "dateTime" and el.text]


def parse_numsc(raw: str) -> str:
    """Нормализует номер счёта из ответа `Data101FNewXML`: большинство кодов
    целые («301»), но встречаются с хвостом «.0»/«.1»/«.2» («20.0», «32.1») —
    это укрупнённые итоги внутри счёта первого порядка (например, «32.1» —
    судя по величине и соседним счетам 322/324/325, часть группы 322-325
    «кредиты банкам»), а не отдельный официальный номер из Положения 579-П.
    Пока смысл хвоста «.N» не подтверждён по полному набору счетов — эта
    функция только чистит формат для сравнения, классификацию считает
    неизвестной (см. `pipeline/cbr_account_types.py`)."""
    return raw.strip()
