"""Пост «Соликамскбумпрома» (g002710cf, сообщение 202 в канале): новый
заголовок от лица покупателя — владелец 14 октября 2026: «написано у нас
плохо, как будто они сами свои акции продают». Поля карточки поправил
`fix_solikamsk_owners_2026_10_14.py`; смена заголовка правку поста рутиной
не запускает (`post_snapshot` его не помнит), поэтому пост правится здесь.
`editMessageText` подписчиков не будит. Без `--edit` — сухой прогон."""
import json, os, sys
sys.path.insert(0, 'pipeline/publish'); sys.path.insert(0, 'pipeline')
import format_post, send_telegram  # noqa: E402
import httpx  # noqa: E402
DATA, ID, MSG = 'static/data/deals_promoted.json', 'g002710cf', 202

data = json.load(open(DATA, encoding='utf-8'))
deal = next(d for d in data['deals'] if d['id'] == ID)
assert data['telegram_posts'].get(ID) == MSG
assert ID not in (data.get('telegram_posts_realty') or {})
assert not deal.get('post_override')
new = format_post.render(deal, data['companies'])     # собран из поправленной карточки
assert new.startswith('<b>Китайская «Юнь Чоу» намерена купить 83,3%'), new[:80]
buttons = format_post.render_buttons(deal)
print(new); print(buttons)
if '--edit' in sys.argv:
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat = send_telegram.channel_address()
    with httpx.Client(timeout=30) as client:
        print(send_telegram.edit_message(client, token, chat, MSG, new, buttons))
    print('сообщение', MSG, 'исправлено')
    # Снимок черновика — тот же текст: иначе следующая правка вернет старый заголовок.
    raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(raw)
    next(d for d in fresh['deals'] if d['id'] == ID)['post_preview'] = new
    open(DATA, 'w', encoding='utf-8').write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('post_preview обновлен')
