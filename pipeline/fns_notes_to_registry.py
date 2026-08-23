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

Применив, скрипт отвечает РЕПЛАЕМ на исходное сообщение (что записано) и
`--consume`ит заметку — тот же контракт, что и у read_notes.py.

Запуск:
    python3 pipeline/fns_notes_to_registry.py            # план, без сети
    python3 pipeline/fns_notes_to_registry.py --write     # применить, ответить, consume
"""
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
INN_RE = re.compile(r"(?<!\d)\d{10}(?:\d{2})?(?!\d)")


def parse_inn(text):
    """Единственная последовательность из 10 или 12 цифр, не приклеенная к
    другим цифрам, — иначе (два числа, дата, телефон) не гадаем."""
    hits = INN_RE.findall(text or "")
    return hits[0] if len(hits) == 1 else None


def collect(notes, registry_idx, companies):
    """(готовые_к_записи, отклонённые_с_причиной) — оба списка нужны для
    печати плана; действие происходит только при --write."""
    ready, rejected = [], []
    for n in notes:
        deal_id = str(n.get("deal_id") or "")
        if not deal_id.startswith(PREFIX):
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


def main():
    write = "--write" in sys.argv

    notes = read_notes.fetch_notes()
    registry_idx = by_company_id()
    companies = json.load(open(DATA, encoding="utf-8"))["companies"]
    ready, rejected = collect(notes, registry_idx, companies)

    if not ready and not rejected:
        print("Заметок по очереди «нужен ИНН» нет.")
        return

    if ready:
        print("Готово к записи (%d):" % len(ready))
        for n, cid, inn in ready:
            print("  %s -> ИНН %s (заметка №%s)" % (companies[cid].get("name", cid), inn, n["id"]))
    if rejected:
        print("\nНе применено, осталось для read_notes.py (%d):" % len(rejected))
        for n, cid, why in rejected:
            print("  заметка №%s (%s): %s — %r" % (n["id"], cid, why, n.get("edited_text")))

    if not write:
        print("\nСухой прогон. Запись/ответ/consume — с ключом --write.")
        return

    if ready:
        append_registry(ready)
        for n, cid, inn in ready:
            read_notes.send_reply(n["id"], "Записано: ИНН %s для «%s»." % (inn, companies[cid].get("name", cid)))
        read_notes.consume([n["id"] for n, _cid, _inn in ready])
        print("\nЗаписано в pipeline/fns_registry.py, отвечено, заметки помечены применёнными.")


if __name__ == "__main__":
    main()
