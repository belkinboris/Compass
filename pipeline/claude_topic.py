# -*- coding: utf-8 -*-
"""Тема «Клод» в группе-консоли: забрать сообщения агенту и ответить на них.

Владелец и партнёр пишут в тему «Клод» задачи, правки и вопросы. Сайт ловит
их вебхуком и складывает в свою базу (`_claude_topic_message` в main.py);
рутина «тема Клод» (routines/claude_topic.md) забирает их этим скриптом,
делает работу и отвечает в ту же тему реплаем на каждое сообщение.

Запуск:
    python3 pipeline/claude_topic.py                       # непрочитанные сообщения
    python3 pipeline/claude_topic.py --reply 123 --text "Сделано: ..."
    python3 pipeline/claude_topic.py --reply 123 --text-file ответ.txt [--html]
    python3 pipeline/claude_topic.py --reply 123 --photo shot.png [--caption "..."]
    python3 pipeline/claude_topic.py --consume 5,6,7      # пометить прочитанными

`--reply` — номер СООБЩЕНИЯ в Telegram (поле message_id в выводе), а не id
записи; `--consume` — id записей. Без TELEGRAM_BOT_TOKEN скрипт печатает, что
отправил бы, и ничего не шлёт. Адрес — только группа-консоль: канал
публикации вычёркивается всегда (см. console_topics.channel_ids/is_channel).
"""
import argparse
import json
import os
from datetime import datetime, timezone
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import console_topics                                      # noqa: E402
import site_bridge                                         # noqa: E402
import telegram_endpoint                                   # noqa: E402

KIND = 'claude'
CHUNK = 4000
CAPTION_LIMIT = 1024
DOWNLOADS = os.path.join(ROOT, 'data', 'inbox', 'claude')
# ПАМЯТЬ ТЕМЫ. Каждый прогон рутины — новая сессия, а Telegram отдаёт только
# само сообщение и обрывок того, на что ответили. 19 октября 2026 рутина без
# истории переспросила, что значит «Да», и спорила о продавце, которого
# партнёр назвал двумя сообщениями выше. Журнал входящих и наших ответов
# лежит в git, и перед новыми сообщениями печатается его хвост.
LOG = os.path.join(ROOT, 'data', 'claude_topic_log.jsonl')
LOG_TAIL = 16


def _log_read():
    if not os.path.exists(LOG):
        return []
    out = []
    for line in open(LOG, encoding='utf-8'):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def _log_add(entry):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _log_incoming(messages):
    seen = {e.get('id') for e in _log_read() if e.get('dir') == 'in'}
    for m in messages:
        if m['id'] in seen:
            continue
        _log_add({'dir': 'in', 'id': m['id'], 'message_id': m.get('message_id'),
                  'from': m.get('from_name'), 'at': str(m.get('created_at') or '')[:16],
                  'reply_to_text': (m.get('reply_to_text') or '')[:600],
                  'text': m.get('text') or ('[фото/файл]' if m.get('photo_file_id') or m.get('document_file_id') else '')})


def show_history():
    tail = _log_read()[-LOG_TAIL:]
    if not tail:
        return
    print('=== Переписка в теме до этих сообщений (последние %d записей) ===' % len(tail))
    for e in tail:
        if e.get('dir') == 'in':
            print('[%s] %s (message_id=%s): %s' % (e.get('at'), e.get('from') or '?',
                                                  e.get('message_id'), (e.get('text') or '')[:800]))
        else:
            print('[%s] МЫ, ответ на %s: %s' % (e.get('at'), e.get('reply_to'), (e.get('text') or '')[:800]))
    print('=== конец истории ===\n')


def _bot():
    return os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()


def fetch_inbox(token):
    return site_bridge.get_json('/api/claude/inbox', {'token': token}).get('messages') or []


def consume(token, ids):
    return site_bridge.post_json('/api/claude/inbox/consume',
                                 {'token': token, 'ids': ids}).get('consumed', 0)


