# -*- coding: utf-8 -*-
"""Приток, шаг 7: применить решения владельца и партнёра к черновикам.

ОТКУДА РЕШЕНИЯ. Кнопки и ответы в Telegram приходят вебхуком на сайт, сайт
пишет их в таблицу; этот скрипт забирает их по публичному API
(`/api/moderation/decisions?token=…`) — потому что напрямую до базы сайта из
контейнера рутины не достать: она в приватной сети хостинга.

ТРИ ИСХОДА ПО КАЖДОМУ ЧЕРНОВИКУ:
  * «Опубликовать» (или ответ с текстом) — карточка переносится в базу; если
    в ответе был текст, он ложится в `post_override` и канал получит именно
    его, а не автоформат;
  * «Придержать» — черновик остаётся в pending с пометкой `held`, больше не
    рассылается и не публикуется по таймауту; снять пометку — руками;
  * МОЛЧАНИЕ СУТКИ — публикуем как есть. Немой шаг, который держит весь поток,
    у нас уже был (тормоз E9), второй раз те же грабли не берём. Про правило
    молчания написано в самом сообщении-черновике.

Запуск:
    python3 pipeline/ingest/approve.py            # сухой прогон
    python3 pipeline/ingest/approve.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SILENCE_HOURS = 24


def fetch_decisions():
    """Решения с сайта. Сайт недоступен — вернём пусто и скажем об этом:
    таймауты всё равно применимы, а решения дождутся следующего прогона."""
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if not token:
        print('MODERATION_TOKEN/TELEGRAM_WEBHOOK_SECRET не заданы — решения не прочитать.')
        return [], None
    try:
        import httpx
        r = httpx.get('%s/api/moderation/decisions' % site, params={'token': token}, timeout=20)
        if r.status_code != 200:
            print('Сайт ответил %s на запрос решений — работаем без них.' % r.status_code)
            return [], None
        return r.json().get('decisions', []), (site, token)
    except Exception as e:
        print('Решения недоступны (%s) — работаем без них.' % e)
        return [], None


def consume(handle, ids):
    if not (handle and ids):
        return
    site, token = handle
    try:
        import httpx
        httpx.post('%s/api/moderation/decisions/consume' % site,
                   json={'token': token, 'ids': ids}, timeout=20)
    except Exception as e:
        print('Не удалось пометить решения применёнными (%s) — не страшно: '
              'повторное применение идемпотентно.' % e)


def hours_pending(card, now):
    try:
        since = datetime.fromisoformat(str(card.get('pending_since')))
    except ValueError:
        return 0.0
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return (now - since).total_seconds() / 3600.0


def plan_actions(cards, decisions, now):
    """(публикуем, придерживаем, ждём) — чистая функция, её держат тесты."""
    by_deal = {}
    for d in decisions:                      # позднее решение перекрывает раннее
        by_deal[d['deal_id']] = d
    publish, hold, wait = [], [], []
    for card in cards:
        decision = by_deal.get(card['id'])
        if decision and decision['verdict'] == 'approve':
            publish.append((card, decision.get('edited_text'), 'решение: опубликовать'))
        elif decision:
            hold.append((card, 'решение: придержать'))
        elif card.get('held'):
            wait.append((card, 'придержана ранее — ждёт ручного решения'))
        elif card.get('draft_sent') and hours_pending(card, now) >= SILENCE_HOURS:
            publish.append((card, None, 'молчание %d ч — публикуем как есть' % SILENCE_HOURS))
        else:
            wait.append((card, 'ждём решения (%.0f ч из %d)' % (hours_pending(card, now), SILENCE_HOURS)))
    return publish, hold, wait


def main(write=False):
    if not os.path.exists(PENDING):
        print('Черновиков нет.')
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))
    decisions, handle = fetch_decisions()
    now = datetime.now(timezone.utc)
    publish, hold, wait = plan_actions(pending['cards'], decisions, now)

    for card, override, why in publish:
        print('  ПУБЛИКУЕМ   %-11s %s%s' % (card['id'], str(card.get('title'))[:56],
                                            ' [текст поста заменён]' if override else ''))
        print('              %s' % why)
    for card, why in hold:
        print('  ПРИДЕРЖАНА  %-11s %s' % (card['id'], why))
    for card, why in wait:
        print('  ЖДЁТ        %-11s %s' % (card['id'], why))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']}
    fresh = []
    for card, override, _why in publish:
        assert card['id'] not in existing, 'карточка %s уже в базе' % card['id']
        clean = {k: v for k, v in card.items()
                 if k not in ('pending_since', 'draft_sent', 'held')}
        if override:
            clean['post_override'] = override
        data['deals'].append(clean)
        fresh.append(clean)
    for card, _why in hold:
        card['held'] = True
    published_ids = {c['id'] for c, _o, _w in publish}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in published_ids]

    if fresh:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    consume(handle, [d['id'] for d in decisions])
    print('Опубликовано: %d. В базе: %d. Осталось в предпросмотре: %d.'
          % (len(fresh), len(data['deals']), len(pending['cards'])))
    if fresh:
        # Личные уведомления по подпискам — как раньше делал promote.notify.
        import promote
        promote.notify(fresh, data['companies'])
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
