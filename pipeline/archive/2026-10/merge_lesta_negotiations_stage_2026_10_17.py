# -*- coding: utf-8 -*-
"""Две карточки об одной сделке «Леста Игры» — в одну.

НАЙДЕНО 17 октября 2026, прогон притока 08:20 МСК: приток принес
перепечатку о продаже «Лесты» (RB.ru), ворота отметили ее как кандидата
на дубль карточки `gd9ccfdd2` («Минфин рассчитывает продать издателя
«Мира танков» «Лесту» осенью», 03.09.2026, статус «Обсуждается») — но
настоящая сделка уже ЗАКРЫТА и описана ОТДЕЛЬНОЙ карточкой `gd09e0945`
(«Игровую студию «Леста» приобрела компания «Промышленные сооружения»»,
заведена 16.10.2026 через `promote.py`, без сверки с уже существующей
карточкой переговоров — та не попала в `near_duplicate()`, потому что
заголовки разошлись словами). Итог: база одновременно утверждала и
«Обсуждается» (без движения с 1 октября), и «Закрыта» — тот же класс
ошибки, что уже чинил `merge_aeroflot_aeromar_stages.py` 19 сентября.

ЧТО ДЕЛАЕТ СКРИПТ. `gd9ccfdd2` перестает быть отдельной сделкой и
становится ТРЕМЯ этапами переговоров внутри `gd09e0945` (ее собственные
три записи `events[]` — 03.09, 15.09, 01.10 — переносятся дословно, как
их уже читало и принимало чтение `gd9ccfdd2` 3 сентября). Старый адрес
продолжает работать через `merged`/`merged_deal_stages` (пост #79 от
3 сентября и закладки открывают `gd09e0945` на этапе 03.09.2026).

ДВА ПРОФИЛЯ ОДНОЙ КОМПАНИИ. `gd9ccfdd2.target` ссылался на `g483cfb4f`
(«Леста», match_keys: леста/леста геймс/wargaming, ИНН не подтвержден) —
отдельный от `geafdfc99` («Леста Игры», group=true, ИНН 7806038436
подтвержден, уже используется `gd09e0945`). `g483cfb4f` не используется
больше никем (проверено по `buyer`/`seller_id`/`target` всех карточек
`deals`/`pending`) — удаляется вместе со своими `match_keys`; в
`pipeline/fns_registry.py` записи для него нет (туда ничего не переносить).

НОВЫЕ ФАКТЫ `gd9ccfdd2`, КОТОРЫХ НЕ БЫЛО В `gd09e0945` (переносятся
дословно текстом, который уже прошел чтение и дочитывание 3 сентября —
это перенос подтвержденного факта, не новое чтение статьи):
  - `eco.val` (была «—»): оценка 135 млрд ₽ из документов в суде;
  - `eco.target_fin`: долги по исполнительным производствам ФССП
    (11,4 млрд ₽ и 239,7 млн ₽) — ДОПОЛНЯЮТ, а не заменяют, уже стоящие
    в `gd09e0945` цифры выручки/прибыли за 2025 год;
  - `eco.context`: кандидаты на покупку до «Промышленных сооружений»
    (структура Никиты Мазепина, «Дхамма» с группой Okkam) — дописано
    явно как история ДО итога, никакая из оценок претендентов не выдается
    за условия состоявшейся сделки.
Источники `gd9ccfdd2` (3 Коммерсанта, Frank Media/303016, 2 RB.ru,
Forbes через 3DNews) переносятся в `src` карточки `gd09e0945`, кроме уже
там стоящих.

Запуск:
    python3 pipeline/merge_lesta_negotiations_stage_2026_10_17.py          # сухой прогон
    python3 pipeline/merge_lesta_negotiations_stage_2026_10_17.py --write  # записать
Скрипт идемпотентен: повторный запуск ничего не меняет.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

STAGE_ID = "gd9ccfdd2"
CANONICAL_ID = "gd09e0945"
LEGACY_COMPANY_ID = "g483cfb4f"
CANONICAL_COMPANY_ID = "geafdfc99"
FIRST_STAGE_EVENT_ID = "negotiations-2026-09-03"

NEW_EVENTS = [
    {
        "id": "negotiations-2026-09-03",
        "kind": "negotiations",
        "date": "2026-09-03",
        "title": "Переговоры",
        "note": "Активы «Лесты», перешедшие государству, планируется продать частному инвестору, "
                "сообщил замглавы Минфина Алексей Моисеев. Он ожидает, что сделка состоится в "
                "ближайшие два месяца.",
        "source": ["Коммерсантъ", "https://www.kommersant.ru/doc/8925020"],
    },
    {
        "id": "negotiations-2026-09-15",
        "kind": "negotiations",
        "date": "2026-09-15",
        "title": "Мазепин — на финишной прямой",
        "note": "По данным Forbes, сделка о продаже «Лесты» Никите Мазепину находится на финишной "
                "прямой — документы уже подготовлены, осталось согласовать цену. Источник Forbes "
                "оценил справедливую стоимость компании в 30–35 млрд ₽ — ниже первоначальной "
                "оценки в 50 млрд ₽.",
        "source": ["Forbes (через 3DNews)",
                   "https://3dnews.ru/1148534/vot-eto-povorot-na-pokupku-izdatelya-mira-tankov-i-"
                   "mira-korabley-natselilsya-bivshiy-rossiyskiy-gonshchik-formuli1"],
    },
    {
        "id": "negotiations-2026-10-01",
        "kind": "negotiations",
        "date": "2026-10-01",
        "title": "Назван потенциальный инвестор",
        "note": "«Дхамма» предложила себя инвестором приватизации «Лесты» (с привлечением группы "
                "Okkam), источник оценил стоимость в 50 млрд ₽ — но источник в ведомстве эту "
                "информацию опроверг. На актив претендуют несколько инвесторов, включая структуру "
                "Никиты Мазепина.",
        "source": ["RB.ru",
                   "https://rb.ru/news/ao-dhamma-zainteresovalos-pokupkoj-razrabotchika-igry-mir-"
                   "tankov-u-gosudarstva-aktiv-ocenili-v-50-mlrd-rublej/"],
    },
]

NEW_ECO_VAL = ("Активы компании в документах, направленных в суд, оценены в 135 млрд ₽ — очень "
               "крупная сумма для игровой индустрии.")

OLD_TARGET_FIN = (
    "Основная выручка и прибыль группы — у «Леста Геймс Эдженси»: 29 млрд руб. и 10,1 млрд руб. "
    "за 2025 год. У самой «Лесты» выручка 5,7 млрд руб. при прибыли всего 14,7 млн руб., у "
    "московского юрлица — 227,3 млн руб. выручки и 8,9 млн руб. прибыли."
)
NEW_TARGET_FIN = OLD_TARGET_FIN + (
    " Отдельно, по данным ФССП, у «Леста Геймс Эдженси» в исполнительном производстве от "
    "5 марта 2026 года висел долг 11,4 млрд ₽ в пользу бюджета РФ, у «Лесты» — еще 239,7 млн ₽."
)

OLD_CONTEXT = (
    "Раньше «Леста» входила в белорусскую Wargaming — компанию Виктора Кислого и Малика "
    "Хатажаева. После начала военных действий на Украине Wargaming свернула российский бизнес, "
    "а 99% студии отошло Хатажаеву. В 2025 году суд по иску Генпрокуратуры сначала арестовал "
    "ключевые юрлица, а затем передал их государству — Хатажаева и Кислого признали причастными "
    "к экстремистской деятельности и запретили им вести дела в России."
)
NEW_CONTEXT = OLD_CONTEXT + (
    " Минфин рассчитывал продать актив частному инвестору осенью 2025 года; среди обсуждавшихся "
    "тогда претендентов были структура экс-гонщика «Формулы-1» Никиты Мазепина и компания "
    "«Дхамма» (предлагала привлечь к развитию группу Okkam) — их оценки актива (30–50 млрд ₽) "
    "разошлись с итогом сделки."
)


def migrate(payload: dict) -> list[str]:
    changes: list[str] = []
    deals = payload.setdefault("deals", [])
    by_id = {d.get("id"): d for d in deals}

    canonical = by_id.get(CANONICAL_ID)
    assert canonical is not None, "карточка %s пропала из базы" % CANONICAL_ID
    stage = by_id.get(STAGE_ID)

    if stage is not None:
        assert stage.get("status") != "Закрыта", stage.get("status")
        assert canonical.get("status") == "Закрыта", canonical.get("status")
        assert stage.get("target") == LEGACY_COMPANY_ID, stage.get("target")
        assert canonical.get("target") == CANONICAL_COMPANY_ID, canonical.get("target")

        have = {tuple(s) for s in (canonical.get("src") or []) if isinstance(s, list)}
        for src in stage.get("src") or []:
            if isinstance(src, list) and tuple(src) not in have:
                canonical.setdefault("src", []).append(src)
                have.add(tuple(src))
                changes.append("источник перенесен: %s" % src[0])

        payload["deals"] = [d for d in deals if d.get("id") != STAGE_ID]
        changes.append("карточка %s больше не отдельная сделка" % STAGE_ID)

    events = canonical.setdefault("events", [])
    for ev in NEW_EVENTS:
        if not any(e.get("id") == ev["id"] for e in events):
            events.append(dict(ev))
            changes.append("добавлено событие «%s»" % ev["id"])
    events.sort(key=lambda e: e.get("date") or "")

    eco = canonical.setdefault("eco", {})
    if eco.get("val") == "—":
        eco["val"] = NEW_ECO_VAL
        changes.append("eco.val заполнено оценкой из суда")
    elif eco.get("val") != NEW_ECO_VAL:
        raise SystemExit("eco.val не в ожидаемом состоянии: %r" % eco.get("val"))

    if eco.get("target_fin") == OLD_TARGET_FIN:
        eco["target_fin"] = NEW_TARGET_FIN
        changes.append("eco.target_fin дополнено долгами по ФССП")
    elif eco.get("target_fin") != NEW_TARGET_FIN:
        raise SystemExit("eco.target_fin не в ожидаемом состоянии: %r" % eco.get("target_fin"))

    if eco.get("context") == OLD_CONTEXT:
        eco["context"] = NEW_CONTEXT
        changes.append("eco.context дополнено историей претендентов")
    elif eco.get("context") != NEW_CONTEXT:
        raise SystemExit("eco.context не в ожидаемом состоянии: %r" % eco.get("context"))

    merged = payload.setdefault("merged", {})
    if merged.get(STAGE_ID) != CANONICAL_ID:
        merged[STAGE_ID] = CANONICAL_ID
        changes.append("старый адрес %s открывает %s" % (STAGE_ID, CANONICAL_ID))

    stages = payload.setdefault("merged_deal_stages", {})
    if stages.get(STAGE_ID) != FIRST_STAGE_EVENT_ID:
        stages[STAGE_ID] = FIRST_STAGE_EVENT_ID
        changes.append("старый адрес привязан к этапу %s" % FIRST_STAGE_EVENT_ID)

    companies = payload.setdefault("companies", {})
    if LEGACY_COMPANY_ID in companies:
        del companies[LEGACY_COMPANY_ID]
        changes.append("удален технический профиль компании %s" % LEGACY_COMPANY_ID)

    match_keys = payload.setdefault("match_keys", {})
    if LEGACY_COMPANY_ID in match_keys:
        del match_keys[LEGACY_COMPANY_ID]
        changes.append("удалены псевдонимы технического профиля %s" % LEGACY_COMPANY_ID)

    merged_companies = payload.setdefault("merged_companies", {})
    if merged_companies.get(LEGACY_COMPANY_ID) != CANONICAL_COMPANY_ID:
        merged_companies[LEGACY_COMPANY_ID] = CANONICAL_COMPANY_ID
        changes.append("добавлен редирект компании %s → %s" % (LEGACY_COMPANY_ID, CANONICAL_COMPANY_ID))

    return changes


def main(write: bool) -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    changes = migrate(payload)
    if not changes:
        print("Изменений нет: история уже объединена.")
        return

    print("\n".join("- %s" % item for item in changes))
    if write:
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        changes = migrate(payload)
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Записано:", DATA)
    else:
        print("Сухой прогон. Для записи добавьте --write.")


if __name__ == "__main__":
    main("--write" in sys.argv)
