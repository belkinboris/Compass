# -*- coding: utf-8 -*-
"""Очередь аудита: устаревшие утверждения и соседние классы — первая партия,
разобрана 5 параллельными читателями (143 находки: STALE_STATEMENT 87,
ASSET_IS_DESCRIPTION 21, SOURCE_MISMATCH 15, PRESS_LANGUAGE 10, LONG_QUOTE 10).

Главный класс — STALE_STATEMENT: карточка говорит о будущем («сделка ждёт
одобрения ФАС», «планирует продать») о том, что давно случилось или
провалилось. Читатель приводит фразу к прошедшему времени ТОЛЬКО по фактам,
которые уже стоят в этой же карточке; если исход нигде не назван (одобрила
ли ФАС на самом деле), время снимается, но исход НЕ дописывается — иначе
правка времени превращается в новое утверждение. Несколько находок именно
на этом и остановились: читатели сходили в источник, не нашли решения органа
и оставили «требовалось одобрение», а не «одобрение получено».

Дисциплина та же, что у предыдущих партий: читатель отдаёт ПОЛНЫЙ текст поля
до и после, скрипт сверяет текущее значение с ожидаемым «до» и только потом
пишет. Поля бывают четырёх видов — простое (`title`, `asset`), вложенное
(`eco.context`), профиль компании (`company:<id>.desc`), подпись источника
(`src[2][0]`) и структурный список (`law.adv`, `events` — тогда тексты «до» и
«после» это JSON списка целиком).

    python3 pipeline/fix_audit_stale_batch1_2026_09_21.py
    python3 pipeline/fix_audit_stale_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "stale_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

SRC_RX = re.compile(r"^src\[(\d+)\]\[(\d+)\]$")
# `law.adv[1][2]` — описание второго консультанта; `events[0].note` — текст вехи.
ADV_RX = re.compile(r"^law\.adv\[(\d+)\]\[(\d+)\]$")
EVENT_RX = re.compile(r"^events\[(\d+)\]\.(\w+)$")
STRUCTURED = ("law.adv", "events")


def read_field(card, companies, field):
    """(текущее значение как строка, функция записи) или (None, None)."""
    if field.startswith("company:"):
        cid, sub = field[len("company:"):].split(".", 1)
        comp = companies.get(cid)
        if comp is None:
            return None, None
        return comp.get(sub), lambda v: comp.__setitem__(sub, v)
    m = SRC_RX.match(field)
    if m:
        i, j = int(m.group(1)), int(m.group(2))
        src = card.get("src") or []
        if i >= len(src) or j >= len(src[i]):
            return None, None
        return src[i][j], lambda v: src[i].__setitem__(j, v)
    m = ADV_RX.match(field)
    if m:
        i, j = int(m.group(1)), int(m.group(2))
        adv = (card.get("law") or {}).get("adv") or []
        if i >= len(adv) or j >= len(adv[i]):
            return None, None
        return adv[i][j], lambda v: adv[i].__setitem__(j, v)
    m = EVENT_RX.match(field)
    if m:
        i, sub = int(m.group(1)), m.group(2)
        events = card.get("events") or []
        if i >= len(events):
            return None, None
        return events[i].get(sub), lambda v: events[i].__setitem__(sub, v)
    if field in STRUCTURED:
        cur = get_field(card, field) if "." in field else card.get(field)
        setter = ((lambda v: set_field(card, field, v)) if "." in field
                  else (lambda v: card.__setitem__(field, v)))
        return json.dumps(cur, ensure_ascii=False), lambda v: setter(json.loads(v))
    cur = get_field(card, field) if "." in field else card.get(field)
    setter = ((lambda v: set_field(card, field, v)) if "." in field
              else (lambda v: card.__setitem__(field, v)))
    return cur, setter


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    by_key = {}
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            by_key.setdefault(it["key"], it)

    log, applied, skipped = [], 0, 0
    for key, it in by_key.items():
        if it["action"] != "fix":
            continue
        cid, field = it["card_id"], it.get("field") or ""
        card = cards.get(cid)
        if card is None:
            log.append("%s (%s): карточки нет — пропущено" % (key, cid))
            skipped += 1
            continue
        # «Машинная правка не спорит с прочитанным»: поле сделки, по которому
        # читатель уже принял решение через review.py, не трогаем.
        if not field.startswith("company:") and not SRC_RX.match(field) \
                and (cid, field) in decided:
            log.append("%s (%s): %s решено читателем review.py — пропущено" % (key, cid, field))
            skipped += 1
            continue
        cur, setter = read_field(card, companies, field)
        if setter is None:
            log.append("%s (%s): поле %s не разрешилось — пропущено" % (key, cid, field))
            skipped += 1
            continue
        expected = it.get("old_full_text")
        if expected is not None and (cur or "") != expected:
            log.append("%s (%s): %s не совпадает с ожидаемым — пропущено" % (key, cid, field))
            skipped += 1
            continue
        log.append("%s (%s): %s обновлено" % (key, cid, field))
        applied += 1
        if write:
            setter(it.get("new_full_text"))

    # ДВЕ ПРАВКИ ПОВЕРХ ПАРТИИ — их поймал полный pytest, а не читатель.
    # Переименование профиля из описания в имя дважды задело то, что лежит
    # РЯДОМ с именем и о чём находка не знала.
    #
    # 1. «допэмиссии «Деметра-холдинга»» → «Деметра-холдинг» столкнулось с уже
    #    существующим профилем «Деметра-Холдинг» (test_no_company_twins): одна
    #    компания оказалась записана дважды. У дубля была одна ссылка из
    #    карточки, у настоящего профиля — семь; карточка переставлена на
    #    настоящий, дубль и его псевдоним сняты.
    # 2. У CanPack псевдонимы остались от старого имени-описания («владелец
    #    активов, американская компания») и после переименования перестали
    #    пересекаться с именем (test_match_key_alias_is_a_name). По таким
    #    псевдонимам поиск не срабатывает никогда — сняты, осталось имя.
    mk = data.get('match_keys') or {}
    dup, real = 'g040f6110', 'g519f8484'
    if companies.get(dup, {}).get('name') == 'Деметра-холдинг' and real in companies:
        moved = [d['id'] for d in data['deals'] if d.get('target') == dup]
        for d in data['deals']:
            for role in ('buyer', 'target', 'seller_id', 'asset_id'):
                if d.get(role) == dup:
                    if write:
                        d[role] = real
        log.append('дубль профиля %s → %s (карточки: %s)' % (dup, real, ', '.join(moved)))
        applied += 1
        if write:
            companies.pop(dup, None)
            mk.pop(dup, None)
    bad_alias = [a for a in (mk.get('gc6965a4f') or []) if 'владелец активов' in a]
    if bad_alias:
        log.append('CanPack: сняты %d псевдонима от старого имени-описания' % len(bad_alias))
        applied += 1
        if write:
            mk['gc6965a4f'] = [a for a in mk['gc6965a4f'] if a not in bad_alias]

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
