# -*- coding: utf-8 -*-
"""Очередь аудита: STATUS_MISMATCH + DATE_MISMATCH — первая партия, разобрана
5 параллельными читателями (91 находка: 36 STATUS_MISMATCH + 55
DATE_MISMATCH, консолидировано до 88 уникальных ключей — 3 дубля внутри
партий). Каждое решение читатель принимал либо по самой карточке (events[],
law.*, eco.*, facts.*), либо сверял с первоисточником через WebFetch, когда
поле само по себе не хватало (дата публикации статьи вместо даты события —
самый частый источник дефекта в этой партии).

Итог разбора: 58 fix (уникальных ключей), 21 not_wrong (находка не
подтвердилась при чтении — состояние карточки уже верное, просто цитата
находки описывала более раннюю стадию), 9 defer (нужно решение владельца:
многолетние инвестпрограммы без разовой даты закрытия, конкурирующие
источники, неоднозначная хронология).

ДВЕ НАХОДКИ ПРОПУЩЕНЫ ЦЕЛИКОМ — конфликт с решением читателя (review.py),
а не применены: «машинная правка не спорит с прочитанным».
- g4feb5ec3 (ХСкаут pre-IPO): review.FIXES уже поставил status=«Закрыта» по
  цитате «книгу заявок... полностью закрыл». Читатель этой партии нашёл
  ДРУГОЙ источник (ABN), прямо расходящийся с первым: «35% от заявленного
  объёма уже закрыто» — то есть раунд не закрыт целиком. Два источника
  спорят об одном и том же факте; решение остаётся за человеком.
- g20d4cc38 (ЛУКОЙЛ/Carlyle): review.FIXES поставил status=«Подписана» по
  ТОЙ ЖЕ цитате («заключенное соглашение... зависит от отлагательных
  условий»), которую читатель этой партии использовал для ПРОТИВОПОЛОЖНОГО
  вывода («Обсуждается» — соглашение не эксклюзивно, OFAC не одобрил).
  Разное прочтение одной и той же цитаты — решение за человеком.
Оба добавлены в `pipeline/send_open_questions.QUESTIONS` (см. тот файл) —
находки НЕ отмечены done, остаются в очереди.

ОДНА НАХОДКА (gc64703e2) ПРИМЕНЕНА, А НЕ ОТПРАВЛЕНА ВОПРОСОМ, хотя формально
была статьёй в QUESTIONS (id gc64703e2 удалён оттуда этим коммитом) —
потому что владелец УЖЕ решил именно этот класс вопроса правилом от
19 сентября 2026 (CLAUDE.md, «обсуждается без новостей много лет»):
молчание без прямого опровержения не делает сделку несостоявшейся. Текст
eco.context карточки уже дословно несёт требуемую правилом фразу («Обсуждение
тянется больше двух лет...») — только status ошибочно перепрыгнул на
«Не состоялась», хотя сама фраза лишь предполагает вероятность. Правило уже
даёт ответ на вопрос, который QUESTIONS всё ещё формально держал открытым.

СТРУКТУРНЫЙ СЛУЧАЙ (g5647e100): три записи events (kind=closed, тот же
факт — 31 июля 2026 года — но с датами ПУБЛИКАЦИЙ трёх разных изданий об
одном и том же закрытии, 08-05/08-06/08-10) слиты в одну, date=2026-07-31
(дата самого события, а не публикаций). Текст note объединён из дословных
фрагментов всех трёх источников — ничего сверх уже сказанного в карточке
не добавлено; один источник (Коммерсантъ, первичный по цитате СПАРК)
оставлен в поле source по образцу схемы (единственная пара, не список).

ОДНА НАХОДКА ПРИМЕНЕНА И ОТКАЧЕНА — ПОЙМАНА ПОЛНЫМ `pytest`, а не найдена
заранее (`test_gold_analytics.py::test_gold_top_purchases[g6d74bc39]`,
`test_ui.py::test_gold_rows_agree_with_client_rules`). Читатель партии
(batch_4) предложил date=2023-04-11 → 2024 для Shell/«Сахалин-2», обосновав
это тем, что фактическая покупка (Газпромом) завершилась в марте 2024 года.
Само по себе прочтение верное, но карточка — уже задокументированный
рецензентом случай (CLAUDE.md, «четвёртый разбор рецензента», и отдельная
запись в `pipeline/gold/analytics_gold.json`): два чтения дали ОДНУ цену по
ДВУМ РАЗНЫМ событиям (распоряжение о продаже НОВАТЭКу, 2023 — и позже
покупка Газпромом вместо него, 2024, та же сумма 94,8 млрд ₽), дата
намеренно оставлена спорной, а «структуру карточки решает человек» — это
дословная строка из gold-записи. Правка нового читателя, не знавшего про
этот прецедент, сдвинула бы карточку в «Крупнейшие покупки» в обход
решения, уже принятого и записанного. Дата оставлена как была
(2023-04-11); находка НЕ отмечена done — ждёт того же решения человека,
что и раньше.

ГОДА В ПРОФИЛЯХ КОМПАНИЙ (14 случаев + карточка g010ece87 — 2 профиля):
находки предлагали дать новый текст целиком, но при сверке с живой базой
разница всегда — ОДНА цифра года (проверено программно: 0 или 1 совпадение
токена года в тексте). Правится только эта цифра, а не текст целиком —
дисциплина «менять ровно то, что доказано находкой», не более. Одно
исключение отклонено: находка по domodedovo-aukcion (buyer_profile
g127cf704) предлагала ещё и дописать «и выкупила актив» — фактически
верно по carte, но это НОВОЕ утверждение сверх находки о годе, не входит в
эту партию (год всё равно поправлен).

Источник решений — консолидированные `out_0.json`..`out_4.json`
(`data/inbox/audit2/status_date_out/`, не в git — рабочий вывод пяти
читателей).

    python3 pipeline/fix_audit_status_date_mismatch_batch1_2026_09_21.py
    python3 pipeline/fix_audit_status_date_mismatch_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402

LOCKED_SKIP = {
    ("g4feb5ec3", "status"): "review.FIXES уже решил (Закрыта); другой источник партии расходится — вопрос владельцу",
    ("g20d4cc38", "status"): "review.FIXES уже решил (Подписана) по той же цитате, что и эта находка, вывод другой — вопрос владельцу",
}

STATUS_FIXES = {
    "g36bc7831": "Обсуждается",
    "g20d4cc38": "Обсуждается",  # заблокировано LOCKED_SKIP, оставлено для документации намерения
    "gcb309b35": "Не состоялась",
    "gafc80ee1": "Согласование получено",
    "g1d76aeb5": "Не состоялась",
    "gf87a65f7": "Не состоялась",
    "gc64703e2": "Обсуждается",
    "g931e89e1": "Не состоялась",
    "g4feb5ec3": "Обсуждается",  # заблокировано LOCKED_SKIP
}

DATE_FIXES = {
    "gad66fcec": "2026-08-21",
    "gmru-vostok-sever-pevek": "2026",
    "g113002a7": "2026-04-20",
    "g1edb1b9d": "2026-05-07",
    "g8af20254": "2026-02-13",
    "g7d64b437": "2025-03-20",
    "g4feb42fc": "2025-01-31",
    "ce7b84bec": "2025-12-18",
    "g3b9c077a": "2024-09-06",
    "gb70b4830": "2024-10-04",
    "ce4180b68": "2024",
    "g91d021c6": "2024",
    "g8430c9d9": "2022",
    "gb31c796f": "2023-09-21",
    "gc6322659": "2024",
    "mercedes": "2023-04-18",
    "g37f106cd": "2023",
    "g6d74bc39": "2024",
    "g76159e00": "2023-03-10",
    "gef7d4e54": "2022-11-02",
    "g50d455bb": "2023",
    # g6d74bc39 (Shell/«Сахалин-2») сюда НЕ входит — см. докстрою файла:
    # находка поймана и откачена полным pytest (gold-конфликт), дата
    # осталась 2023-04-11, находка не отмечена done.
    "g7a96dda2": "2026-09-03",
    "g2d653619": "2023-04-20",
    "g4bb21315": "2023",
    "gffed92e4": "2024",
}

# (card_id, event_index) -> новая дата события
EVENT_DATE_FIXES = {
    ("gdfce7e3d", 0): "2026-05-04",
    ("g6d73538c", 0): "2025",
    ("g7f396659", 0): "2026-05-29",
    ("g7a96dda2", 0): "2026-09-03",
}

# (card_id, event_index) -> (kind, title) — kind чинится находкой, title
# приведён в соответствие (иначе плашка "closed" будет подписана "Переговоры")
EVENT_KIND_FIXES = {
    ("g677f3309", 0): ("closed", "Сделка завершена"),
}

TITLE_FIXES = {
    "g91ec3558": "«Магнит» купил контрольный пакет «Азбуки вкуса»",
    "cbb6ba4c9": "АО «Альфа-банк» купил кинотеатр «Пушкинский» у группы «Каро Фильм»",
}

EXTRA_FIXES = {
    "g1eb1565c": (
        "Продан комплексный девелоперский проект на левом берегу Дона. "
        "Покупатель — ООО «Поколение», связанное с учредителем ГК «Сумма "
        "элементов» Георгием Плиевым. Компания создана как отдельная "
        "структура для диверсификации активов бизнесмена."
    ),
}

# company_id -> (старый год, новый год) — точечная замена ровно одной
# 4-значной цифры года, найденной находкой; текст вокруг не трогается.
COMPANY_DESC_YEAR_FIXES = {
    "g127cf704": ("2024", "2026"),
    "gaae34483": ("2025", "2026"),
    "g466479df": ("2025", "2026"),
    "g56e4248d": ("2025", "2026"),
    "gd2d19a26": ("2023", "2025"),
    "gfc0e493d": ("2023", "2025"),
    "gd28693f6": ("2023", "2025"),
    "gec77bc9b": ("2024", "2025"),
    "g79c674f6": ("2024", "2025"),
    "g27e61f37": ("2023", "2025"),
    "gf3f11590": ("2023", "2025"),
    "g470a51f2": ("2023", "2024"),
    "gd6c3c0ff": ("2023", "2024"),
    "gca251d50": ("2024", "2023"),
}

# card_id -> (роль карты, старый год, новый год) — профиль разрешается через
# card[роль], а не назван по id напрямую в самой находке
COMPANY_DESC_YEAR_FIXES_BY_ROLE = {
    "g010ece87": [("buyer", "2022", "2023"), ("target", "2022", "2023")],
}


def apply_events_merge(card: dict, log: list, write: bool) -> None:
    events = card.get("events") or []
    if len(events) != 3:
        log.append("g5647e100: events уже не из трёх записей (%d) — пропущено" % len(events))
        return
    expected_dates = {"2026-08-05", "2026-08-06", "2026-08-10"}
    if {e.get("date") for e in events} != expected_dates or any(e.get("kind") != "closed" for e in events):
        log.append("g5647e100: events не совпадает с ожидаемым — пропущено")
        return
    merged_note = (
        "31 июля 2026 года АО «Нейропоток», связанный с Новой инвестиционной "
        "группой, купило 100% долей ООО «Фрозен Бек» — одного из крупнейших "
        "российских производителей замороженной хлебобулочной продукции под "
        "брендом Frozella, с производственной площадкой в городском округе "
        "Пушкино Московской области. Прежний собственник — Патвакан Мкртчян. "
        "Сделку оценили в 8 млрд ₽."
    )
    log.append("g5647e100: три записи events (публикации 08-05/08-06/08-10 об одном и том же "
               "закрытии 31 июля) слиты в одну, date=2026-07-31")
    if write:
        card["events"] = [{
            "kind": "closed",
            "date": "2026-07-31",
            "title": "Сделка завершена",
            "note": merged_note,
            "source": ["Коммерсантъ", "https://www.kommersant.ru/doc/8862728"],
        }]


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    log: list = []
    applied = 0
    skipped = 0

    for cid, new_status in STATUS_FIXES.items():
        if (cid, "status") in LOCKED_SKIP:
            log.append("%s: status — %s" % (cid, LOCKED_SKIP[(cid, "status")]))
            skipped += 1
            continue
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено" % cid)
            skipped += 1
            continue
        if (cid, "status") in decided:
            log.append("%s: status решено читателем review.py — пропущено" % cid)
            skipped += 1
            continue
        log.append("%s: status %r -> %r" % (cid, card.get("status"), new_status))
        applied += 1
        if write:
            card["status"] = new_status

    for cid, new_date in DATE_FIXES.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено" % cid)
            skipped += 1
            continue
        if (cid, "date") in decided:
            log.append("%s: date решено читателем review.py — пропущено" % cid)
            skipped += 1
            continue
        log.append("%s: date %r -> %r" % (cid, card.get("date"), new_date))
        applied += 1
        if write:
            card["date"] = new_date

    for (cid, idx), new_date in EVENT_DATE_FIXES.items():
        card = cards.get(cid)
        events = card.get("events") if card else None
        if not events or idx >= len(events):
            log.append("%s: events[%d] недоступен — пропущено" % (cid, idx))
            skipped += 1
            continue
        log.append("%s: events[%d].date %r -> %r" % (cid, idx, events[idx].get("date"), new_date))
        applied += 1
        if write:
            events[idx]["date"] = new_date

    for (cid, idx), (new_kind, new_title) in EVENT_KIND_FIXES.items():
        card = cards.get(cid)
        events = card.get("events") if card else None
        if not events or idx >= len(events):
            log.append("%s: events[%d] недоступен — пропущено" % (cid, idx))
            skipped += 1
            continue
        log.append("%s: events[%d].kind %r -> %r, title %r -> %r"
                   % (cid, idx, events[idx].get("kind"), new_kind, events[idx].get("title"), new_title))
        applied += 1
        if write:
            events[idx]["kind"] = new_kind
            events[idx]["title"] = new_title

    apply_events_merge(cards["g5647e100"], log, write)
    if cards["g5647e100"] is not None:
        applied += 1

    for cid, new_title in TITLE_FIXES.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено" % cid)
            skipped += 1
            continue
        if (cid, "title") in decided:
            log.append("%s: title решено читателем review.py — пропущено" % cid)
            skipped += 1
            continue
        log.append("%s: title %r -> %r" % (cid, card.get("title"), new_title))
        applied += 1
        if write:
            card["title"] = new_title

    for cid, new_extra in EXTRA_FIXES.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено" % cid)
            skipped += 1
            continue
        if (cid, "extra") in decided:
            log.append("%s: extra решено читателем review.py — пропущено" % cid)
            skipped += 1
            continue
        log.append("%s: extra изменён (устаревший хедж снят)" % cid)
        applied += 1
        if write:
            card["extra"] = new_extra

    for company_id, (old_year, new_year) in COMPANY_DESC_YEAR_FIXES.items():
        comp = companies.get(company_id)
        if comp is None:
            log.append("company %s: профиля нет — пропущено" % company_id)
            skipped += 1
            continue
        desc = comp.get("desc") or ""
        pattern = r"\b%s\b" % old_year
        if len(re.findall(pattern, desc)) != 1:
            log.append("company %s: год %s встречается не ровно один раз — пропущено" % (company_id, old_year))
            skipped += 1
            continue
        log.append("company %s: desc год %s -> %s" % (company_id, old_year, new_year))
        applied += 1
        if write:
            comp["desc"] = re.sub(pattern, new_year, desc, count=1)

    for cid, role_fixes in COMPANY_DESC_YEAR_FIXES_BY_ROLE.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено" % cid)
            skipped += 1
            continue
        for role, old_year, new_year in role_fixes:
            company_id = card.get(role)
            comp = companies.get(company_id) if company_id else None
            if comp is None:
                log.append("%s: роль %s не разрешилась в профиль — пропущено" % (cid, role))
                skipped += 1
                continue
            desc = comp.get("desc") or ""
            pattern = r"\b%s\b" % old_year
            if len(re.findall(pattern, desc)) != 1:
                log.append("%s (%s): год %s встречается не ровно один раз — пропущено" % (cid, role, old_year))
                skipped += 1
                continue
            log.append("%s (%s, %s): desc год %s -> %s" % (cid, role, company_id, old_year, new_year))
            applied += 1
            if write:
                comp["desc"] = re.sub(pattern, new_year, desc, count=1)

    print("Применено: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
