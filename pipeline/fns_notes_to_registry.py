# -*- coding: utf-8 -*-
"""Приток, шаг вслед за очередью «нужен ИНН» (этап 3, П3'''): разбирает
ответы владельца на сообщения `[инн <id>]` и пишет подтверждённый ИНН в
`pipeline/fns_registry.py`.

ОТКУДА БЕРЁТСЯ ЗАМЕТКА. `pipeline/fns_unresolved_queue.py --to-console`
шлёт в Telegram-консоль по одному сообщению на компанию с маркером
`[инн <id>]` в первой строке. Ответ текстом на такое сообщение приходит
вебхуком (`main.py::telegram_webhook`) как решение `verdict='note'` с
`deal_id = "инн~<id>"` — префикс `инн~` не даёт заметке быть прочитанной
как правку карточки СДЕЛКИ с тем же голым id (семь таких совпадений уже
есть в базе: «citibank» и другие кураторские слаги — компания и сделка с
одинаковым именем).

ГРАНИЦА, КАК И ВЕЗДЕ В ПРИТОКЕ: механика применяет ТОЛЬКО то, что можно
проверить формально — контрольную сумму ИНН по алгоритму ФНС
(`fns_registry.inn_is_valid`, тот же, что уже стоит тестом на реестре).
Заметка, из которой не удалось однозначно вынуть валидный ИНН (опечатка,
два числа сразу, свободный текст вместо номера), НЕ потребляется этим
скриптом — она остаётся непрочитанной и попадёт в обычный
`pipeline/ingest/read_notes.py`, где её увидит человек или рутина при
следующем общем чтении заметок. Так же остаётся нетронутой заметка на
компанию, для которой в реестре уже ЕСТЬ запись (кто-то успел решить её
другим путём, пока ответ был в пути, — не перезаписываем чужое решение
молча).

ВТОРОЙ ПОТОК — ПОВТОРНЫЙ ВОПРОС ПО `no_match` (этап 9, П8-9). Заметка с
префиксом `"инн-омоним~"` (`pipeline/fns_homonym_queue.py`) отвечает на
компанию, которая УЖЕ есть в реестре с `decision="no_match"` — для нового
`decision="confirmed"` тут нельзя просто ДОПИСАТЬ запись (см. `collect()`
выше: «уже есть запись — не перезаписываем» защищает как раз от дублей
company_id, и `test_fns_registry_company_id_is_not_duplicated` не пропустит
двух текущих записей одного профиля). Вместо этого `edit_registry_entry()`
находит ИМЕННО ЭТОТ словарь в исходном тексте `fns_registry.py` через AST
(`ast.parse` + точные `lineno`/`col_offset` узла — не regex по фигурным
скобкам: причина `no_match` — свободный текст и может содержать что угодно,
включая случайные `},`) и заменяет его целиком, оставляя всё остальное в
файле нетронутым. Старый `reason` не исчезает — он дословно входит в новый
как история («Было: …»), это тот же принцип, что уже применяется при
слиянии двух записей `FIXES` в review.py (CLAUDE.md, «Правку нельзя
переписать — только заменить эквивалентной»).

Применив, скрипт отвечает РЕПЛАЕМ на исходное сообщение (что записано) и
`--consume`ит заметку — тот же контракт, что и у read_notes.py.

Запуск:
    python3 pipeline/fns_notes_to_registry.py            # план, без сети
    python3 pipeline/fns_notes_to_registry.py --write     # применить, ответить, consume
"""
import ast
import json
import os
import re
import sys
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "pipeline", "ingest"))

from pipeline.fns_registry import by_company_id, inn_is_valid  # noqa: E402
import read_notes  # noqa: E402

DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
PREFIX = "инн~"
HOMONYM_PREFIX = "инн-омоним~"
INN_RE = re.compile(r"(?<!\d)\d{10}(?:\d{2})?(?!\d)")


def parse_inn(text):
    """Единственная последовательность из 10 или 12 цифр, не приклеенная к
    другим цифрам, — иначе (два числа, дата, телефон) не гадаем."""
    hits = INN_RE.findall(text or "")
    return hits[0] if len(hits) == 1 else None


