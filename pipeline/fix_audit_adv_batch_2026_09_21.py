# -*- coding: utf-8 -*-
"""«Консультанты» (law.adv) несёт финансовых советников — партия по law.adv
(аудит 13 сентября). law.adv отведено под ЮРИДИЧЕСКИХ консультантов;
типовой промах — организатор/финансовый консультант/брокер по недвижимости
записан туда же, притом чаще всего тот же факт уже верно стоит в
eco.finadv (просто задвоен), реже — eco.finadv пуст и факт нужно туда
перенести, а не выбросить. Все 17 находок этого поля свободны от чтения
(law.adv почти не трогали правки FIXES).

    python3 pipeline/fix_audit_adv_batch_2026_09_21.py
    python3 pipeline/fix_audit_adv_batch_2026_09_21.py --write
"""
import json
import sys

DATA = "/home/user/Compass/static/data/deals_promoted.json"


def keep_entries(adv, drop_names):
    return [e for e in adv if e[1] not in drop_names]


def main(write: bool) -> int:
    data = json.load(open(DATA, encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    log = []

    # --- удаление: факт уже верно стоит в eco.finadv, law.adv — дубль ---
    REMOVALS = [
        ("g34b9af03", {"Сбербанк"}),
        ("ga218f75c", {"Unicorn"}),
        ("g7299791f", {"Strategy Partners"}),
        ("g8e9d37ba", {"Astoria Capital"}),
        ("gdab53817", {"BITL"}),
        ("g016f1b13", {"IBC Real Estate"}),
        ("gb1cacbc1", {"«Старт Капитал», Сбербанк, Тинькофф-банк"}),
        ("g14356b25", {"АО ИФК «Солид»"}),
        ("g64a94e27", {"Aspring Capital"}),
    ]
    for cid, names in REMOVALS:
        card = cards[cid]
        adv = card["law"]["adv"]
        new_adv = keep_entries(adv, names)
        assert len(new_adv) == len(adv) - len(names), \
            "%s: не нашлась запись для удаления (%s)" % (cid, names)
        log.append("%s: law.adv — удалена запись %s (дубль eco.finadv)" % (cid, names))
        if write:
            card["law"]["adv"] = new_adv

    # gd01de1ad: обе записи — неподтверждённые комментаторы, не консультанты.
    gd = cards["gd01de1ad"]
    assert len(gd["law"]["adv"]) == 2
    log.append("gd01de1ad: law.adv — очищено целиком (обе записи — комментаторы, не консультанты)")
    if write:
        gd["law"]["adv"] = []

    # --- перенос записи целиком в eco.finadv (там пусто или ложный плейсхолдер) ---
    MOVES_TO_FINADV = [
        ("gd3769bb9", "Advance Capital",
         "Advance Capital на своём сайте называет себя эксклюзивным "
         "финансовым консультантом продавца (Е-ПРОМ) в сделке по продаже "
         "49,99% долей фонду «ВИМ Инвестиции»."),
        ("technored", "BSF Partners",
         "TECHNORED на своём сайте называет инвестбанк BSF Partners "
         "участником организации сделки с ГК «Вартон»."),
        ("g9f6fe860", "Роман Муразанов",
         "Финансовый консультант — Роман Муразанов (бывший глава REG.RU)."),
        ("gfa0fe27a", "CORE.XP",
         "CORE.XP выступила консультантом сделки; представитель компании "
         "от комментариев отказался."),
    ]
    for cid, name, finadv_text in MOVES_TO_FINADV:
        card = cards[cid]
        adv = card["law"]["adv"]
        new_adv = keep_entries(adv, {name})
        assert len(new_adv) == len(adv) - 1, "%s: не нашлась запись %s" % (cid, name)
        cur_finadv = card["eco"].get("finadv")
        log.append("%s: law.adv → eco.finadv (%s), было «%s»" % (cid, name, cur_finadv))
        if write:
            card["law"]["adv"] = new_adv
            card["eco"]["finadv"] = finadv_text

    # c7996afb5: law.adv пуст, а LECAP/FOCUS Management прямо названы
    # консультантами в extra/eco.context.
    c = cards["c7996afb5"]
    assert c["law"]["adv"] == []
    log.append("c7996afb5: law.adv заполнен (LECAP, УК FOCUS Management)")
    if write:
        c["law"]["adv"] = [
            ["Юридический консультант", "LECAP",
             "Сопровождал сделку со структурными облигациями, привязанными "
             "к обыкновенным акциям."],
            ["Консультант", "УК FOCUS Management",
             "Сопровождала сделку со структурными облигациями, привязанными "
             "к обыкновенным акциям."],
        ]

    # cf2375bf5: заметка O2 Consulting несёт факты сделки, дословно
    # дублирующие eco.rationale — оставляем только роль консультанта.
    cf = cards["cf2375bf5"]
    adv = cf["law"]["adv"]
    assert len(adv) == 1 and adv[0][1] == "O2 Consulting"
    old_note = adv[0][2]
    assert old_note == ("O2 Consulting — за покупателя; более 850 тыс. м² "
                         "застройки, земельный банк «Брусники» в Москве "
                         "вырос более чем в 2,5 раза")
    log.append("cf2375bf5: law.adv — заметка O2 Consulting обрезана до роли (факты сделки уже в eco.rationale)")
    if write:
        cf["law"]["adv"] = [["Юридический консультант", "O2 Consulting", "За покупателя."]]

    print("Записей: %d" % len(log))
    for line in log:
        print("   " + line)
    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
