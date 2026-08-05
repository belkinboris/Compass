#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Зарегистрировать вебхук бота — иначе личные уведомления не подключаются.

ЧТО БЫЛО СЛОМАНО. Привязка Telegram к аккаунту устроена так: кабинет просит
`/api/notification-preferences/telegram-link`, получает ссылку вида
`t.me/<бот>?start=kompas_<токен>`, человек жмёт «Запустить», Telegram шлёт
боту сообщение `/start kompas_<токен>`, и обработчик
`/api/telegram/webhook/<секрет>` связывает chat_id с пользователем. Вся
цепочка написана и работает — кроме одного: НИКТО никогда не говорил
Telegram, куда слать обновления. Во всём коде не было вызова `setWebhook`.
Без него человек нажимал «Подключить», уходил в бота, жал «Запустить» — и
ничего не происходило: ошибки нет, экран прежний, канал не подключён.
Ровно тот случай, когда отсутствие ошибки читается как успех.

ПОЧЕМУ ОТДЕЛЬНЫМ ШАГОМ, А НЕ ПРИ СТАРТЕ ПРИЛОЖЕНИЯ. Регистрация вебхука —
разовое действие на окружение, а не на каждый запуск процесса: на старте
она била бы в Telegram при каждом деплое и при каждом перезапуске, а с
боевого хоста (Timeweb, РФ) соединение с `api.telegram.org` даёт заметную
долю отказов — падение на старте из-за недоступности стороннего сервиса
уронило бы сайт целиком. Поэтому шаг отдельный, ручной и с честным отчётом.

ЧТО НУЖНО В ОКРУЖЕНИИ:
    TELEGRAM_BOT_TOKEN       — тот же токен, что у публикации в канал
    TELEGRAM_WEBHOOK_SECRET  — секрет в пути вебхука (его проверяет main.py)
    APP_BASE_URL             — адрес сайта, куда Telegram будет стучаться
    TELEGRAM_BOT_USERNAME    — @имя бота; без него кабинет не покажет кнопку

Запуск:
    python3 pipeline/publish/setup_telegram_webhook.py          # что стоит сейчас
    python3 pipeline/publish/setup_telegram_webhook.py --write  # зарегистрировать
    python3 pipeline/publish/setup_telegram_webhook.py --delete # снять вебхук
"""
import os
import sys

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import telegram_endpoint  # noqa: E402

# Боту нужны два события: сообщение («/start kompas_<токен>» для привязки
# аккаунта, а с 5 августа ещё и ответ на черновик поста с правкой текста) и
# callback_query (кнопки «Опубликовать»/«Придержать» под черновиком). Забыть
# callback_query — значит зарегистрировать вебхук, на который кнопки молча не
# доходят: Telegram их просто не шлёт, если тип не в списке, а сообщение
# «зарегистрировано» при этом печатается как успех.
ALLOWED_UPDATES = ['message', 'callback_query']


def env(name):
    return (os.environ.get(name) or '').strip()


def webhook_url():
    base = env('APP_BASE_URL') or 'https://projectcompass.ru'
    return '%s/api/telegram/webhook/%s' % (base.rstrip('/'), env('TELEGRAM_WEBHOOK_SECRET'))


def call(token, method, **payload):
    response = httpx.post(telegram_endpoint.method_url(token, method), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def show(info):
    """Печатаем то, что Telegram думает о нас сам, — включая свои жалобы."""
    result = info.get('result') or {}
    current = result.get('url') or ''
    print('Сейчас зарегистрировано: %s' % (current or '— ничего —'))
    if result.get('pending_update_count'):
        print('  необработанных обновлений: %d' % result['pending_update_count'])
    if result.get('last_error_message'):
        print('  последняя ошибка доставки: %s' % result['last_error_message'])
        print('  (это жалоба Telegram на НАШ адрес: сайт не ответил или ответил ошибкой)')
    return current


def main(argv):
    token = env('TELEGRAM_BOT_TOKEN')
    if not token:
        print('TELEGRAM_BOT_TOKEN не задан — ничего не делаем и не притворяемся, '
              'что сделали.')
        return 1

    missing = [n for n in ('TELEGRAM_WEBHOOK_SECRET', 'TELEGRAM_BOT_USERNAME') if not env(n)]
    if missing:
        print('Не заданы: %s' % ', '.join(missing))
        print('  без TELEGRAM_WEBHOOK_SECRET обработчик вебхука отвечает 404 на всё,')
        print('  без TELEGRAM_BOT_USERNAME кабинет не покажет кнопку «Подключить».')
        if '--write' in argv:
            return 1

    try:
        current = show(call(token, 'getWebhookInfo'))
    except httpx.HTTPError as exc:
        print('Telegram недоступен: %s' % exc)
        print('  С боевого хоста это ожидаемо без релея — см. TELEGRAM_API_BASE.')
        return 1

    if '--delete' in argv:
        print('Снимаем вебхук.')
        print(call(token, 'deleteWebhook'))
        return 0

    wanted = webhook_url()
    print('Нужный адрес:      %s' % wanted)
    if current == wanted:
        print('Совпадает — регистрировать нечего.')
        return 0
    if '--write' not in argv:
        print('Сухой прогон. Регистрация — с ключом --write.')
        return 0

    answer = call(token, 'setWebhook', url=wanted, allowed_updates=ALLOWED_UPDATES,
                  drop_pending_updates=True)
    print('Ответ Telegram: %s' % answer)
    # Не верим собственному «ok»: перечитываем состояние у Telegram.
    if show(call(token, 'getWebhookInfo')) != wanted:
        print('ВНИМАНИЕ: после записи Telegram показывает другой адрес — не сработало.')
        return 1
    print('Готово: привязка Telegram к аккаунту теперь может завершиться.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