def collect(notes, registry_idx, companies):
    """(готово_к_записи, отклонено_с_причиной) для обычной очереди «нужен
    ИНН» (компании, которых в реестре ЕЩЁ НЕТ) — оба списка нужны для
    печати плана; действие происходит только при --write."""
    ready, rejected = [], []
    for n in notes:
        deal_id = str(n.get("deal_id") or "")
        if not deal_id.startswith(PREFIX) or deal_id.startswith(HOMONYM_PREFIX):
            continue
        cid = deal_id[len(PREFIX):]
        if cid not in companies:
            rejected.append((n, cid, "профиля %r нет в базе" % cid))
            continue
        if cid in registry_idx:
            rejected.append((n, cid, "уже есть запись в реестре (decision=%r) — "
                                     "не перезаписываем" % registry_idx[cid]["decision"]))
            continue
        inn = parse_inn(n.get("edited_text") or "")
        if not inn:
            rejected.append((n, cid, "не нашли ровно одно число из 10/12 цифр в ответе"))
            continue
        if not inn_is_valid(inn):
            rejected.append((n, cid, "контрольная сумма ИНН %s не сходится" % inn))
            continue
        ready.append((n, cid, inn))
    return ready, rejected


def collect_homonym(notes, registry_idx, companies):
    """(готово_к_правке, отклонено_с_причиной) для повторного вопроса по
    `no_match` (`pipeline/fns_homonym_queue.py`, префикс «инн-омоним~»).
    В отличие от `collect()`, здесь запись в реестре ОБЯЗАНА уже
    существовать — и с decision="no_match": именно её правим на месте."""
    ready, rejected = [], []
    for n in notes:
        deal_id = str(n.get("deal_id") or "")
        if not deal_id.startswith(HOMONYM_PREFIX):
            continue
        cid = deal_id[len(HOMONYM_PREFIX):]
        if cid not in companies:
            rejected.append((n, cid, "профиля %r нет в базе" % cid))
            continue
        row = registry_idx.get(cid)
        if not row:
            rejected.append((n, cid, "в реестре нет записи — это не сценарий «инн-омоним»"))
            continue
        if row["decision"] != "no_match":
            rejected.append((n, cid, "запись уже %r, не no_match — решена другим путём, не трогаем"
                                     % row["decision"]))
            continue
        inn = parse_inn(n.get("edited_text") or "")
        if not inn:
            rejected.append((n, cid, "не нашли ровно одно число из 10/12 цифр в ответе"))
            continue
        if not inn_is_valid(inn):
            rejected.append((n, cid, "контрольная сумма ИНН %s не сходится" % inn))
            continue
        ready.append((n, cid, inn, row))
    return ready, rejected


