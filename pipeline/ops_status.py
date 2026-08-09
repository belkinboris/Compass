# -*- coding: utf-8 -*-
"""Короткая строка «рутина проверила и вот что увидела» в консоль основателей.

ЗАЧЕМ. До 9 августа рутины писали в Telegram, только когда есть ЧТО
показать (новая карточка, пост, решение), — а «прогон был, ничего не
нашлось» и «прогон не состоялся вовсе» снаружи выглядели ОДИНАКОВО:
молчанием. Так суточный приток пропал из расписания на несколько дней, и
никто не заметил, пока владелец сам не спросил «почему нет новых сделок».
Теперь каждая из трёх рутин («приток», «публикация», «качество») в конце
ЛЮБОГО прогона — успешного, пустого или сорвавшегося — присылает сюда одну
строку статуса: не решение, не кнопку, а факт «я проверила, вот что нашла».

Отдельно от PushNotification (телефон, только настоящие сбои) — этот канал
для отчётов «всё штатно» тоже, чтобы очередная неделя тишины не была
неотличима от очередной недели без новостей на рынке.

Запуск:
    python3 pipeline/ops_status.py "приток: 32 кандидата, 0 новых, сеть ок"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import telegram_endpoint                                  # noqa: E402


def post_status(client, token, chat, text):
    """(отправлено?, причина отказа). Сеть/сервис недоступны — не бросаем:
    статус — это забота, а не критичный шаг, который должен ронять рутину."""
    try:
        r = client.post(telegram_endpoint.method_url(token, 'sendMessage'),
                         json={'chat_id': chat, 'text': text,
                               'disable_web_page_preview': True})
        body = r.json()
    except Exception as e:                                 # noqa: BLE001
        return False, '%s: %s' % (type(e).__name__, e)
    if body.get('ok'):
        return True, None
    return False, body.get('description') or str(body)


def main(argv):
    text = ' '.join(argv).strip()
    if not text:
        print('Нужен текст статуса аргументом.')
        return 1
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = os.environ.get('TELEGRAM_REVIEW_GROUP_ID')
    if not token or not chat:
        print('TELEGRAM_BOT_TOKEN/TELEGRAM_REVIEW_GROUP_ID не заданы — '
              'статус не отправлен, только в консоль прогона: %s' % text)
        return 1
    import httpx
    with httpx.Client(timeout=20) as client:
        ok, why = post_status(client, token, chat, text)
    if not ok:
        print('Статус не ушёл (%s): %s' % (why, text))
        return 1
    print('Статус отправлен в консоль.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
