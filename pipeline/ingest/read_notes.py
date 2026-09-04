# -*- coding: utf-8 -*-
"""Приток: прочитать заметки партнёров и не дать им потеряться.

ЧТО СЛОМАНО БЫЛО. Ответ текстом на сообщение `[карточка id]` или
`[сырьё draft_id]` в консоли пишется вердиктом 'note' и API честно отдаёт его
рутине — но НИ ОДИН шаг рутины его не читал. Бот отвечал «Заметка записана —
рутина применит её через review.py», а на самом деле approve.py заметки
НАРОЧНО не потребляет (комментарий в его коде: «их читает суточная рутина
притока»), и в самой суточной рутине не было ни строчки, которая бы их
забирала. 7 августа партнёр оставил 4 заметки за сутки — ни одна не была
прочитана, пока не спросил владелец.

ЧТО ДЕЛАЕТ ЭТОТ СКРИПТ. Забирает нерешённые заметки, для каждой печатает:
  * текст заметки и кто её оставил;
  * id, на который она отвечает — карточка (база/pending) или сырьё
    (последний известный черновик с таким draft_id, если ещё лежит в hold);
  * если это карточка — её текущие поля, чтобы было видно, что уже известно.
Это ЧТЕНИЕ, не применение: что означает заметка и как её перенести в поля —
решает читающий (человек или модель в рутине), потом пишет строку в
`pipeline/ingest/review.py` (для существующей карточки) или строит новую
карточку тем же путём, что `approve.py` строит её для кнопки «в работу»
(для сырья). Применив, ОБЯЗАТЕЛЬНО ответить владельцу РЕПЛАЕМ на то же сообщение
(`--reply <id> "текст"` — раздел C MILESTONES_BRIEF.md, 22 августа: до этого
заметка получала мгновенное «принята» и тишину навсегда, второй человек в
группе не видел, что рутина вообще что-то сделала) и вызвать
`--consume <id...>` — иначе та же заметка будет напоминать о себе каждый день.

Запуск:
    python3 pipeline/ingest/read_notes.py                    # показать нерешённые
    python3 pipeline/ingest/read_notes.py --reply 56 "Текст ответа партнёру"
    python3 pipeline/ingest/read_notes.py --consume 56 69     # пометить применёнными
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)                                  # telegram_endpoint в корне
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))        # console_topics

import console_topics                                      # noqa: E402
import telegram_endpoint                                  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')


def _site_and_token():
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    return site, token


def fetch_notes():
    import httpx
    site, token = _site_and_token()
    if not token:
        print('TELEGRAM_WEBHOOK_SECRET/MODERATION_TOKEN не заданы — заметки не прочитать.')
        return []
    r = httpx.get('%s/api/moderation/decisions' % site, params={'token': token}, timeout=20)
    if r.status_code != 200:
        print('Сайт ответил %s на запрос решений.' % r.status_code)
        return []
    return [d for d in r.json().get('decisions', []) if d['verdict'] == 'note']


def consume(ids):
    import httpx
    site, token = _site_and_token()
    if not (token and ids):
        return
    httpx.post('%s/api/moderation/decisions/consume' % site,
              json={'token': token, 'ids': ids}, timeout=20)


def send_reply(note_id, text):
    """Ответить РЕПЛАЕМ на то же сообщение, где оставлена заметка —
    `chat_id`/`reply_message_id` записаны вебхуком (`main.py`) при получении
    заметки. Заметка уже `--consume`д (её нет среди непрочитанных) — это не
    сбой: значит, ответ на неё уже отправлялся раньше, вызывать второй раз
    незачем."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        print('TELEGRAM_BOT_TOKEN не задан — ответ не отправлен.')
        return False
    note = next((n for n in fetch_notes() if n['id'] == note_id), None)
    if not note:
        print('Заметка %d не среди непрочитанных — уже отвечена и применена (--consume)?' % note_id)
        return False
    if not (note.get('chat_id') and note.get('reply_message_id')):
        print('У заметки %d нет chat_id/reply_message_id — отправить ответ некуда.' % note_id)
        return False
    import httpx
    body = {
        'chat_id': note['chat_id'], 'text': text,
        'reply_to_message_id': note['reply_message_id'],
        'disable_web_page_preview': True,
    }
    # Заметка всегда рождена в теме «Подтверждение постов» (карточка/сырьё/
    # ИНН) — `reply_to_message_id` сам по себе тему не выводит, Telegram
    # требует message_thread_id явно.
    thread = console_topics.thread_id('decision')
    if thread:
        body['message_thread_id'] = thread
    r = httpx.post(telegram_endpoint.method_url(bot_token, 'sendMessage'), json=body, timeout=20)
    if r.status_code == 200 and r.json().get('ok'):
        print('Ответ на заметку %d отправлен.' % note_id)
        return True
    print('Не удалось отправить ответ на заметку %d: %s' % (note_id, r.text[:200]))
    return False


