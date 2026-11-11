# -*- coding: utf-8 -*-
"""«АГР Холдинг» (g99f697c1) и Hefei Hengyi (g1953287c): посты вышли нашим текстом,
а не текстом владельца из консоли (11 ноября 2026).

Решения владельца от 10 ноября (20:47–20:48, ответ своим текстом на проект поста)
погасили на сайте без применения (known_issues/publication.md). Отметку
`post_approved` вернули руками, текст — нет: вышел сгенерированный пост. Текст
достаем из истории решений сайта (`/api/moderation/decisions?deal_id=&history=1`),
ставим `post_override` и правим вышедшие сообщения (editMessageText не будит
подписчиков).

    python3 pipeline/archive/2026-11/restore_owner_post_text_2026_11_11.py            # показать
    ... --edit <id>=<main_msg>[,<realty_msg>] ...   # исправить сообщения в каналах
    ... --write                                     # post_override в базу
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), os.path.join(ROOT, 'pipeline', 'ingest')]
import httpx  # noqa: E402
import format_post, send_telegram  # noqa: E402
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
IDS = ('g99f697c1', 'g1953287c')


def owner_text(cid):
    site = (os.environ.get('SITE_URL') or 'https://projectcompass.ru').rstrip('/')
    tok = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET')
    rows = httpx.get(site + '/api/moderation/decisions', params={'token': tok, 'deal_id': cid, 'history': 1},
                     timeout=30).json()['decisions']
    texts = [r['edited_text'] for r in rows if (r.get('edited_text') or '').strip()]
    assert texts, 'у %s нет текста владельца' % cid
    return format_post.owner_text_as_html(texts[-1])


texts = {i: owner_text(i) for i in IDS}
for i, t in texts.items():
    print('==', i, '\n' + t[:200] + '…')
if '--edit' in sys.argv:
    site = send_telegram.site_channels() if hasattr(send_telegram, 'site_channels') else None
    main_chat = send_telegram.channel_address()
    realty = send_telegram.realty_channel_address(site, main_chat)
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    with httpx.Client(timeout=30) as client:
        for arg in sys.argv[sys.argv.index('--edit') + 1:]:
            if arg.startswith('--'):
                break
            cid, ids = arg.split('=')
            ids = [int(x) for x in ids.split(',')]
            for chat, mid in zip((main_chat, realty), ids):
                send_telegram.edit_message(client, os.environ['TELEGRAM_BOT_TOKEN'], chat, mid, texts[cid],
                                           format_post.render_buttons(deals[cid]))
                print('исправлено', cid, chat and str(chat)[:6], mid)
if '--write' in sys.argv:
    data = json.load(open(DATA, encoding='utf-8'))
    for d in data['deals']:
        if d['id'] in IDS:
            assert not d.get('post_override'), d['id']
            d['post_override'] = texts[d['id']]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
