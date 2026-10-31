"""Пост «Чемодан Про» (g83ad1f72, сообщение 198 в канале): убрать подпись
предпросмотра «Кнопки под постом: …», ушедшую подписчикам текстом, и
уточнить предмет — куплены оставшиеся 30%, а не весь «Чемодан Про».

Артем, 13 октября 2026: «Написал ебаную ересь для тг канала по сделке
Samsonite». Правка `post_override` — в базе; `--edit` правит вышедшее
сообщение (`editMessageText` подписчиков не будит), кнопка «Открыть
карточку сделки» передается заново, иначе Telegram ее снимет.
Без ключей — сухой прогон."""
import json, os, sys
sys.path.insert(0, 'pipeline/publish'); sys.path.insert(0, 'pipeline')
import format_post, send_telegram, telegram_endpoint  # noqa: E402
import httpx  # noqa: E402
DATA, ID, MSG = 'static/data/deals_promoted.json', 'g83ad1f72', 198
OLD_SUBJ = '<b>Предмет:</b> ООО «Чемодан Про»\n'
NEW_SUBJ = '<b>Предмет:</b> 30% ООО «Чемодан Про»\n'


def fixed(text):
    assert OLD_SUBJ in text and 'Кнопки под постом' in text, text[-300:]
    return format_post.strip_platform_links(text.replace(OLD_SUBJ, NEW_SUBJ))


data = json.load(open(DATA, encoding='utf-8'))
deal = next(d for d in data['deals'] if d['id'] == ID)
assert data['telegram_posts'].get(ID) == MSG
new = fixed(deal['post_override'])
print(new)
if '--write' in sys.argv:
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == ID)
    deal['post_override'] = fixed(deal['post_override'])
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
    print('записано')
if '--edit' in sys.argv:
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat = send_telegram.channel_address()
    with httpx.Client(timeout=30) as client:
        send_telegram.edit_message(client, token, chat, MSG, new, format_post.render_buttons(deal))
    print('сообщение', MSG, 'исправлено в', chat)