def latest_draft(draft_id):
    """Последний известный черновик с этим draft_id среди hold-файлов, если
    ещё не был переупакован (draft_id меняется при пересборке — см. urок про
    память по заголовку, а не по id)."""
    if not os.path.isdir(HOLD_DIR):
        return None
    for name in sorted(os.listdir(HOLD_DIR), reverse=True):
        if not name.endswith('.json'):
            continue
        for d in json.load(open(os.path.join(HOLD_DIR, name), encoding='utf-8')).get('drafts', []):
            if str(d.get('draft_id')) == str(draft_id):
                return d
    return None


def main():
    if '--reply' in sys.argv:
        i = sys.argv.index('--reply')
        rest = sys.argv[i + 1:]
        assert rest, '--reply требует id и текст ответа: --reply 56 "текст"'
        note_id = int(rest[0])
        text = ' '.join(rest[1:]).strip()
        assert text, '--reply требует текст ответа: --reply %d "текст"' % note_id
        ok = send_reply(note_id, text)
        return 0 if ok else 1
    if '--consume' in sys.argv:
        ids = [int(x) for x in sys.argv[sys.argv.index('--consume') + 1:]]
        consume(ids)
        print('Помечено применёнными: %s' % ids)
        return 0

    notes = fetch_notes()
    if not notes:
        print('Непрочитанных заметок нет.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    cards = {d['id']: d for d in data['deals']}
    cards.update({c['id']: c for c in pending['cards']})

    print('Непрочитанных заметок: %d\n' % len(notes))
    for n in notes:
        print('=' * 60)
        print('id решения: %d | оставил: %s | %s' % (n['id'], n['decided_by'], n['created_at']))
        print('текст: %s' % n.get('edited_text'))
        if not (n.get('chat_id') and n.get('reply_message_id')):
            print('  (нет chat_id/reply_message_id — заметка старая, ответить реплаем на неё нельзя)')
        target = n['deal_id']
        if target in cards:
            card = cards[target]
            print('отвечает на КАРТОЧКУ %s: %s' % (target, card.get('title')))
            print('  сейчас: ind=%r sum=%r seller=%r buyer_name=%r asset=%r'
                  % (card.get('ind'), card.get('sum'), card.get('seller'),
                     card.get('buyer_name'), card.get('asset')))
        else:
            draft = latest_draft(target)
            if draft:
                print('отвечает на СЫРЬЁ %s: %s' % (target, draft.get('title')))
                print('  причины: %s' % draft.get('hold_reasons'))
                print('  источник: %s' % draft.get('src'))
            else:
                print('отвечает на %s — ни карточки, ни черновика с таким id не '
                      'нашлось (id сырья мог смениться при пересборке)' % target)
        print()
    print('После того как правки внесены (review.py FIXES для карточки, новая '
          'карточка для сырья) — ОБЯЗАТЕЛЬНО ответить по каждой заметке реплаем '
          '(что сделали, что нашли, с чем не согласны — честно и коротко), потом --consume:')
    for n in notes:
        print('  python3 pipeline/ingest/read_notes.py --reply %d "..."' % n['id'])
    print('  python3 pipeline/ingest/read_notes.py --consume %s'
          % ' '.join(str(n['id']) for n in notes))
    return 0


if __name__ == '__main__':
    sys.exit(main())
