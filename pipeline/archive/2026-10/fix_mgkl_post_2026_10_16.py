"""Пост МГКЛ (g0158e326, сообщение 204 в канале): владелец 16 октября 2026 —
«Какие собеседники» про «Какая доля может достаться инвестору, собеседники не
раскрыли» в строке «Предмет». Поле карточки очищено
(`fixes/mgkl_tone_2026_10_16.py`); `post_snapshot` предмет не помнит, поэтому
рутина пост не правит — правится здесь. `editMessageText` подписчиков не
будит. Без `--edit` — сухой прогон."""
import json, os, sys
sys.path.insert(0, 'pipeline/publish'); sys.path.insert(0, 'pipeline')
import format_post, send_telegram  # noqa: E402
import httpx  # noqa: E402
DATA, ID, MSG = 'static/data/deals_promoted.json', 'g0158e326', 204

data = json.load(open(DATA, encoding='utf-8'))
deal = next(d for d in data['deals'] if d['id'] == ID)
assert data['telegram_posts'].get(ID) == MSG
assert ID not in (data.get('telegram_posts_realty') or {})
new = format_post.render(deal, data['companies'])
assert 'собеседник' not in new and 'Крупный инвестор обсуждает вход в капитал МГКЛ' in new, new[:200]
buttons = format_post.render_buttons(deal)
print(new); print(buttons)
if '--edit' in sys.argv:
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat = send_telegram.channel_address()
    with httpx.Client(timeout=30) as client:
        print(send_telegram.edit_message(client, token, chat, MSG, new, buttons))
    print('сообщение', MSG, 'исправлено')
    raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(raw)
    next(d for d in fresh['deals'] if d['id'] == ID)['post_preview'] = new
    open(DATA, 'w', encoding='utf-8').write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('post_preview обновлен')
