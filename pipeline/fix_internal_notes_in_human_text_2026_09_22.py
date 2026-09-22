# -*- coding: utf-8 -*-
"""Служебные пометки, вытекшие в текст, который читает человек.

СИМПТОМ. Владелец увидел в проекте поста на подтверждение:
«Покупатель: ВИМ Сбережения — Управляющая компания фонда, ранее называлась
«ВТБ Капитал Пенсионный резерв» (ПОДТВЕРЖДЕНО ЧТЕНИЕМ ИСТОЧНИКА mergers.ru)».
Последние четыре слова — наша внутренняя кухня, а не факт о компании.

ЧТО ЗДЕСЬ ПОЧИНЕНО. Шесть текстов, найденных сплошной проверкой всех 2027
описаний компаний и 12 137 прозаических полей карточек:
  • ВИМ Сбережения — «(подтверждено чтением источника mergers.ru)»;
  • WhoIsBlogger — «(по данным TAdviser)»;
  • Остин Рассел — «по данным Washington Post и «Коммерсанта»»;
  • ЗПИФ «СР» — «По данным одного источника (Ведомости)… второй источник
    это не подтверждает» (взвешивание источников — наша работа, не текст
    для читателя; спорное утверждение из профиля убрано целиком, потому
    что пустое поле честнее сомнительного);
  • «Связной» — «(покупатель не назван)» переписано прозой: факт верный,
    но в скобках он читается как служебная пометка;
  • карточка группы «Свой» — «на дату этого ПРОГОНА переименование ещё не
    состоялось»: слово «прогон» из нашего диалекта, и сама привязка к
    «сегодня» в хранимом тексте протухает. Названа дата.

Остальные шесть находок той же проверки прочитаны и оставлены как есть:
«Издание Rusbase», «медиахолдинг РБК», «журналистские расследования» у
телеграм-канала Baza — это факты о самих компаниях; перечисление активов и
площадь в скобках — не служебные пометки. Признак дефекта — повод прочитать,
а не основание стереть.

    python3 pipeline/fix_internal_notes_in_human_text_2026_09_22.py
    python3 pipeline/fix_internal_notes_in_human_text_2026_09_22.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
PENDING = ROOT / "static" / "data" / "pending.json"

sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
sys.path.insert(0, str(ROOT / "pipeline" / "publish"))

import proofread                                     # noqa: E402

# (id профиля, что было целиком, что станет)
PROFILES = [
    ("g50c327a7",
     "Управляющая компания фонда, ранее называлась «ВТБ Капитал Пенсионный резерв» "
     "(подтверждено чтением источника mergers.ru). Планирует включить квартал "
     "«Поклонка плейс» в закрытый паевой инвестиционный фонд для квалифицированных инвесторов.",
     "Управляющая компания фонда, ранее называлась «ВТБ Капитал Пенсионный резерв». "
     "Планирует включить квартал «Поклонка плейс» в закрытый паевой инвестиционный фонд "
     "для квалифицированных инвесторов."),
    ("g71a251f8",
     "Платформа аналитики и подбора блогеров для рекламных кампаний; юрлицо — "
     "ООО «Даблюайби» (по данным TAdviser). Основатель и гендиректор — Лев Грунин. "
     "В сентябре 2026 года вошла в состав Альфа-Банка, сохранив руководство и команду.",
     "Платформа аналитики и подбора блогеров для рекламных кампаний; юрлицо — "
     "ООО «Даблюайби». Основатель и гендиректор — Лев Грунин. В сентябре 2026 года "
     "вошла в состав Альфа-Банка, сохранив руководство и команду."),
    ("gf8ab8d88",
     "Американский миллиардер; в 2023 году, по данным Washington Post и «Коммерсанта», "
     "собирался выкупить у гонконгской Integrated Whale Media Investments контрольный "
     "пакет медиагруппы Forbes, но 21 ноября стороны расторгли сделку, хотя издатель "
     "Forbes Russia Магомед Мусаев называет себя истинным покупателем.",
     "Американский миллиардер; в 2023 году собирался выкупить у гонконгской "
     "Integrated Whale Media Investments контрольный пакет медиагруппы Forbes, "
     "но 21 ноября стороны расторгли сделку. Издатель Forbes Russia Магомед Мусаев "
     "называет истинным покупателем себя."),
    ("g05adfbe5",
     "Фонд под управлением «КСП Капитал»; в 2026 году купил у ВТБ торговый центр «Весна» "
     "на Новом Арбате. По данным одного источника (Ведомости), связан с совладельцем сети "
     "ЦОД Key Point Group — второй источник это не подтверждает.",
     "Фонд под управлением «КСП Капитал»; в 2026 году купил у ВТБ торговый центр «Весна» "
     "на Новом Арбате."),
    ("gc9b45ded",
     "Сеть салонов связи; в 2022 году «МегаФон» вышел из капитала, продав свои 25% "
     "(покупатель не назван).",
     "Сеть салонов связи; в 2022 году «МегаФон» вышел из капитала, продав свои 25%. "
     "Покупателя стороны не раскрывали."),
]

# Проза карточки правится ТОЛЬКО через proofread.py: её текст написан записью
# таблицы `FIXES`, и правка JSON напрямую объявила бы запись неприменённой
# (test_review_table_is_applied_and_not_pending). proofread кладёт в карточку
# отпечаток поглощённой записи и потому не ссорится с таблицей.
# (id карточки, поле, кусок «было», кусок «стало»)
FIELDS = [
    ("gmru-svoj-kredit-evropa-strah", "eco.context",
     "на дату этого прогона переименование ещё не состоялось",
     "переименование пока не состоялось"),
]


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    changed = 0

    for cid, was, now in PROFILES:
        prof = data["companies"].get(cid)
        if prof is None:
            print("  %s: профиля нет — пропущено" % cid)
            continue
        cur = str(prof.get("desc") or "")
        if cur == now:
            print("  %s: уже исправлено" % cid)
            continue
        if cur != was:
            print("  %s: описание изменилось с тех пор — НЕ трогаю" % cid)
            print("     сейчас: %s" % cur[:150])
            continue
        print("  %s (%s)" % (cid, prof.get("name")))
        print("     было:  %s" % was)
        print("     стало: %s" % now)
        if write:
            prof["desc"] = now
        changed += 1

    edits = []
    for did, field, was, now in FIELDS:
        card = next((x for x in data["deals"] if x["id"] == did), None)
        if card is None:
            print("  %s: карточки нет — пропущено" % did)
            continue
        cur = str(proofread.get_field(card, field) or "")
        if was not in cur:
            print("  %s %s: текст уже другой — НЕ трогаю" % (did, field))
            continue
        print("  %s %s (через proofread.py)" % (did, field))
        print("     было:  …%s…" % was)
        print("     стало: …%s…" % now)
        edits.append({"id": did, "field": field, "old": cur, "new": cur.replace(was, now)})
    if edits:
        ok = proofread.run(edits, data, write=write)
        changed += len(edits)
        if ok is False:
            print("  вычитка отклонила правку — смотреть причину выше")
            return 1

    # Пост владельцу показывают СНИМКОМ (`post_preview`), чтобы подписчики
    # получили ровно тот текст, что он одобрил. Значит, правка описания сама
    # по себе до канала не доедет — снимок надо пересобрать заново.
    import format_post                     # noqa: E402
    pend = json.loads(PENDING.read_text(encoding="utf-8")) if PENDING.exists() else {"cards": []}
    comps = dict(data["companies"])
    for card in pend.get("cards") or []:
        pv = str(card.get("post_preview") or "")
        if not pv or not proofread.INTERNAL_NOTE.search(pv):
            continue
        fresh = format_post.render(card, comps)
        if fresh == pv:
            print("  %s: предпросмотр пересобран, но текст тот же — смотреть руками" % card["id"])
            continue
        print("  %s: предпросмотр поста пересобран" % card["id"])
        for line in fresh.splitlines():
            if "Покупател" in line or "Продав" in line:
                print("     %s" % line)
        if write:
            card["post_preview"] = fresh
        changed += 1
    if write and pend.get("cards"):
        PENDING.write_text(json.dumps(pend, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("\nправок: %d" % changed)
    if not write:
        print("(сухой прогон; чтобы записать — --write)")
        return 0
    if changed:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("записано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
