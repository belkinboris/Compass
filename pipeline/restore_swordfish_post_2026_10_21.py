"""Swordfish Security (gf6c084b9) — вернуть в канал текст владельца, 21 октября 2026.

Пост вышел текстом владельца (post_override), а через три часа send_telegram
переписал его автотекстом после дополнения карточки (правка «⟳ Обновлено» не
смотрела на post_override; починено в send_telegram.py). Владелец: «Выложили
не тот пост, который я в консоль отправил». Правим тот же пост обратно на его
текст с кнопкой карточки. Без ключа — сухой прогон.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in ('pipeline/publish', 'pipeline/ingest', 'pipeline', ''):
    sys.path.insert(0, os.path.join(ROOT, p))
import send_telegram, format_post  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == 'gf6c084b9')
    mid = data['telegram_posts']['gf6c084b9']
    assert mid == 218 and deal.get('post_override')
    text = send_telegram.initial_post_text(deal, data['companies'])
    print(text)
    if not write:
        print('сухой прогон'); return
    import httpx
    with httpx.Client(timeout=30) as client:
        send_telegram.edit_message(client, os.environ['TELEGRAM_BOT_TOKEN'], send_telegram.channel_address(),
                                   mid, text, format_post.render_buttons(deal))
    data = json.load(open(DATA, encoding='utf-8'))
    data.setdefault('telegram_post_state', {})['gf6c084b9'] = send_telegram.post_snapshot(
        next(d for d in data['deals'] if d['id'] == 'gf6c084b9'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('пост 218 возвращен к тексту владельца')


if __name__ == '__main__':
    main('--write' in sys.argv)