def split_text(text, size=CHUNK):
    """Порезать длинный текст на части не длиннее size — по абзацу, строке или
    пробелу, если получится, а не посреди слова."""
    text = text.strip()
    parts = []
    while len(text) > size:
        cut = -1
        for sep in ('\n\n', '\n', ' '):
            cut = text.rfind(sep, 0, size)
            if cut > size // 2:
                break
        if cut <= 0:
            cut = size
        parts.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        parts.append(text)
    return parts


def _target():
    """(чат, тема) консоли. Канал публикации сюда не попадёт никогда."""
    chats = console_topics.console_chats()
    forbidden = console_topics.channel_ids()
    group = None
    for chat in chats:
        if str(chat) in forbidden or console_topics.is_channel(chat):
            continue
        group = chat
        break
    assert group is None or (str(group) not in forbidden and not console_topics.is_channel(group)), \
        'адрес консоли оказался каналом публикации — отправка запрещена'
    return group, console_topics.thread_id(KIND)


def _download(bot, file_id, record_id, hint_name=None):
    """Скачать файл из Telegram в data/inbox/claude/<id>.<ext>; путь или None."""
    import httpx
    r = httpx.post(telegram_endpoint.method_url(bot, 'getFile'), json={'file_id': file_id}, timeout=30)
    data = r.json()
    if not data.get('ok'):
        print('  файл не скачан: %s' % data.get('description'))
        return None
    path = (data.get('result') or {}).get('file_path') or ''
    ext = os.path.splitext(hint_name or path)[1] or '.bin'
    os.makedirs(DOWNLOADS, exist_ok=True)
    local = os.path.join(DOWNLOADS, '%s%s' % (record_id, ext))
    url = '%s/file/bot%s/%s' % (telegram_endpoint.api_root(), bot, path)
    body = httpx.get(url, timeout=60)
    if body.status_code != 200:
        print('  файл не скачан: код %d' % body.status_code)
        return None
    with open(local, 'wb') as fh:
        fh.write(body.content)
    return local


def show(messages):
    bot = _bot()
    if messages:
        show_history()
        _log_incoming(messages)
    print('Непрочитанных сообщений в теме «Клод»: %d' % len(messages))
    for m in messages:
        print('\n--- id=%s  message_id=%s  от %s (%s)  %s' % (
            m['id'], m['message_id'], m.get('from_name') or '?', m.get('from_id'),
            str(m.get('created_at') or '')[:16].replace('T', ' ')))
        if m.get('reply_to_text'):
            print('В ответ на: %s' % m['reply_to_text'][:3000])
        if m.get('text'):
            print(m['text'])
        for key, name in (('photo_file_id', None), ('document_file_id', m.get('document_name'))):
            fid = m.get(key)
            if not fid:
                continue
            what = 'фото' if key == 'photo_file_id' else 'файл %s' % (name or '')
            if not bot:
                print('[%s не скачан: нет TELEGRAM_BOT_TOKEN]' % what)
                continue
            try:
                local = _download(bot, fid, m['id'], name or ('x.jpg' if key == 'photo_file_id' else None))
            except Exception as e:                          # noqa: BLE001
                local = None
                print('  %s не скачан: %s' % (what, e))
            if local:
                print('[%s: %s]' % (what, local))


def _post(method, payload, files=None):
    import httpx
    bot = _bot()
    url = telegram_endpoint.method_url(bot, method)
    if files:
        r = httpx.post(url, data={k: str(v) for k, v in payload.items()}, files=files, timeout=60)
    else:
        r = httpx.post(url, json=payload, timeout=30)
    try:
        data = r.json()
    except ValueError:
        data = {'ok': False, 'description': 'ответ не разобран (код %d)' % r.status_code}
    if not data.get('ok') and payload.get('parse_mode') and "can't parse entities" in str(data.get('description')):
        print('  разметку не приняли — повторяю без неё')
        payload = dict(payload)
        del payload['parse_mode']
        return _post(method, payload, files)
    return data


