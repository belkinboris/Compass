# -*- coding: utf-8 -*-
"""99 вопросов аудита, которые 21 сентября 2026 ушли «на решение владельца».

Владелец 25 сентября: разобрать их по первоисточникам самим и принести ему
только спорные («сделай»). Пять читателей (саб-агенты по
`pipeline/audit_field_placement/READER_BRIEF_2026_09_21.md`) прочитали
карточки и источники и записали ответы в `data/inbox/audit2/owner99_out/`
в формате `fix_audit_close_2026_09_21.py`: fix / reject / owner, полный
текст поля до и после, цитата и ссылка.

ПОЧЕМУ ЭТИ ВОПРОСЫ НЕ РЕШИЛИСЬ МАШИННО И ЧТО ИЗМЕНИЛОСЬ. Почти у всех
правка упиралась в поле, которое когда-то заполнил читатель через
`review.py`: перенести текст ИЗ такого поля значит оставить его строку
таблицы правок «неприменённой», и `fix_audit_close` такую находку
откатывает. Выход, который тот скрипт назвал «отдельным решением», принят
здесь: строка читателя, применённая ДО этой правки, запоминается в
`proofread_absorbed` карточки — тем же механизмом, что у вычитки. Смысл
тот же: правка читателя была в базе, потом поле сознательно переписал
проверенный шаг (здесь — повторное чтение источника по поручению
владельца). Факт при этом не пропадает молча: перенос обязан сохранить
каждое перенесённое предложение (сторож `lost_sentences`), а удаление или
замена фразы идёт только с цитатой источника в ответе читателя.

Все остальные защиты `fix_audit_close` остаются: сверка «до» символ в
символ, ссылка только на существующий профиль, одна компания — одна роль,
имя покупателя текстом шире профиля — откат.

    python3 pipeline/fix_audit_owner99_2026_09_25.py            # сухой прогон
    python3 pipeline/fix_audit_owner99_2026_09_25.py --write
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline import fix_audit_close_2026_09_21 as close  # noqa: E402

review = close.review
ABSORBED = []


def name_key(name):
    """Сравнение имён покупателя без приставок, которых не знает
    `_linker_key` (`review.party_name_key`): «МКПАО «Яндекс»» и «Яндекс»,
    «Группа компаний «Брусника»» и «ГК «Брусника»» — одна компания. Всё
    остальное сравнивается как прежде («ООО «Сбербанк Инвестиции»» и
    «СберИнвест» — по-прежнему разные)."""
    return review.party_name_key(name)


def absorb_readers_rows(card, companies, fields):
    """Вместо отката — запомнить строки читателя по тронутым полям."""
    for row in review.FIXES:
        if row["id"] != card["id"] or row.get("field") not in fields:
            continue
        if review.already_applied(row, card, companies):
            continue
        box = card.setdefault("proofread_absorbed", {}).setdefault(row["field"], [])
        fp = review.fix_fingerprint(row["new"])
        if fp not in box:
            box.append(fp)
            ABSORBED.append("%s.%s" % (card["id"], row["field"]))
    return True


# Ответы, которые НЕ вносим. 41bd2dd113bf (gfebe16ad, отель Courtyard в
# Казани): читатель предложил вместо пустой суммы «Не раскрыта». Прежний
# читатель сознательно оставил её пустой, сняв стартовую цену торгов, а
# «Не раскрыта» — утверждение, что стороны цену скрыли, а не «мы не нашли».
SKIP_KEYS = {"41bd2dd113bf"}

# Псевдонимы, оставшиеся от старого названия профиля Amber («… 
# (национализированный владелец)» — приписка из истории Talvis, снятая с
# имени читателем): кусок фразы, а не имя (`test_match_key_alias_is_a_name`).
DROP_ALIASES = {"g565484bd": {"amber beverage group holding (национализированный владелец)",
                              "национализированный владелец"}}


def tidy(write):
    """После записи: убрать псевдонимы-обрывки и вернуть снятую правку."""
    import json
    data = json.loads(close.DATA.read_text(encoding="utf-8"))
    changed = False
    for cid, drop in DROP_ALIASES.items():
        keys = data["match_keys"].get(cid) or []
        kept = [k for k in keys if k not in drop]
        if kept != keys:
            data["match_keys"][cid] = kept
            changed = True
    card = next(c for c in data["deals"] if c["id"] == "gfebe16ad")
    if card.get("sum") == "Не раскрыта":
        card["sum"] = None
        box = (card.get("proofread_absorbed") or {}).get("sum") or []
        fp = review.fix_fingerprint(None)
        if fp in box:
            box.remove(fp)
        if not box:
            (card.get("proofread_absorbed") or {}).pop("sum", None)
        changed = True
    if changed and write:
        close.DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Уборка после записи: %s" % ("сделана" if changed else "нечего"))


def normalize_answers():
    """Опустевшее поле в базе пишется «—» (4 622 поля «Экономиста» и 2 283
    «Юриста» против двух пустых строк), а читатели местами оставили "".
    Имя покупателя текстом при привязке к профилю не обнуляется вручную —
    его снимает сам `fix_audit_close` (правило «покупатель назван один раз»),
    поэтому такие строки из ответа убираются. Правит ответы на месте и
    повторно ничего не меняет."""
    import glob
    import json
    for path in sorted(glob.glob(str(close.ROOT / "data" / "inbox" / "audit2" / "owner99_out" / "out_*.json"))):
        items = json.loads(Path(path).read_text(encoding="utf-8"))
        out = []
        for it in items:
            field = str(it.get("field") or "")
            if it.get("key") in SKIP_KEYS:
                continue
            if it.get("action") == "fix" and it.get("new_full_text") == "":
                if field == "buyer_name":
                    continue
                if field.startswith(("eco.", "law.")):
                    it["new_full_text"] = "—"
            out.append(it)
        Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    normalize_answers()
    close._linker_key = name_key
    close.readers_rows_still_hold = absorb_readers_rows
    code = close.main("--write" in sys.argv, "owner99_out")
    tidy("--write" in sys.argv)
    print("Строк читателя учтено как переписанные: %d" % len(ABSORBED))
    sys.exit(code)
