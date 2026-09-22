# -*- coding: utf-8 -*-
"""Закрытие очереди аудита: смешанная партия из семнадцати классов.

Партия собрана не по классу, а по признаку «это можно внести, прочитав
карточку»: ROLE_MISSING (сторона названа в тексте, но поля роли нет),
OTHER, TYPE_MISMATCH, SUM_FIELDS_DIFFER, CONTRADICTION, SUM_NOT_PRICE,
STATUS_MISMATCH, DATE_MISMATCH, ASSET_IS_DESCRIPTION, PARTY_IN_ASSET_NAME,
FALSE_PLACEHOLDER, TRUNCATED и другие мелкие.

За её границами осталось то, что прочтением одной карточки не закрывается,
и это названо честно, а не отложено молча:
  • UNLINKED_PARTY (536) — сторона названа текстом, профиля компании в базе
    нет. Механический путь исчерпан: `link_parties.py` находит ровно одну
    привязку на всю базу. Разных названий за находками — 497, то есть это
    кампания заведения профилей, а не партия правок.
  • FIELD_MISPLACED (349) — из них 252 упираются в поле, которое уже писал
    читатель через review.py. Перенести текст ИЗ такого поля значит оставить
    строку таблицы правок неприменённой и уронить
    `test_review_table_is_applied_and_not_pending`. Механизм «правка
    применена, хотя поле изменилось» в проекте есть (`proofread_absorbed`),
    но он про вычитку; распространять его на переносы — отдельное решение.

ДИСЦИПЛИНА ПРИМЕНЕНИЯ — та же, что у предыдущих партий, и каждая её часть
появилась после конкретной поломки:
 1. Читатель отдаёт ПОЛНЫЙ текст поля до и после; скрипт сверяет «до» с
    текущим значением и молча не пишет ничего, если оно разошлось.
 2. Машинная правка не спорит с прочитанным: поле, по которому читатель уже
    принял решение через review.py, пропускается.
 3. Ссылка на профиль принимается только на существующий id — иначе это
    выдумка.
 4. Одна компания — одна роль в сделке; карточка, где после правок это
    нарушилось бы, откатывается целиком.
 5. Несколько правок одной находки применяются В ПОРЯДКЕ, который дал
    читатель (сначала снятие ссылки, потом установка), иначе на мгновение
    возникает запрещённое состояние.

    python3 pipeline/fix_audit_close_2026_09_21.py
    python3 pipeline/fix_audit_close_2026_09_21.py --write
"""
from __future__ import annotations

import copy
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
OUT_DIR = ROOT / "data" / "inbox" / "audit2" / "close_out"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import get_field, set_field  # noqa: E402

sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
import review  # noqa: E402
from review import _linker_key  # noqa: E402  «ООО «Х»» и «Х» — одно имя


def readers_rows_still_hold(card, companies, fields):
    """Правки читателя по этим полям по-прежнему считаются применёнными.

    ТОЧНАЯ ПРОВЕРКА ВМЕСТО ГРУБОГО ЗАМКА. Правило «машинная правка не спорит
    с прочитанным» раньше запрещало трогать ЛЮБОЕ поле, которого когда-то
    касался `review.py`. Замер 21 сентября 2026 показал, что запрет шире
    нужного: из 252 находок класса «факт не в том поле», упиравшихся в такое
    поле, у 203 (81%) правка читателя уже ПОГЛОЩЕНА вычиткой — её отпечаток
    записан в `proofread_absorbed`, и сам `review.already_applied` с этого
    момента считает строку применённой независимо от текста поля.

    Поэтому спрашиваем не «трогал ли это поле читатель», а «остаётся ли его
    правка применённой ПОСЛЕ нашей». Судья — сам review.py: один исполнитель
    правил, а не вторая копия рассуждения о них. Проверено на живой
    карточке: перенос предложения из `eco.context` в `law.terms` оставляет
    `test_review_table_is_applied_and_not_pending` зелёным.
    """
    for row in review.FIXES:
        if row["id"] != card["id"] or row.get("field") not in fields:
            continue
        if not review.already_applied(row, card, companies):
            return False
    return True

