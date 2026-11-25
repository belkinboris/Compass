# -*- coding: utf-8 -*-
"""events[0].note карточки g707211ba (консорциум Тодда Боэли / ЛУКОЙЛ, еще в
static/data/pending.json) почти дословно повторяло абзац «Ъ» (цепочка от 20
слов подряд), несло опечатку источника «Reuterts» и имя «Бёли» с буквой «ё».
Текст переписан своими словами по тем же фактам (review.py эту часть
карточки не трогает — `events.0.note` читается как ключ словаря, не как
путь; правка поля из списка — одноразовый скрипт, docs/card_editing_scripts.md).

Запуск:
    python3 pipeline/fix_g707211ba_events_note.py            # сухой прогон
    python3 pipeline/fix_g707211ba_events_note.py --write    # запись
"""
import json
import sys

PATH = "static/data/pending.json"
ID = "g707211ba"

OLD = ("Американский миллиардер Тодд Бёли заявил, что подписал соглашение с ЛУКОЙЛом о "
       "создании консорциума, передает Reuterts. Структура создана для приобретения "
       "международных энергетических активов российской нефтяной компании.")
NEW = ("Американский миллиардер Тодд Боэли сообщил о подписании соглашения с ЛУКОЙЛом от "
       "имени консорциума из четырех участников — самого Боэли (глава холдинга Eldridge), "
       "государственной корпорации DFC, банка Xtellus Partners и эмиратской Catena "
       "Investment Holding. Консорциум получит зарубежные энергетические активы ЛУКОЙЛа в "
       "обмен на его собственные акции, которые ранее выкупил у западных инвесторов.")


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {c["id"]: c for c in base["cards"]}
    card = by_id[ID]
    assert card["events"][0]["note"] == OLD, "events[0].note уже другой — уже правили?"
    card["events"][0]["note"] = NEW
    print(f"{ID}: events[0].note переписан своими словами (без «ё», без опечатки «Reuterts»)")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
