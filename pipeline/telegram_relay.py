# -*- coding: utf-8 -*-
"""Аварийный мост: забрать обновления у Telegram и передать их сайту.

ЗАЧЕМ. Бывает состояние, в котором Telegram не может достучаться до нашего
сайта, а мы можем: 7 сентября 2026 наш POST в адрес вебхука отвечал за 0,9 с
кодом 200, вызов Bot API — за 0,2 с, а `getWebhookInfo` в ту же секунду
показывал `Connection timed out` и держал в очереди нажатия владельца. Сайт
жив и быстр — до него не доходит Telegram (нестабильность связи Timeweb ↔
Telegram, см. telegram_endpoint.py).

Постоянное лекарство — опрос внутри самого сайта (`_poll_telegram_updates` в
main.py): весь обмен идёт исходящим путём, где связь работает. Но пока новая
сборка не доехала, консоль остаётся глухой, а человек жмёт кнопку в третий
раз. Этот скрипт закрывает разрыв ровно тем же приёмом, только снаружи: он
забирает обновления `getUpdates` и отправляет каждое в наш же вебхук обычным
POST — то есть в ту сторону, которая работает.

ЧЕМ ЭТО ОПАСНО И ЧТО СДЕЛАНО. Telegram не отдаёт обновления, пока
зарегистрирован вебхук, поэтому скрипт его снимает. Если после этого просто
закончиться, консоль останется без обоих входов — ровно та авария, что уже
случилась в тот же вечер. Поэтому вебхук ВОЗВРАЩАЕТСЯ при любом выходе:
по времени, по Ctrl-C, по исключению.

Запуск:
    python3 pipeline/telegram_relay.py --minutes 30
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ALLOWED = ['message', 'channel_post', 'edited_channel_post',
           'callback_query', 'my_chat_member']


def call(token, method, **payload):
    req = urllib.request.Request(
        'https://api.telegram.org/bot%s/%s' % (token, method),
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return json.load(e)
        except Exception:                                   # noqa: BLE001
            return {'ok': False, 'description': 'HTTP %s' % e.code}


def deliver(site, secret, update):
    req = urllib.request.Request(
        '%s/api/telegram/webhook/%s' % (site.rstrip('/'), secret),
        data=json.dumps(update).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--minutes', type=float, default=30)
    args = p.parse_args()

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET', '').strip()
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru')
    if not token or not secret:
        print('Нужны TELEGRAM_BOT_TOKEN и TELEGRAM_WEBHOOK_SECRET.')
        return 1

    hook = '%s/api/telegram/webhook/%s' % (site.rstrip('/'), secret)
    print('Снимаю вебхук, чтобы Telegram отдал накопленное...')
    call(token, 'deleteWebhook')
    offset, delivered, deadline = None, 0, time.time() + args.minutes * 60
    try:
        while time.time() < deadline:
            body = {'timeout': 20, 'allowed_updates': ALLOWED}
            if offset is not None:
                body['offset'] = offset
            answer = call(token, 'getUpdates', **body)
            if not answer.get('ok'):
                print('  getUpdates отказал: %s' % answer.get('description'))
                time.sleep(3)
                continue
            for update in answer.get('result') or []:
                offset = int(update.get('update_id', 0)) + 1
                what = ('нажатие кнопки' if update.get('callback_query')
                        else 'сообщение' if update.get('message') else 'служебное')
                try:
                    code = deliver(site, secret, update)
                    delivered += 1
                    print('  передано сайту (%s): %s -> %s' % (what, update.get('update_id'), code))
                except Exception as exc:                    # noqa: BLE001
                    print('  сайт не принял %s: %s' % (update.get('update_id'), exc))
    finally:
        print('Возвращаю вебхук — иначе консоль осталась бы без входа.')
        back = call(token, 'setWebhook', url=hook, allowed_updates=ALLOWED,
                    drop_pending_updates=False, max_connections=40)
        print('  setWebhook:', back.get('description') or back)
    print('Передано обновлений: %d.' % delivered)
    return 0


if __name__ == '__main__':
    sys.exit(main())
