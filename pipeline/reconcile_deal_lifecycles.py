# -*- coding: utf-8 -*-
"""Объединить новости об этапах одной сделки в одну карточку.

Карточка описывает жизненный цикл сделки, а не отдельную публикацию. Поэтому
переговоры, согласование, закрытие и срыв хранятся в ``events`` одной записи.
Старые адреса продолжают работать через ``merged`` и ``merged_deal_stages``.

В этот файл попадают только вручную проверенные случаи. Автоматический поиск
кандидатов выполняет ``pipeline/data_audit.py``; он ничего не склеивает сам.

Запуск:
    python3 pipeline/reconcile_deal_lifecycles.py          # сухой прогон
    python3 pipeline/reconcile_deal_lifecycles.py --write  # записать
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "static" / "data" / "deals_promoted.json"
DEALS_2026 = ROOT / "static" / "data" / "deals_2026.json"


def src(label: str, url: str) -> list[str]:
    return [label, url]


SPECS = [
    {
        "canonical": "g718e3d0e",
        "legacy": {"gea8ea954": "negotiations-2026-02-09"},
        "fields": {
            "date": "2026-05-28",
            "title": "Flowwow отказался от продажи российского бизнеса «Яндексу»",
            "buyer": "yandex",
            "target": "g578c62cd",
            "asset_id": None,
            "asset": "Российский бизнес Flowwow: маркетплейс и франшиза FMart",
            "seller": "Владельцы Flowwow",
            "seller_id": None,
            "status": "Не состоялась",
            "sum": "Не раскрыта",
            "ind": "E-commerce",
            "type": "M&A",
            "events": [
                {
                    "id": "negotiations-2026-02-09",
                    "kind": "negotiations",
                    "date": "2026-02-09",
                    "title": "Появилась информация о переговорах",
                    "historicalTitle": "«Яндекс» обсуждал покупку российского бизнеса Flowwow",
                    "note": "Источники сообщали о переговорах по российским активам Flowwow. Возможную стоимость оценивали в 5–8 млрд рублей; компании параметры сделки не подтверждали.",
                    "facts": [
                        ["Статус", "Переговоры"],
                        ["Потенциальный покупатель", "«Яндекс»"],
                        ["Предмет", "Российский маркетплейс Flowwow и франшиза FMart"],
                        ["Оценка", "5–8 млрд ₽ по сообщениям СМИ"],
                    ],
                    "sources": [
                        src("Forbes", "https://www.forbes.ru/svoi-biznes/555131-milliard-alyh-roz-flowwow-prodaet-rossijskij-biznes-andeksu"),
                        src("Коммерсантъ", "https://www.kommersant.ru/doc/8420688"),
                    ],
                },
                {
                    "id": "cancelled-2026-05-28",
                    "kind": "cancelled",
                    "date": "2026-05-28",
                    "title": "Переговоры прекращены",
                    "historicalTitle": "Flowwow отказался от продажи российского бизнеса «Яндексу»",
                    "note": "Стороны не договорились о финансовых условиях. Flowwow сообщил, что готов рассматривать предложения других инвесторов.",
                    "facts": [
                        ["Статус", "Сделка не состоялась"],
                        ["Причина", "Стороны не согласовали финансовые условия"],
                        ["Длительность переговоров", "Около девяти месяцев, по данным источников"],
                    ],
                    "sources": [
                        src("Коммерсантъ", "https://www.kommersant.ru/doc/8692653"),
                        src("Forbes", "https://www.forbes.ru/biznes/561870-kommersant-soobsil-ob-otkaze-flowwow-ot-prodazi-biznesa-andeksu"),
                    ],
                },
            ],
            "extra": "Переговоры касались российского бизнеса Flowwow. Стороны не согласовали финансовые условия, и в мае 2026 года Flowwow прекратил переговоры с «Яндексом».",
            "eco": {
                "sum": "Не раскрыта",
                "share": "Обсуждалась продажа российского бизнеса Flowwow: маркетплейса и франшизы FMart.",
                "val": "В феврале 2026 года источники оценивали возможную сделку в 5–8 млрд ₽; после прекращения переговоров участники рынка оценивали весь бизнес выше.",
                "target_fin": "По сообщениям СМИ, выручка ООО «Флаувау» за 2025 год составила 5,7 млрд ₽, чистая прибыль — 416 млн ₽. После подключения ФНС показатели должны выводиться из БФО, а не из текста карточки.",
                "fin": "Не раскрывалось",
                "rationale": "Для «Яндекса» покупка могла усилить направление доставки цветов и подарков. Сделка не состоялась из-за разногласий по финансовым условиям.",
                "context": "Flowwow продолжил поиск инвестора после прекращения переговоров.",
                "finadv": "Не раскрывался",
            },
            "law": {
                "struct": "Обсуждалась продажа российских активов Flowwow «Яндексу». Документы о сделке не были подписаны.",
                "appr": "До получения регуляторных согласований сделка не дошла.",
                "adv": [["Стороны", "Не раскрывались", "Консультанты в публичных источниках не названы"]],
                "terms": "Финансовые условия не согласованы.",
            },
        },
        "sources": [
            src("Коммерсантъ", "https://www.kommersant.ru/doc/8692653"),
            src("Forbes", "https://www.forbes.ru/biznes/561870-kommersant-soobsil-ob-otkaze-flowwow-ot-prodazi-biznesa-andeksu"),
            src("Forbes — о переговорах", "https://www.forbes.ru/svoi-biznes/555131-milliard-alyh-roz-flowwow-prodaet-rossijskij-biznes-andeksu"),
            src("Коммерсантъ — о параметрах переговоров", "https://www.kommersant.ru/doc/8420688"),
        ],
    },
    {
        "canonical": "gf12c6323",
        "legacy": {"gb92a97a4": "negotiations-2025-02-01"},
        "fields": {
            "date": "2026-07-01",
            "title": "Wildberries и Russ приобрели контрольную долю в «Еаптеке»",
            "buyer": "g549ab474",
            "target": "g5a939ce1",
            "seller": "Структуры Алексея Репика (ГК «Р-Фарм»)",
            "status": "Закрыта",
            "events": [
                {
                    "id": "negotiations-2025-02-01",
                    "kind": "negotiations",
                    "date": "2025-02-01",
                    "title": "Появилась информация о переговорах",
                    "historicalTitle": "Wildberries обсуждал покупку «Еаптеки» у «Сбера» и «Р-Фарм»",
                    "note": "На раннем этапе источники называли продавцами «Сбер» и «Р-Фарм». К закрытию структура «Р-Фарм» консолидировала актив и выступила продавцом.",
                    "facts": [["Статус", "Переговоры"], ["Потенциальный покупатель", "Wildberries и Russ"], ["Предмет", "Онлайн-аптека «Еаптека»"]],
                    "sources": [src("Фармацевтический вестник", "https://pharmvestnik.ru/content/news/Na-rynke-obsujdaut-potencialnuu-sdelku-o-pokupke-Wildberries-seti-Eapteka.html")],
                },
                {
                    "id": "closed-2026-07-01",
                    "kind": "closed",
                    "date": "2026-07-01",
                    "title": "Сделка завершена",
                    "historicalTitle": "Wildberries и Russ приобрели контрольную долю в «Еаптеке»",
                    "note": "ООО «РВБ» получило контрольную долю в «Еаптеке». Точный размер пакета и официальная цена не раскрывались.",
                    "facts": [["Статус", "Закрыта"], ["Покупатель", "ООО «РВБ» (Wildberries и Russ)"], ["Продавец", "Структуры Алексея Репика (ГК «Р-Фарм»)"], ["Предмет", "Контрольная доля в «Еаптеке»"]],
                    "sources": [src("Интерфакс", "https://www.interfax.ru/business/1099396"), src("Коммерсантъ", "https://www.kommersant.ru/doc/8780836")],
                },
            ],
        },
        "sources": [],
    },
    {
        "canonical": "g4577126f",
        "legacy": {"g327686f7": "negotiations-2023-03-01"},
        "fields": {
            "date": "2023-05-22",
            "title": "S8 Capital приобрёл российские активы Continental",
            "buyer": "gffdff138",
            "target": "gd8392d81",
            "seller": "Continental AG",
            "status": "Закрыта",
            "sum": "Не раскрыта",
            "events": [
                {
                    "id": "negotiations-2023-03-01",
                    "kind": "negotiations",
                    "date": "2023-03-01",
                    "title": "Continental объявила о продаже российских активов",
                    "historicalTitle": "Continental готовилась продать российский шинный бизнес S8 Capital",
                    "note": "Сделка включала шинный завод в Калуге и российскую сбытовую компанию.",
                    "facts": [["Статус", "Подготовка к продаже"], ["Покупатель", "S8 Capital"], ["Продавец", "Continental AG"]],
                    "sources": [src("Forbes", "https://www.forbes.ru/biznes/489684-nemeckij-proizvoditel-sin-continental-prodal-rossijskie-aktivy")],
                },
                {
                    "id": "closed-2023-05-22",
                    "kind": "closed",
                    "date": "2023-05-22",
                    "title": "Сделка завершена",
                    "historicalTitle": "S8 Capital приобрёл российские активы Continental",
                    "note": "S8 Capital получил шинный завод в Калуге и ООО «Континентал Тайрс Рус». Цена сделки официально не раскрывалась.",
                    "facts": [["Статус", "Закрыта"], ["Покупатель", "S8 Capital"], ["Продавец", "Continental AG"], ["Предмет", "Российский шинный бизнес Continental"]],
                    "sources": [src("Forbes", "https://www.forbes.ru/biznes/489684-nemeckij-proizvoditel-sin-continental-prodal-rossijskie-aktivy")],
                },
            ],
            "src": [src("Forbes", "https://www.forbes.ru/biznes/489684-nemeckij-proizvoditel-sin-continental-prodal-rossijskie-aktivy")],
        },
        "sources": [],
    },
    {
        "canonical": "g69a22dab",
        "legacy": {"g733847f4": "closed-2024-08-31"},
        "fields": {
            "date": "2024-08-31",
            "title": "Структура Умара Кремлёва приобрела «Рольф» у Росимущества",
            "buyer": "g6f5d7e99",
            "target": "gf0622a24",
            "seller": "Росимущество",
            "status": "Закрыта",
            "sum": "34,8 млрд ₽",
            "events": [
                {
                    "id": "closed-2024-08-31",
                    "kind": "closed",
                    "date": "2024-08-31",
                    "title": "Сделка завершена",
                    "historicalTitle": "Структура Умара Кремлёва приобрела «Рольф» у Росимущества",
                    "note": "Активы дилерского холдинга перешли структуре Умара Кремлёва. Согласно отчётности «Рольфа», цена составила 34,798 млрд рублей.",
                    "facts": [["Статус", "Закрыта"], ["Покупатель", "Структура Умара Кремлёва"], ["Продавец", "Росимущество"], ["Сумма", "34,798 млрд ₽"]],
                    "sources": [src("Интерфакс", "https://www.interfax.ru/business/1000901"), src("РБК", "https://www.rbc.ru/business/02/09/2024/66d5c7c39a7947774ba95af5")],
                }
            ],
        },
        "sources": [src("Интерфакс", "https://www.interfax.ru/business/1000901")],
    },
    {
        "canonical": "g2d90c4d5",
        "legacy": {"geb8eaeab": "announced-2025-01-28"},
        "fields": {
            "date": "2026-04-07",
            "title": "ING Group расторгла соглашение о продаже ИНГ Банка компании «Глобал Девелопмент»",
            "buyer": "gc905c016",
            "target": "gc0e9c501",
            "seller_id": "g84ef6ac1",
            "seller": "ING Group",
            "asset": "100% акций АО «ИНГ Банк (Евразия)»",
            "status": "Не состоялась",
            "sum": "Не раскрыта",
            "ind": "Банки",
            "type": "M&A",
            "events": [
                {
                    "id": "announced-2025-01-28",
                    "kind": "signed",
                    "date": "2025-01-28",
                    "title": "Стороны договорились о продаже банка",
                    "historicalTitle": "ING Group договорилась продать ИНГ Банк компании «Глобал Девелопмент»",
                    "note": "ING объявила о соглашении продать 100% АО «ИНГ Банк (Евразия)». Закрытие ожидалось в третьем квартале 2025 года после получения регуляторных разрешений.",
                    "facts": [
                        ["Статус", "Соглашение заключено"],
                        ["Покупатель", "АО «Глобал Девелопмент»"],
                        ["Продавец", "ING Group"],
                        ["Предмет", "100% АО «ИНГ Банк (Евразия)»"],
                    ],
                    "sources": [
                        src("ING Group", "https://www.ing.com/Newsroom/News/ING-announces-sale-of-its-Russian-business.htm"),
                        src("Право.ru", "https://pravo.ru/news/257140/"),
                    ],
                },
                {
                    "id": "cancelled-2026-04-07",
                    "kind": "cancelled",
                    "date": "2026-04-07",
                    "title": "Соглашение расторгнуто",
                    "historicalTitle": "ING Group отменила продажу российского банка",
                    "note": "ING расторгла соглашение: группа сочла получение покупателем необходимых разрешений маловероятным.",
                    "facts": [
                        ["Статус", "Сделка не состоялась"],
                        ["Причина", "Покупатель не получил необходимые разрешения"],
                    ],
                    "sources": [
                        src("Forbes", "https://www.forbes.ru/finansy/558708-niderlandskaa-ing-group-otmenila-prodazu-rossijskogo-banka"),
                        src("Интерфакс", "https://www.interfax.ru/business/1082459"),
                    ],
                },
            ],
            "extra": "Соглашение было заключено в январе 2025 года, но сделку не закрыли. В апреле 2026 года ING расторгла соглашение из-за отсутствия необходимых разрешений у покупателя.",
            "party_evidence": {
                "buyer": [{"value": "АО «Глобал Девелопмент»", "method": "manual_source_review", "url": "https://www.forbes.ru/finansy/558708-niderlandskaa-ing-group-otmenila-prodazu-rossijskogo-banka"}],
                "target": [{"value": "АО «ИНГ Банк (Евразия)»", "method": "manual_source_review", "url": "https://www.forbes.ru/finansy/558708-niderlandskaa-ing-group-otmenila-prodazu-rossijskogo-banka"}],
                "seller": [{"value": "ING Group", "method": "manual_source_review", "url": "https://www.forbes.ru/finansy/558708-niderlandskaa-ing-group-otmenila-prodazu-rossijskogo-banka"}],
            },
        },
        "sources": [
            src("Forbes", "https://www.forbes.ru/finansy/558708-niderlandskaa-ing-group-otmenila-prodazu-rossijskogo-banka"),
            src("Интерфакс", "https://www.interfax.ru/business/1082459"),
            src("Право.ru — об объявлении сделки", "https://pravo.ru/news/257140/"),
        ],
    },
    {
        "canonical": "g2f572b66",
        "legacy": {"gddbe3c97": "bidding-2023-01-10"},
        "fields": {
            "date": "2023-03-01",
            "title": "«Горные вершины» выиграли конкурс на приобретение курорта «Архыз»",
            "buyer": "geeb40253",
            "target": "g059b01f5",
            "seller": "АО «Кавказ.РФ»",
            "status": "Подписана",
            "sum": "24,2 млрд ₽",
            "events": [
                {
                    "id": "bidding-2023-01-10",
                    "kind": "negotiations",
                    "date": "2023-01-10",
                    "title": "Начался конкурс",
                    "historicalTitle": "Структура семьи Ткачёва подала заявку на приобретение курорта «Архыз»",
                    "note": "На конкурс выставили 100% акций управляющей компании курорта. Первоначальное предложение «Горных вершин» составляло 17 млрд рублей.",
                    "facts": [["Статус", "Конкурс"], ["Претендент", "ООО «Горные вершины»"], ["Продавец", "АО «Кавказ.РФ»"]],
                    "sources": [src("РБК Кавказ", "https://kavkaz.rbc.ru/kavkaz/01/03/2023/63fef0cb9a7947430bc61f73")],
                },
                {
                    "id": "winner-2023-03-01",
                    "kind": "signed",
                    "date": "2023-03-01",
                    "title": "Победитель конкурса определён",
                    "historicalTitle": "«Горные вершины» выиграли конкурс на приобретение курорта «Архыз»",
                    "note": "Компания предложила 24,2 млрд рублей. Сначала покупателю передаются 25% акций, оставшиеся 75% — по мере выполнения инвестиционных обязательств.",
                    "facts": [["Статус", "Победитель определён"], ["Покупатель", "ООО «Горные вершины»"], ["Продавец", "АО «Кавказ.РФ»"], ["Цена предложения", "24,2 млрд ₽"]],
                    "sources": [src("Интерфакс", "https://www.interfax.ru/business/889290"), src("Коммерсантъ", "https://www.kommersant.ru/doc/5843962")],
                },
            ],
            "src": [src("Интерфакс", "https://www.interfax.ru/business/889290"), src("Коммерсантъ", "https://www.kommersant.ru/doc/5843962"), src("РБК Кавказ", "https://kavkaz.rbc.ru/kavkaz/01/03/2023/63fef0cb9a7947430bc61f73")],
            "law": {
                "struct": "Продажа 100% акций АО «УК Архыз» поэтапно: 25% — после заключения договора, оставшиеся 75% — при выполнении инвестиционных обязательств.",
                "appr": "Публично не сообщалось",
                "adv": [["Стороны", "Не раскрывались", "Консультанты в публичных источниках не названы"]],
                "terms": "Инвестиционные обязательства включают развитие трасс, канатных дорог и гостиничной инфраструктуры.",
            },
        },
        "sources": [],
    },
]


def merge_sources(*groups: list[list[str]]) -> list[list[str]]:
    out: list[list[str]] = []
    seen: set[str] = set()
    for group in groups:
        for row in group or []:
            if not isinstance(row, list) or len(row) < 2 or not row[1]:
                continue
            if row[1] in seen:
                continue
            seen.add(row[1])
            out.append(row)
    return out


def apply_specs(payload: dict) -> list[str]:
    changes: list[str] = []
    deals = payload.setdefault("deals", [])
    by_id = {d.get("id"): d for d in deals}
    removed: set[str] = set()

    for spec in SPECS:
        canonical_id = spec["canonical"]
        canonical = by_id.get(canonical_id)
        if canonical is None:
            continue
        legacy_cards = [by_id[x] for x in spec["legacy"] if x in by_id]
        old = copy.deepcopy(canonical)
        for key, value in spec["fields"].items():
            if value is None:
                canonical.pop(key, None)
            else:
                canonical[key] = copy.deepcopy(value)
        canonical["src"] = merge_sources(
            spec.get("sources", []),
            canonical.get("src", []),
            *[d.get("src", []) for d in legacy_cards],
        )
        canonical["lifecycle_reviewed"] = True
        if canonical != old:
            changes.append(f"обновлена каноническая карточка {canonical_id}")

        for legacy_id, stage_id in spec["legacy"].items():
            if legacy_id in by_id:
                removed.add(legacy_id)
                changes.append(f"удалён дубль этапа {legacy_id}")
            payload.setdefault("merged", {})[legacy_id] = canonical_id
            payload.setdefault("merged_deal_stages", {})[legacy_id] = stage_id

    if removed:
        payload["deals"] = [d for d in deals if d.get("id") not in removed]
    return changes


def sync_2026(canonical_payload: dict, payload_2026: dict) -> list[str]:
    changes: list[str] = []
    canonical = {d["id"]: d for d in canonical_payload.get("deals", [])}
    ids = {spec["canonical"] for spec in SPECS}
    legacy = {x for spec in SPECS for x in spec["legacy"]}
    rows = []
    for deal in payload_2026.get("deals", []):
        if deal.get("id") in legacy:
            changes.append(f"из deals_2026 удалён дубль {deal['id']}")
            continue
        if deal.get("id") in ids and deal.get("id") in canonical:
            synced = copy.deepcopy(canonical[deal["id"]])
            rows.append(synced)
            if deal != synced:
                changes.append(f"в deals_2026 синхронизирована {deal['id']}")
        else:
            rows.append(deal)
    payload_2026["deals"] = rows
    return changes


def main(write: bool) -> None:
    promoted = json.loads(PROMOTED.read_text(encoding="utf-8"))
    changes = apply_specs(promoted)
    d2026 = json.loads(DEALS_2026.read_text(encoding="utf-8"))
    changes += sync_2026(promoted, d2026)
    if not changes:
        print("Изменений нет.")
        return
    print("\n".join(f"- {x}" for x in changes))
    if write:
        PROMOTED.write_text(json.dumps(promoted, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        DEALS_2026.write_text(json.dumps(d2026, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Записано.")
    else:
        print("Сухой прогон. Добавьте --write.")


if __name__ == "__main__":
    main("--write" in sys.argv)