ROLE_IDS = ("buyer", "seller_id", "target", "asset_id")
SRC_RX = re.compile(r"^src\[(\d+)\]\[(\d+)\]$")
ADV_RX = re.compile(r"^law\.adv\[(\d+)\]\[(\d+)\]$")
EVENT_RX = re.compile(r"^events\[(\d+)\]\.(\w+)$")
AS_JSON = ("law.adv", "events", "src")
STRAIGHT_QUOTES = ('"', "“", "”")
QUOTED_FIELDS = ("title", "seller", "buyer_name", "asset")


def read_field(card, companies, field):
    """(текущее значение, функция записи) или (None, None), если поля нет."""
    if field.startswith("company:"):
        cid, sub = field[len("company:"):].split(".", 1)
        comp = companies.get(cid)
        if comp is None:
            return None, None
        return comp.get(sub), lambda v: comp.__setitem__(sub, v)
    for rx, getter in ((SRC_RX, "src"), (ADV_RX, "adv")):
        m = rx.match(field)
        if m:
            i, j = int(m.group(1)), int(m.group(2))
            box = (card.get("src") or []) if getter == "src" else ((card.get("law") or {}).get("adv") or [])
            if i >= len(box) or j >= len(box[i]):
                return None, None
            return box[i][j], lambda v: box[i].__setitem__(j, v)
    m = EVENT_RX.match(field)
    if m:
        i, sub = int(m.group(1)), m.group(2)
        events = card.get("events") or []
        if i >= len(events):
            return None, None
        return events[i].get(sub), lambda v: events[i].__setitem__(sub, v)
    cur = get_field(card, field) if "." in field else card.get(field)
    setter = ((lambda v: set_field(card, field, v)) if "." in field
              else (lambda v: card.__setitem__(field, v)))
    if field in AS_JSON:
        return json.dumps(cur, ensure_ascii=False), lambda v: setter(
            json.loads(v) if isinstance(v, str) else v)
    return cur, setter


def _card_strings(card):
    """Все строки карточки, кроме слоя фактов (он производный)."""
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k != "facts":
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(card)
    return out


def _sentences(text):
    # Режем ТОЛЬКО по точке-восклицанию-вопросу. По закрывающей ёлочке резать
    # нельзя: «Об интересе «Черноголовки» к бизнесу Kellogg…» развалилось бы
    # посреди фразы, и половина предложения объявилась бы потерянной.
    text = re.sub(r"\s+", " ", str(text or ""))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 40]


def sentences_readers_placed(all_items):
    """Предложения, которые читатели этой кампании ПЕРЕНЕСЛИ в новое поле.

    Вычисляется по всем ответам сразу, а не по одному: ровно в этом и была
    беда — находки разных читателей применялись разными прогонами, и второй
    не знал, что первый только что положил в поле.
    """
    placed = set()
    for it in all_items:
        was = re.sub(r"\s+", " ", str(it.get("old_full_text") or ""))
        for sent in _sentences(it.get("new_full_text") or ""):
            if sent not in was:
                placed.add(sent)
    return placed