def append_registry(ready, path=None):
    path = path or os.path.join(ROOT, "pipeline", "fns_registry.py")
    src = open(path, encoding="utf-8").read()
    today = os.environ.get("FNS_QUEUE_DATE") or _date.today().isoformat()
    lines = [
        "",
        "",
        "# ============================================================================",
        "# ИНН от владельца — %s. Ответ на очередь «нужен ИНН» в Telegram-консоли" % today,
        "# (pipeline/fns_unresolved_queue.py --to-console), разобран pipeline/",
        "# fns_notes_to_registry.py: контрольная сумма ИНН сходится, запись одна.",
        "# ============================================================================",
        "REGISTRY += [",
    ]
    for n, cid, inn in ready:
        reason = "ИНН от владельца (заметка №%s, %s): %r." % (n["id"], today, (n.get("edited_text") or "").strip())
        lines.append('    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (cid, inn))
        lines.append('     "reason": %r,' % reason)
        lines.append('     "date": %r},' % today)
    lines.append("]")
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src, "не нашли конец REGISTRY в fns_registry.py — формат файла изменился"
    open(path, "w", encoding="utf-8").write(src.replace(marker, "\n".join(lines) + marker, 1))


def _entry_span(src, company_id):
    """(start, end) — точные символьные границы словаря `{"company_id":
    <company_id>, ...}` внутри REGISTRY в исходном тексте `src`, найденные
    через AST, а не регуляркой по фигурным скобкам: `reason` — свободный
    текст и может нести что угодно, включая случайные `},` внутри строки.
    None, если такой записи нет (или их несколько — реестр уже нарушает
    свой собственный инвариант, тест `test_fns_registry_company_id_is_not_
    duplicated` должен был поймать это раньше, чем мы сюда дойдём)."""
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, val in zip(node.keys, node.values):
            if (isinstance(key, ast.Constant) and key.value == "company_id"
                    and isinstance(val, ast.Constant) and val.value == company_id):
                hits.append(node)
                break
    if len(hits) != 1:
        return None
    node = hits[0]
    lines = src.splitlines(keepends=True)

    def offset(lineno, col):
        return sum(len(line) for line in lines[:lineno - 1]) + col

    return offset(node.lineno, node.col_offset), offset(node.end_lineno, node.end_col_offset)


def edit_registry_entry(company_id, new_fields, path=None):
    """Заменяет словарь `{"company_id": company_id, ...}` в REGISTRY на
    новый — `new_fields` целиком определяет содержимое (никакие старые поля
    не наследуются молча: вызывающий обязан явно перенести всё нужное,
    включая историю старой причины внутри новой). Возвращает True/False —
    нашли ли запись."""
    path = path or os.path.join(ROOT, "pipeline", "fns_registry.py")
    src = open(path, encoding="utf-8").read()
    span = _entry_span(src, company_id)
    if not span:
        return False
    start, end = span
    keys = ("company_id", "decision", "inn", "reason", "date")
    for k in new_fields:
        assert k in keys, "неизвестное поле %r — edit_registry_entry не переносит лишнее молча" % k
    new_text = ('{"company_id": %r, "decision": %r, "inn": %r,\n'
                '     "reason": %r,\n'
                '     "date": %r}' % (new_fields["company_id"], new_fields["decision"],
                                       new_fields["inn"], new_fields["reason"], new_fields["date"]))
    open(path, "w", encoding="utf-8").write(src[:start] + new_text + src[end:])
    return True


def main():
    write = "--write" in sys.argv

    notes = read_notes.fetch_notes()
    registry_idx = by_company_id()
    companies = json.load(open(DATA, encoding="utf-8"))["companies"]
    ready, rejected = collect(notes, registry_idx, companies)
    ready_h, rejected_h = collect_homonym(notes, registry_idx, companies)

    if not ready and not rejected and not ready_h and not rejected_h:
        print("Заметок по очереди «нужен ИНН» нет.")
        return

    if ready:
        print("Готово к записи, новая запись реестра (%d):" % len(ready))
        for n, cid, inn in ready:
            print("  %s -> ИНН %s (заметка №%s)" % (companies[cid].get("name", cid), inn, n["id"]))
    if ready_h:
        print("Готово к правке существующей записи no_match (%d):" % len(ready_h))
        for n, cid, inn, _row in ready_h:
            print("  %s -> ИНН %s (заметка №%s)" % (companies[cid].get("name", cid), inn, n["id"]))
    if rejected or rejected_h:
        print("\nНе применено, осталось для read_notes.py (%d):" % (len(rejected) + len(rejected_h)))
        for n, cid, why in rejected + rejected_h:
            print("  заметка №%s (%s): %s — %r" % (n["id"], cid, why, n.get("edited_text")))

    if not write:
        print("\nСухой прогон. Запись/ответ/consume — с ключом --write.")
        return

    applied_ids = []
    if ready:
        append_registry(ready)
        for n, cid, inn in ready:
            read_notes.send_reply(n["id"], "Записано: ИНН %s для «%s»." % (inn, companies[cid].get("name", cid)))
            applied_ids.append(n["id"])

    if ready_h:
        today = os.environ.get("FNS_QUEUE_DATE") or _date.today().isoformat()
        for n, cid, inn, old_row in ready_h:
            new_reason = ("ИНН от владельца (заметка №%s, %s): %r. Было (no_match, %s): %s"
                          % (n["id"], today, (n.get("edited_text") or "").strip(),
                             old_row.get("date"), old_row.get("reason")))
            ok = edit_registry_entry(cid, {
                "company_id": cid, "decision": "confirmed", "inn": inn,
                "reason": new_reason, "date": today,
            })
            assert ok, "не нашли запись %r в fns_registry.py при --write — состояние разошлось с collect_homonym()" % cid
            read_notes.send_reply(n["id"], "Записано: ИНН %s для «%s» (было no_match)."
                                  % (inn, companies[cid].get("name", cid)))
            applied_ids.append(n["id"])

    if applied_ids:
        read_notes.consume(applied_ids)
        print("\nЗаписано в pipeline/fns_registry.py, отвечено, заметки помечены применёнными.")


if __name__ == "__main__":
    main()
