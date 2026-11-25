# -*- coding: utf-8 -*-
"""Карточка g707211ba (консорциум Тодда Боэли / зарубежные активы «Лукойла»),
сборка 25 ноября 2026: заметка этапа `events[0].note` была первым абзацем
«Коммерсанта» дословно (находки приемки: 20 слов подряд как в источнике,
буква «ё», опечатка издания «Reuterts»). `proofread.py` такую правку не
принимает (меняется написание имени: «Бёли» -> «Боэли», как в «Ведомостях» и
в остальной карточке), `review.py` элемент списка не адресует
(docs/card_editing_scripts.md) — поэтому прямая запись своим текстом по тем
же фактам: о подписании объявил сам Боэли, сделка — обмен бумаг на активы,
для закрытия нужна лицензия OFAC.

Запуск: python3 pipeline/archive/2026-11/fix_g707211ba_event_note_2026_11_25.py --write
"""
import json
import sys

PATH = "static/data/pending.json"
CARD_ID = "g707211ba"
OLD_START = "Американский миллиардер Тодд Бёли заявил, что подписал соглашение с ЛУКОЙЛом"
NEW_NOTE = ("Тодд Боэли объявил, что его консорциум подписал соглашение с «Лукойлом»: "
            "бумаги компании обменивают на ее зарубежные активы. Для закрытия нужна лицензия OFAC.")


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    card = next(c for c in base["cards"] if c["id"] == CARD_ID)
    ev = card["events"][0]
    if ev["note"] == NEW_NOTE:
        print("%s: заметка этапа уже новая — нечего делать." % CARD_ID)
        return
    assert ev["kind"] == "signed" and ev["note"].startswith(OLD_START), "events[0] уже другой: %r" % ev
    ev["note"] = NEW_NOTE
    print("%s: events[0].note -> %s" % (CARD_ID, NEW_NOTE))
    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО.")
    else:
        print("Сухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
