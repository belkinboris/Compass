# -*- coding: utf-8 -*-
"""Sokolov (g04328d0f) получил вопрос «инн-омоним» в Telegram-консоли
31 августа 2026 (~10:57 МСК, сессия cse_016orpUdRbSsXqfPhLtsFena,
триггер «нужен ИНН») — владелец прислал скриншот с этим вопросом. Но
штамп `fns_asked`, который `fns_homonym_queue.py` пишет в том же прогоне
сразу после отправки, в репозиторий не попал: тот же класс потери, что
уже описан в CLAUDE.md («Отправка в Telegram и запись «отправлено»
разнесены во времени — сбой между ними шлёт дубль») — только здесь роль
повторной публикации играет повторный вопрос владельцу.

Без этой правки следующий прогон `fns_homonym_queue.py --write` увидел бы
Sokolov как ещё не спрошенного и отправил бы тот же вопрос ЕЩЁ РАЗ, хотя
ответ уже виден в консоли.

Штампуем ТОЛЬКО Sokolov, а не весь предполагаемый пакет позиций 6-10
CANDIDATES: проверка базы показала, что состав пакета не совпадает с
наивным «следующие пять по списку» — g63814c8a («Медкапитал», позиция 10)
удалён из базы 25.08.2026 (`pipeline/fns_registry.py`, комментарий у
`gf3a496bd`), а gb330c34a/gc2792a44/g47bca1da (КСЭ/АФК «Система»/«Детский
мир», позиции 11-13) с тех пор получили `decision: confirmed` в реестре
через отдельную кампанию самопроверки — `eligible()` их уже не отдаёт
независимо от `fns_asked`. Прямого подтверждения (скриншота), что
Приосколье/Бизнес-Недвижимость/Гулливер были отправлены В ТОМ ЖЕ пакете,
нет — штамповать их без доказательства рискованнее, чем оставить как
есть: ложный штамп молча снимает компанию с очереди навсегда, а лишний
повторный вопрос — это просто более raннее переспрашивание, не потеря.

`add_repo`-фикс триггера (31 августа, ШАГ 0 промпта) применён ДО этого
конкретного прогона и всё равно не помог — причина потери пуша в этом
случае, видимо, не в авторизации репозитория, а в чём-то другом
(например, гонка с параллельным коммитом другой рутины на шаге
`git pull --rebase`); это отдельный, ещё не решённый вопрос.

Запуск: python3 pipeline/fix_stamp_fns_asked_lost_homonym_batch.py --write
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")

# Подтверждено скриншотом владельца — только Sokolov.
LOST_BATCH = ["g04328d0f"]

STAMP_DATE = "2026-08-31"


def main():
    write = "--write" in sys.argv
    base = json.load(open(DATA, encoding="utf-8"))
    companies = base["companies"]

    changed = []
    for cid in LOST_BATCH:
        profile = companies.get(cid)
        assert profile is not None, "профиль %s пропал из базы" % cid
        assert not profile.get("fns_asked"), (
            "%s (%s) уже несёт fns_asked=%r — правка больше не нужна, "
            "проверьте вручную, не задваиваем" % (cid, profile.get("name"), profile.get("fns_asked"))
        )
        changed.append((cid, profile.get("name")))

    print("К штамповке (%d):" % len(changed))
    for cid, name in changed:
        print("  %s (%s)" % (name, cid))

    if not write:
        print("\nСухой прогон. Запись — с ключом --write.")
        return

    for cid, _ in changed:
        companies[cid]["fns_asked"] = STAMP_DATE

    json.dump(base, open(DATA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\nЗаписано.")


if __name__ == "__main__":
    main()
