"""Пост «Медси» (g4d7b2e19, сообщение 199 в канале): новая подпись кнопки
«Подробнее в карточке сделки» и та же надпись ссылкой последней строкой
текста. Владелец, 13 октября 2026: «измени пост с медси, чтобы так было,
можешь не отправлять на проверку, а просто поменять». Текст — тот, что
прислал партнёр владельца (`post_override`), базу не трогаем: ссылку
добавляет `format_post.with_card_link`. Без `--edit` — сухой прогон."""
import json, os, sys
sys.path.insert(0, 'pipeline/publish'); sys.path.insert(0, 'pipeline')
import format_post, send_telegram  # noqa: E402
import httpx  # noqa: E402
DATA, ID, MSG = 'static/data/deals_promoted.json', 'g4d7b2e19', 199

data = json.load(open(DATA, encoding='utf-8'))
deal = next(d for d in data['deals'] if d['id'] == ID)
assert data['telegram_posts'].get(ID) == MSG
assert ID not in (data.get('telegram_posts_realty') or {})
new = send_telegram.initial_post_text(deal, data['companies'])
buttons = format_post.render_buttons(deal)
print(new); print(buttons)
if '--edit' in sys.argv:
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat = send_telegram.channel_address()
    with httpx.Client(timeout=30) as client:
        print(send_telegram.edit_message(client, token, chat, MSG, new, buttons))
    print('сообщение', MSG, 'исправлено')
