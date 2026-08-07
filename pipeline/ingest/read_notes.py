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
(для сырья). Применив, ОБЯЗАТЕЛЬНО вызвать `--consume <id...>` — иначе та
же заметка будет напоминать о себе каждый день.

Запуск:
    python3 pipeline/ingest/read_notes.py                # показать нерешённые
    python3 pipeline/ingest/read_notes.py --consume 56 69 # пометить применёнными
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

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
          'карточка для сырья) — обязательно:')
    print('  python3 pipeline/ingest/read_notes.py --consume %s'
          % ' '.join(str(n['id']) for n in notes))
    return 0


if __name__ == '__main__':
    sys.exit(main())
