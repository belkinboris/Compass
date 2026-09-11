# -*- coding: utf-8 -*-
"""Повторная отправка 21 старого открытого вопроса — перепроверены, ничего не изменилось.

ЗАЧЕМ. Большая ревизия «Известных проблем» 11 сентября 2026 (пять параллельных
читателей) заново прочитала все 75 записей раздела. 21 из них уже были
отправлены в консоль партиями 1-2 (4 и 7 сентября) — но с тех пор прошла
неделя с лишним новых прогонов, сообщения наверняка погребены под свежими
постами и решениями, а владелец ни разу не ответил. Читатели перепроверили
каждую по источникам заново и не нашли ничего нового к тому, что уже
спрашивали, — вопрос остаётся ровно тем же. Владелец прямо попросил переслать
эти 21 вопроса тоже, с полным описанием кейса.

ЧТО ДЕЛАЕТ СКРИПТ. Берёт готовые вопросы из `send_open_questions.QUESTIONS`
(они уже написаны подробно и по-человечески) по списку из 21 id, добавляет
одну строку о том, что это повтор и что перепроверка сегодня ничего не
изменила, и шлёт тем же путём (`send_drafts.send_one`, тема "decision").
Основной `open_questions_sent.json` не трогает — это не первая отправка, а
явный, разовый повтор по прямой просьбе; свой стейт-файл рядом
(`resend_2026_09_11_state.json`) не даёт продублировать при повторном запуске
скрипта.

Запуск:
    python3 pipeline/resend_open_questions_reconfirmed.py            # сухой прогон
    python3 pipeline/resend_open_questions_reconfirmed.py --write
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import console_topics                                      # noqa: E402
from send_drafts import send_one, PAUSE                    # noqa: E402
from send_open_questions import QUESTIONS, SITE            # noqa: E402

STATE = os.path.join(HERE, 'resend_2026_09_11_state.json')

IDS = [
    'g56342584', 'g404d96eb', 'g560a4b70', 'g75837e8b', 'gbfe2ee65',
    'g2800e337', 'g1c5d636d', 'g83bd07f6', 'g6ad6fe69', 'g9ec93147',
    'g60280ac0', 'g8ce554c5', 'g401b169a', 'gd3f012e4', 'ga4082daa',
    'gb49e3668', 'gc5eb971c', 'gbd3416b4', 'g4165ba00', 'g139db8c2',
    'g7299791f',
]

HEADER = "\n".join([
    "🔁 21 старый вопрос — присылаю ещё раз",
    "",
    "Это те же вопросы, что уходили 4 и 7 сентября: вы на них пока не"
    " ответили, а сообщения наверняка потерялись среди более свежих."
    " Сегодня перечитал каждую карточку и источники заново — ничего нового"
    " к уже написанному не нашлось, вопрос стоит тот же.",
    "",
    "Дальше пойдут 21 сообщение подряд, по одному на карточку. Отвечайте"
    " прямо на нужное — ответ дойдёт до рутины так же, как раньше.",
])


def render(item, number, total):
    return "\n".join([
        "❓ Вопрос %d из %d (повтор) — нужен ваш ответ" % (number, total),
        "[карточка %s] %s" % (item["id"], item["title"]),
        "",
        "Сейчас в базе: " + item["now"],
        "",
        "Что нашли: " + item["found"],
        "",
        "Перепроверено ещё раз 11 сентября 2026 — ничего нового по"
        " сравнению с тем, что уже спрашивал 4-7 сентября, не нашлось.",
        "",
        "Что решить: " + item["ask"],
        "",
        "Карточка: %s/#/deal/%s" % (SITE, item["id"]),
        "Ответьте на это сообщение — ответ дойдёт до рутины.",
    ])


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding='utf-8'))
    return {"sent": {}, "header_sent": False}


def main():
    args = sys.argv[1:]
    write = '--write' in args

    by_id = {q["id"]: q for q in QUESTIONS}
    missing = [i for i in IDS if i not in by_id]
    assert not missing, "нет в QUESTIONS: %s" % missing

    todo_ids = [i for i in IDS if i not in load_state()["sent"]]
    items = [by_id[i] for i in todo_ids]
    total = len(IDS)

    if not items:
        print("Все %d вопросов уже переотправлены." % total)
        return 0
    print("К повторной отправке: %d из %d" % (len(items), total))

    if not write:
        for q in items:
            print("\n" + "-" * 60)
            print(render(q, IDS.index(q["id"]) + 1, total))
        print("\nСухой прогон. Отправить: --write")
        return 0

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = console_topics.console_chats()
    if not token or not chats:
        print("Отправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.")
        return 1

    import httpx
    state = load_state()
    sent = 0
    thread = console_topics.thread_id('decision')
    with httpx.Client(timeout=20) as client:
        if not state.get("header_sent"):
            if all(send_one(client, token, chat, HEADER, None, thread) for chat in chats):
                state["header_sent"] = True
                json.dump(state, open(STATE, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1, sort_keys=True)
                time.sleep(PAUSE)
        for i, q in enumerate(items):
            text = render(q, IDS.index(q["id"]) + 1, total)
            ok = all(send_one(client, token, chat, text, None, thread) for chat in chats)
            if ok:
                state["sent"][q["id"]] = True
                sent += 1
                json.dump(state, open(STATE, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1, sort_keys=True)
            print("  %s %s" % ("отправлено" if ok else "НЕ ДОШЛО", q["id"]))
            if i < len(items) - 1:
                time.sleep(PAUSE)
    print("Отправлено: %d из %d" % (sent, len(items)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