def lost_sentences(before, after, placed):
    """Перенесённое другим читателем предложение, исчезнувшее из карточки.

    ПОЧЕМУ ЭТА ПРОВЕРКА ОТДЕЛЬНАЯ ОТ СВЕРКИ «ДО». Сверка `old_full_text`
    отвечает на вопрос «не изменилось ли поле с тех пор, как читатель его
    прочитал». У неё нашлась слепая зона: две находки одной карточки
    разбирали разные читатели. Первый перенёс предложение в пустой
    «Контекст». Второй читал карточку уже ПОСЛЕ него, увидел там чужое
    предложение — и честно заменил поле целиком, как и требует формат ответа
    («new_full_text — полный текст поля»). «До» у него было свежим,
    откатывать было нечего, а предложение исчезло из базы совсем
    (`g1f098415`, Kellogg → «Черноголовка»).

    ПОЧЕМУ СТОРОЖ СМОТРИТ ТОЛЬКО НА ПЕРЕНЕСЁННОЕ, А НЕ НА ЛЮБУЮ ПРОПАЖУ.
    Удалять текст читателю МОЖНО и нужно: классы STALE_STATEMENT и
    CONTRADICTION ровно об этом («Теперь компания намерена увеличить долю до
    100%» при уже состоявшейся консолидации). Замер по партии 21 сентября:
    сторож «пропало любое предложение» откатил бы 6 находок из 65, и пять из
    шести были законными удалениями. Сторож «пропало предложение, которое
    ТОЛЬКО ЧТО перенёс другой читатель» откатывает ровно ту одну, ради
    которой заведён.
    """
    now = " || ".join(re.sub(r"\s+", " ", s) for s in _card_strings(after))
    gone = []
    for chunk in _card_strings(before):
        for sent in _sentences(chunk):
            if sent not in placed:
                continue
            if sent in now or sent.rstrip(".") in now or sent[:40] in now:
                continue
            gone.append(sent)
    return gone


def roles_are_distinct(card):
    used = [card.get(r) for r in ROLE_IDS if card.get(r)]
    return len(used) == len(set(used))


