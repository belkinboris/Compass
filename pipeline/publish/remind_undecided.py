# -*- coding: utf-8 -*-
"""Напоминание в личку: что показано в консоли и сутки ждет решения (12 ноября 2026).

Владелец: «Отмени правило молчания 1 день что выпускается пост. Теперь если
вдруг мы не отреагировали, то пиши мне и артему в личку, что такой-то пост не
опубликован». С этого дня молчание не выпускает ничего — ни карточку
предпросмотра (approve.py), ни пост об этапе сделки, ни месячную сводку
(send_telegram.py). Чтобы забытое не висело в консоли молча, этот скрипт
находит все, что ждет решения дольше REMIND_HOURS, и пишет каждому из
TELEGRAM_REVIEW_CHAT_IDS (личные чаты владельца и партнера) одно сообщение
списком.

ЧТО СЧИТАЕТСЯ ЖДУЩИМ — ровно то, что планировщики выпуска держат с причиной
«ждет решения» (одно место правды, без своего разбора):
  * карточка: `approve.plan_actions` -> wait, состояние `shown`; отсчет —
    `readiness.hours_pending` (от `pending_since`);
  * этап сделки: `send_telegram.plan_milestones` -> hold «ждет решения»;
    отсчет — `milestone_drafted_at`;
  * сводка: `send_telegram.plan_digest` -> «ждет решения»; отсчет —
    `telegram_digests[<месяц>].drafted_at`.
Решения с сайта (approve.fetch_decisions) учитываются: нажатое, но еще не
примененное не напоминается. С ключом --write без прочитанных решений не
шлем ничего — иначе напомнили бы о том, что уже решено.

ОДНО НАПОМИНАНИЕ НА ЗАПИСЬ В СУТКИ. Отметка «напомнили» — в отдельном
отслеживаемом файле data/inbox/undecided_reminders.json ({ключ: время}),
а не в pending.json или базе: у них свои проверки схемы, а у этой отметки
нет другого смысла. Повтор — не раньше REPEAT_HOURS, пока решения нет;
решенное из файла уходит. Пишет только окно WINDOW_MSK (10:00–21:00 МСК).

Вызывают: pipeline/ingest/sweep.py --send (каждый час) и
pipeline/publish/ship_decisions.py --write — оба коммитят файл отметок.

    python3 pipeline/publish/remind_undecided.py           # сухой прогон
    python3 pipeline/publish/remind_undecided.py --write   # отправить
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)                                   # telegram_endpoint в корне
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import approve                                             # noqa: E402
import send_telegram                                       # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'undecided_reminders.json')
SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
MSK = timezone(timedelta(hours=3))
REMIND_HOURS = approve.REMIND_HOURS        # ждет дольше — напоминаем
REPEAT_HOURS = 23                          # «раз в сутки»: час запаса на сдвиг прогона
WINDOW_MSK = (10, 21)                      # с 10:00 до 21:00 по Москве
MAX_ITEMS = 15                             # длиннее список в одном сообщении не читают

MONTHS = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август',
          'сентябрь', 'октябрь', 'ноябрь', 'декабрь')
MONTHS_GEN = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа',
              'сентября', 'октября', 'ноября', 'декабря')


def private_chats():
    """Личные чаты владельца и партнера — не группа-консоль."""
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',') if x.strip()]


def _parse(stamp):
    try:
        t = datetime.fromisoformat(str(stamp))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def in_window(now):
    hour = now.astimezone(MSK).hour
    return WINDOW_MSK[0] <= hour < WINDOW_MSK[1]


def waiting(data, cards, decisions, now):
    """Все, что показано в консоли и ждет решения: [{key, kind, title, since, link}]."""
    comps = data.get('companies') or {}
    out = []
    _pub, _hold, wait, _drop = approve.plan_actions(cards, decisions, now, comps)
    for card, _why in wait:
        if approve.readiness.state(card, comps) != 'shown':
            continue
        hours = approve.hours_pending(card, now)
        out.append({'key': 'card:%s' % card['id'], 'kind': 'card',
                    'title': str(card.get('title') or card['id']),
                    'since': now - timedelta(hours=hours),
                    'link': '%s/#/preview/%s' % (SITE, card['id'])})
    _send, hold, _disc, _sent = send_telegram.plan_milestones(
        data.get('deals') or [], data.get('telegram_milestones') or {}, decisions, now,
        data.get('telegram_post_state') or {})
    for deal, event, why in hold:
        since = _parse(event.get('milestone_drafted_at'))
        if not since or not str(why).startswith('ждет решения'):
            continue
        out.append({'key': 'milestone:%s' % event['id'], 'kind': 'milestone',
                    'title': str(event.get('headline') or deal.get('title') or event['id']),
                    'since': since, 'link': '%s/#/deal/%s' % (SITE, deal.get('id'))})
    action, key, why, _ids = send_telegram.plan_digest(data, decisions, now)
    if action is None and key and str(why).startswith('ждет решения'):
        since = _parse(((data.get('telegram_digests') or {}).get(key) or {}).get('drafted_at'))
        if since:
            month = MONTHS[int(key[5:7]) - 1]
            out.append({'key': 'digest:%s' % key, 'kind': 'digest',
                        'title': 'итоги месяца за %s %s' % (month, key[:4]),
                        'since': since, 'link': ''})
    return out


def due(items, state, now):
    """Ждут дольше REMIND_HOURS и не напоминались последние REPEAT_HOURS."""
    out = []
    for it in items:
        if (now - it['since']).total_seconds() < REMIND_HOURS * 3600:
            continue
        last = _parse((state or {}).get(it['key']))
        if last and (now - last).total_seconds() < REPEAT_HOURS * 3600:
            continue
        out.append(it)
    return out


def when(t):
    t = t.astimezone(MSK)
    return '%d %s, %02d:%02d МСК' % (t.day, MONTHS_GEN[t.month - 1], t.hour, t.minute)


LEAD = {'card': 'Сделка не опубликована', 'milestone': 'Пост об этапе сделки не опубликован',
        'digest': 'Пост не опубликован'}


def message(items):
    """Одно сообщение по-человечески; несколько ждущих — списком."""
    if len(items) == 1:
        it = items[0]
        text = '%s: %s. Ждет вашего решения в консоли с %s.' % (LEAD[it['kind']], it['title'], when(it['since']))
        return text + ('\n' + it['link'] if it['link'] else '')
    lines = ['Не опубликовано, ждет вашего решения в консоли: %d.' % len(items), '']
    for i, it in enumerate(items[:MAX_ITEMS], 1):
        lines.append('%d. %s: %s. Ждет с %s.' % (i, LEAD[it['kind']], it['title'], when(it['since'])))
        if it['link']:
            lines.append(it['link'])
    if len(items) > MAX_ITEMS:
        lines.append('')
        lines.append('И еще %d — в консоли, кнопка «Что ждет решения».' % (len(items) - MAX_ITEMS))
    return '\n'.join(lines)


def load_state(path=STATE):
    try:
        return json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_state(state, path=STATE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def plan(data, cards, decisions, state, now):
    """(напомнить сейчас, все ждущие, новое состояние без решенного)."""
    items = waiting(data, cards, decisions, now)
    keys = {it['key'] for it in items}
    kept = {k: v for k, v in (state or {}).items() if k in keys}
    return due(items, kept, now), items, kept


def run(write=False, now=None, data_path=DATA, pending_path=PENDING, state_path=STATE,
        fetch=None, sender=None):
    """Код возврата 0 всегда, кроме поломки чтения файлов. `fetch` и `sender`
    подменяют тесты: сеть и Telegram в тестах не трогаются."""
    now = now or datetime.now(timezone.utc)
    data = json.load(open(data_path, encoding='utf-8'))
    cards = (json.load(open(pending_path, encoding='utf-8')).get('cards') or [])
    decisions, handle = (fetch or approve.fetch_decisions)()
    state = load_state(state_path)
    todo, items, kept = plan(data, cards, decisions, state, now)
    print('Ждут решения в консоли: %d, из них дольше %d ч и без напоминания за сутки: %d'
          % (len(items), REMIND_HOURS, len(todo)))
    for it in items:
        print('  %-9s %s — ждет %.0f ч%s' % (it['kind'], it['title'][:90],
                                            (now - it['since']).total_seconds() / 3600,
                                            ' → напомнить' if it in todo else ''))
    if not todo:
        if write and kept != state:
            save_state(kept, state_path)
        return 0
    print('\n' + message(todo))
    chats = private_chats()
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    reason = None
    if not write:
        reason = 'Сухой прогон. Отправка — с ключом --write.'
    elif not in_window(now):
        reason = 'Вне окна %02d:00–%02d:00 МСК — напомним днем.' % WINDOW_MSK
    elif handle is None and fetch is None:
        reason = 'Решения с сайта не прочитаны — не напоминаем, чтобы не написать о решенном.'
    elif not chats:
        reason = 'TELEGRAM_REVIEW_CHAT_IDS не задан — писать некому.'
    elif not token and sender is None:
        reason = 'TELEGRAM_BOT_TOKEN не задан — не отправляю.'
    if reason:
        print('\n' + reason)
        if write and kept != state:
            save_state(kept, state_path)
        return 0
    text = message(todo)
    if sender is None:
        import httpx
        import send_drafts
        client = httpx.Client(timeout=20)

        def sender(chat, body):
            return send_drafts.send_one(client, token, chat, body, None)
    ok = [chat for chat in chats if sender(chat, text)]
    print('Напоминание отправлено: %d из %d личных чатов.' % (len(ok), len(chats)))
    if ok:
        stamp = now.isoformat(timespec='seconds')
        for it in todo:
            kept[it['key']] = stamp
    save_state(kept, state_path)
    return 0


if __name__ == '__main__':
    sys.exit(run('--write' in sys.argv))