def reply(message_id, text=None, html=False, photo=None, caption=None):
    chat, thread = _target() if _bot() else (None, None)
    base = {}
    if thread is not None:
        base['message_thread_id'] = thread
    if message_id:
        base['reply_to_message_id'] = int(message_id)
        base['allow_sending_without_reply'] = True
    if html:
        base['parse_mode'] = 'HTML'
    if not _bot():
        print('Нет TELEGRAM_BOT_TOKEN — ничего не отправлено. Отправил бы в тему «Клод» '
              'реплаем на сообщение %s:' % message_id)
        if photo:
            print('[картинка %s] %s' % (photo, caption or ''))
        for part in split_text(text or ''):
            print('---\n' + part)
        return True
    if not chat:
        print('Адреса консоли нет (или он оказался каналом) — ничего не отправлено.')
        note = console_topics.channel_leak_note()
        if note:
            print(note)
        return False
    if thread is None:
        print('Тема «Клод» ещё не закреплена: сообщение уйдёт в общую ленту группы. '
              'Закрепить — /start в теме и кнопка «Назначить эту тему».')
    ok = True
    if photo:
        payload = dict(base, chat_id=chat)
        if caption:
            payload['caption'] = caption[:CAPTION_LIMIT]
        with open(photo, 'rb') as fh:
            data = _post('sendPhoto', payload, files={'photo': (os.path.basename(photo), fh)})
        ok = bool(data.get('ok'))
        print('картинка: %s' % ('отправлена' if ok else 'НЕ ДОШЛА — %s' % data.get('description')))
    for i, part in enumerate(split_text(text or '')):
        payload = dict(base, chat_id=chat, text=part, disable_web_page_preview=True)
        if i or photo:
            # Реплай — только у первой части; остальные идут следом в той же теме.
            payload.pop('reply_to_message_id', None)
            payload.pop('allow_sending_without_reply', None)
        data = _post('sendMessage', payload)
        sent = bool(data.get('ok'))
        ok = ok and sent
        print('часть %d: %s' % (i + 1, 'отправлена' if sent else 'НЕ ДОШЛА — %s' % data.get('description')))
    if ok:
        _log_add({'dir': 'out', 'reply_to': message_id,
                  'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M'),
                  'text': (text or caption or '')[:3000]})
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description='Тема «Клод»: прочитать сообщения и ответить.')
    ap.add_argument('--reply', help='message_id сообщения, на которое отвечаем')
    ap.add_argument('--text')
    ap.add_argument('--text-file')
    ap.add_argument('--html', action='store_true', help='текст с разметкой HTML Telegram')
    ap.add_argument('--photo')
    ap.add_argument('--caption')
    ap.add_argument('--consume', help='id записей через запятую')
    args = ap.parse_args(argv)

    if args.consume:
        ids = [int(x) for x in args.consume.replace(' ', '').split(',') if x]
        token = site_bridge.token()
        if not token:
            print('Нет токена (MODERATION_TOKEN / TELEGRAM_WEBHOOK_SECRET) — пометить нечем.')
            return 1
        try:
            n = consume(token, ids)
        except site_bridge.BridgeUnavailable as e:
            print('Пометить прочитанными не удалось: %s' % e.reason)
            return 1
        print('Помечено прочитанными: %d из %d' % (n, len(ids)))
        return 0

    if args.text or args.text_file or args.photo:
        text = args.text
        if args.text_file:
            with open(args.text_file, encoding='utf-8') as fh:
                text = fh.read()
        if not (text or args.photo):
            print('Пустой ответ — нечего отправлять.')
            return 1
        return 0 if reply(args.reply, text, html=args.html, photo=args.photo,
                          caption=args.caption) else 1

    token = site_bridge.token()
    if not token:
        print('Нет токена (MODERATION_TOKEN / TELEGRAM_WEBHOOK_SECRET) — сайт не ответит.')
        return 1
    try:
        messages = fetch_inbox(token)
    except site_bridge.BridgeUnavailable as e:
        print('Сообщения забрать не удалось: %s' % e.reason)
        return 1
    show(messages)
    return 0


if __name__ == '__main__':
    sys.exit(main())