def main(write: bool, out_dir=None) -> int:
    global OUT_DIR
    if out_dir:
        OUT_DIR = ROOT / "data" / "inbox" / "audit2" / out_dir
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    companies = data["companies"]
    decided = aq.decided_by_a_reader()

    items = []
    for path in sorted(glob.glob(str(OUT_DIR / "out_*.json"))):
        for it in json.loads(Path(path).read_text(encoding="utf-8")):
            if it.get("action") == "fix":
                items.append(it)
    # ГРУППИРУЕМ ПО НАХОДКЕ, А НЕ ПО КАРТОЧКЕ. Первая версия откатывала всю
    # карточку при первом несовпадении «до» — и уносила с собой правки других
    # читателей по той же карточке: у `g4cd1fa52` устаревшее «до» в одном
    # файле отменяло верную правку из другого. Единица отката — находка
    # (`key`): её правки применяются все или ни одной (они бывают связаны:
    # «снять ссылку» + «поставить другую»), а соседние находки не страдают.
    by_key = {}
    for it in items:
        by_key.setdefault((it["card_id"], it["key"]), []).append(it)
    # Считается по ВСЕМ ответам сразу и до первой правки: находки разных
    # читателей применяются разными прогонами, и второй не должен затереть
    # то, что первый только что перенёс.
    placed = sentences_readers_placed(items)

    log, applied, skipped = [], 0, 0
    for (cid, _key), parts in by_key.items():
        card = cards.get(cid)
        if card is None:
            log.append("%s: карточки нет — пропущено (%d)" % (cid, len(parts)))
            skipped += len(parts)
            continue
        before = copy.deepcopy(card)
        trouble, done, touched_decided = None, [], set()
        for it in parts:
            field = str(it.get("field") or "")
            new = it.get("new_full_text")
            if not field:
                trouble = "правка без поля"
                break
            if not field.startswith("company:") and (cid, field) in decided:
                touched_decided.add(field)
            if field in ROLE_IDS and new and new not in companies:
                trouble = "профиля %s нет в базе — это была бы выдумка" % new
                break
            if field in QUOTED_FIELDS and isinstance(new, str) \
                    and any(q in new for q in STRAIGHT_QUOTES):
                trouble = "в %s кавычки не ёлочки" % field
                break
            cur, setter = read_field(card, companies, field)
            if setter is None:
                trouble = "поле %s не разрешилось" % field
                break
            expected = it.get("old_full_text")
            if not ((cur or None) == (expected or None) or str(cur) == str(expected)):
                trouble = "%s не совпадает с ожидаемым «до»" % field
                break
            setter(new)
            done.append(field)
        # ПОКУПАТЕЛЬ НАЗВАН ОДИН РАЗ — профилем ИЛИ текстом (замер: 1096
        # карточек только с профилем, 155 только с текстом, ни одной с
        # обоими; держит `test_buyer_is_named_once`). У продавца соглашение
        # ДРУГОЕ: и профиль, и текст стоят у 316 карточек — там чистить
        # нечего. Привязка покупателя обязана убрать текст, но убрать его
        # можно не всегда:
        #   • текст писал читатель через review.py и имя профиля с ним не
        #     совпадает — снятие оставит строку таблицы правок неприменённой
        #     («Группа компаний «Свеза»» против профиля «Свеза»);
        #   • в тексте названы ДВЕ стороны («X и Y») — одной ссылкой это не
        #     выражается, и половина факта пропадёт.
        # В обоих случаях привязка откатывается, находка уходит владельцу:
        # пустое место честнее половины факта.
        if not trouble and card.get("buyer") and card.get("buyer_name") \
                and any(p.get("field") == "buyer" for p in parts):
            name = (companies.get(card["buyer"]) or {}).get("name") or ""
            text = str(card.get("buyer_name") or "")
            if (cid, "buyer_name") in decided and _linker_key(name) != _linker_key(text):
                trouble = "имя покупателя текстом поставил читатель и оно шире профиля"
            elif re.search(r"\sи\s|,", text):
                trouble = "в тексте названы две стороны — одной ссылкой не выражается"
            else:
                card.pop("buyer_name", None)
                done.append("buyer_name снято (имя несёт профиль)")
        # Флаг «предметом стоял продавец» — пометка о ДЕФЕКТЕ, а не факт
        # сделки: клиент по нему выводит сноску «подробности о предмете — во
        # вкладке «Экономист»». Как только предмет привязан, пометка врёт о
        # состоянии карточки. Снимается тем же движением, что и в
        # `merge_essity_shilov_dup.py`.
        if not trouble and card.get("target") and card.get("target_was_seller") \
                and any(p.get("field") == "target" for p in parts):
            card.pop("target_was_seller", None)
            done.append("target_was_seller снят (предмет привязан)")
        # Поля, которых когда-то касался читатель, проверяем ТОЧНО: остаются
        # ли его строки применёнными после нашей правки. Судит сам review.py.
        if not trouble and touched_decided \
                and not readers_rows_still_hold(card, companies, touched_decided):
            trouble = ("правка оставила бы строку читателя (%s) неприменённой"
                       % ", ".join(sorted(touched_decided)))
        if not trouble and not roles_are_distinct(card):
            trouble = "после правки компания заняла бы две роли"
        # ПЕРЕНОС НЕ ТЕРЯЕТ ТЕКСТ. Правка переставляет предложения между
        # полями одной карточки, поэтому предложение, стоявшее в карточке
        # ДО правки, обязано найтись в ней и ПОСЛЕ — хоть в другом поле.
        # Исключение — когда читатель сам переписал это предложение
        # (устаревшее время, противоречие): тогда его новая версия стоит в
        # `new_full_text` той же находки, и начало предложения там есть.
        if not trouble:
            gone = lost_sentences(before, card, placed)
            if gone:
                trouble = "правка потеряла бы текст: «%s…»" % gone[0][:60]
        if trouble:
            cards[cid].clear()
            cards[cid].update(before)
            log.append("%s: %s — откат %d правок" % (cid, trouble, len(parts)))
            skipped += len(parts)
            continue
        log.append("%s: %s" % (cid, ", ".join(done)))
        applied += len(done)

    print("Применено правок: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    d = None
    for i, a in enumerate(sys.argv):
        if a == "--dir" and i + 1 < len(sys.argv):
            d = sys.argv[i + 1]
    sys.exit(main("--write" in sys.argv, d))
