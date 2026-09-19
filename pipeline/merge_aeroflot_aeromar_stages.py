# -*- coding: utf-8 -*-
"""Две карточки об одной сделке «Аэрофлот» / «Аэромар» — в одну.

НАЙДЕНО 19 сентября 2026 сплошной проверкой базы на противоречия: пары
карточек с ОДНИМ покупателем и ОДНИМ предметом, где одна «Закрыта», а
другая нет. Таких пар в базе три, и две из них — настоящие разные сделки
(«Башнефть»: часть блокирующего пакета и остаток; ГК «Дело»: опцион 2022
года и «русская рулетка» 2026-го). Третья — ошибка:

  * `g42e42759` «Аэрофлот приобретает долю в АО «Аэромар»» — 16.03.2024,
    статус «Обсуждается», и в «Контексте» прямым текстом стоит фраза
    «Подтверждений тому, что сделка после этого закрыта, в открытых
    источниках нет.»
  * `g2c27516d` «Аэрофлот» выкупил долю структуры Lufthansa…» — 01.09.2026,
    статус «Закрыта», четыре источника, событие `closed`, пост уже вышел.

То есть база одновременно утверждала, что сделка закрыта и что
подтверждений закрытия нет. Читатель, открывший обе карточки, видит это
сразу — и справедливо перестаёт верить обеим. При этом карточки не были
«случайно задвоены»: `pipeline/fix_aeromar_industry_catering.py` прямо
называет их «двумя карточками одной истории», то есть о двойственности
знали и оставили как есть.

ЧТО ДЕЛАЕТ СКРИПТ. Ровно то, что уже делает `merge_deal_histories.py` для
Ситибанка: ранняя карточка перестаёт быть отдельной сделкой и становится
ЭТАПОМ поздней — согласованием. Старый адрес продолжает работать через
`merged`/`merged_deal_stages`, поэтому ссылка из вышедшего поста и из
закладок открывает оставшуюся карточку.

ОТКУДА ВЗЯТ ТЕКСТ СОБЫТИЯ. Дословно из самой карточки `g42e42759` — её
поля уже прошли чтение источника (`reviewed`), дочитывание и языковую
вычитку. Ничего нового не утверждается: предложения переносятся как есть,
лишнее вырезается (это разрешено правилом переноса факта). НЕ переносится
одна фраза — «Подтверждений тому, что сделка после этого закрыта… нет»:
она и была неправдой, ради которой всё затевалось.

ИМЯ ПРОДАВЦА НЕ ТРОГАЕМ. В базе оно записано тремя способами: «Trüffel 2
GmbH» (поля `seller` и `extra` ранней карточки), «Truffel 2 GmbH» (её же
«Контекст») и «Truffle 2 GmbH» (поздняя карточка, подтверждено чтением
«Интерфакса» — `party_evidence`). Какое верно, по нашим источникам не
установить, поэтому выбранное чтением написание остаётся, а из
переносимого текста упоминание вырезано — иначе на одной карточке стояли
бы два разных написания одного юрлица. Установить правильное имя — задача
чтения первоисточника (распоряжение на publication.pravo.gov.ru), не этого
скрипта.

Запуск:
    python3 pipeline/merge_aeroflot_aeromar_stages.py          # сухой прогон
    python3 pipeline/merge_aeroflot_aeromar_stages.py --write  # записать
Скрипт идемпотентен: повторный запуск ничего не меняет.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"

STAGE_ID = "g42e42759"          # ранняя карточка — станет этапом
CANONICAL_ID = "g2c27516d"      # оставшаяся карточка сделки
EVENT_ID = "approval-2024-03-16"

# Дословно из полей ранней карточки (`law.appr` и `eco.context`), с
# вырезанным упоминанием продавца — см. шапку.
EVENT_NOTE = (
    "Сделка одобрена Распоряжением Президента РФ № 74-рп от 16 марта. "
    "16 марта 2026 года президент РФ Владимир Путин издал второе распоряжение "
    "о той же сделке, разрешив «Аэрофлоту» выкупить те же 4900 акций у структуры "
    "Lufthansa (Германия). Это ровно через два года после первого распоряжения "
    "№ 74-рп от 16.03.2024."
)

# «16 марта» без года на оставшейся карточке — дата, по которой нельзя
# сказать, о каком из двух распоряжений речь. Год берётся из «Контекста»
# ранней карточки, где он назван прямо и подтверждён ссылкой на
# publication.pravo.gov.ru.
OLD_APPR = ("16 марта президент РФ Владимир Путин подписал распоряжение о сделке в связи "
            "с недружественными действиями некоторых иностранных государств и "
            "международных организаций.")
NEW_APPR = ("16 марта 2026 года президент РФ Владимир Путин подписал распоряжение о сделке "
            "в связи с недружественными действиями некоторых иностранных государств и "
            "международных организаций. Это было второе распоряжение о той же сделке: "
            "первое, № 74-рп, вышло 16 марта 2024 года.")


def migrate(payload: dict) -> list[str]:
    changes: list[str] = []
    deals = payload.setdefault("deals", [])
    by_id = {d.get("id"): d for d in deals}

    canonical = by_id.get(CANONICAL_ID)
    assert canonical is not None, "оставшаяся карточка %s пропала из базы" % CANONICAL_ID
    stage = by_id.get(STAGE_ID)

    if stage is not None:
        # Проверяем, что сливаем именно то, что разбирали: тот же покупатель,
        # тот же предмет, и ранняя карточка действительно не закрыта.
        assert stage.get("buyer") == canonical.get("buyer"), "покупатели разошлись"
        assert stage.get("target") == canonical.get("target"), "предметы разошлись"
        assert stage.get("status") != "Закрыта", stage.get("status")
        assert canonical.get("status") == "Закрыта", canonical.get("status")

        # Источники ранней карточки не теряются.
        have = {tuple(s) for s in (canonical.get("src") or []) if isinstance(s, list)}
        for src in stage.get("src") or []:
            if isinstance(src, list) and tuple(src) not in have:
                canonical.setdefault("src", []).append(src)
                have.add(tuple(src))
                changes.append("источник перенесён: %s" % src[0])

        payload["deals"] = [d for d in deals if d.get("id") != STAGE_ID]
        changes.append("карточка %s больше не отдельная сделка" % STAGE_ID)

    events = canonical.setdefault("events", [])
    if not any(e.get("id") == EVENT_ID for e in events):
        events.append({
            "id": EVENT_ID,
            "kind": "approval",
            "date": "2024-03-16",
            "title": "Сделку разрешило распоряжение президента",
            "note": EVENT_NOTE,
            "source": ["Официальный интернет-портал правовой информации",
                       "http://publication.pravo.gov.ru/document/0001202603160011"],
        })
        events.sort(key=lambda e: e.get("date") or "")
        changes.append("добавлено событие «%s»" % EVENT_ID)

    appr = (canonical.get("law") or {}).get("appr")
    if appr == OLD_APPR:
        canonical["law"]["appr"] = NEW_APPR
        changes.append("в «Согласованиях» назван год распоряжения")
    elif appr != NEW_APPR:
        raise SystemExit("law.appr не в ожидаемом состоянии: %r" % appr)

    merged = payload.setdefault("merged", {})
    if merged.get(STAGE_ID) != CANONICAL_ID:
        merged[STAGE_ID] = CANONICAL_ID
        changes.append("старый адрес %s открывает %s" % (STAGE_ID, CANONICAL_ID))

    stages = payload.setdefault("merged_deal_stages", {})
    if stages.get(STAGE_ID) != EVENT_ID:
        stages[STAGE_ID] = EVENT_ID
        changes.append("старый адрес привязан к этапу %s" % EVENT_ID)

    return changes


def main(write: bool) -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    changes = migrate(payload)
    if not changes:
        print("Изменений нет — всё уже слито.")
        return
    for line in changes:
        print(" •", line)
    if not write:
        print("\nСухой прогон. Записать: --write")
        return
    # Без завершающего перевода строки: именно так лежит файл сейчас, и
    # лишний байт в конце дал бы изменение на строке, к делу не относящейся.
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nЗаписано в %s" % DATA)


if __name__ == "__main__":
    main("--write" in sys.argv)
