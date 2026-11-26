"""Пост о покупке Леваном Назаровым ~20% «Циана» (gd1bf6d5e): строка «Покупатель»
с пояснением, кто он (владелец, 26 ноября 2026: «нужно написать, кто такой Леван
Назаров… очень коротко»; «просто в консоль отправь, мы отметим»). Пояснение — по
«Коммерсанту», Frank Media и сообщению канала, которое привел владелец.

Текст кладется в `post_preview` (снимок, который уходит по кнопке), а НЕ в
`post_override`: override send_telegram считает одобрением и выпустил бы пост без
кнопки. Новый проект поста уходит в консоль с обычными кнопками.

    python3 pipeline/archive/2026-11/gd1bf6d5e_post_buyer_line.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, p) for p in ('pipeline/publish', 'pipeline/ingest', 'pipeline', '.')]
import format_post  # noqa: E402
import send_drafts  # noqa: E402
import console_topics  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = '<b>Покупатель:</b> Леван Назаров\n'
NEW = ('<b>Покупатель:</b> Леван Назаров — финтех-предприниматель, основатель группы '
       '«Баланс-платформа», которая разрабатывает программное обеспечение для банков\n')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == 'gd1bf6d5e')
    assert 'gd1bf6d5e' not in data.get('telegram_posts', {}), 'пост уже вышел — нужна правка, а не новый проект'
    assert not deal.get('post_override') and not deal.get('post_approved')
    base = deal.get('post_preview') or format_post.render(deal, data['companies'])
    if NEW not in base:
        assert base.count(OLD) == 1, base
        base = base.replace(OLD, NEW)
    deal['post_preview'] = base
    text = send_drafts.post_message_text(deal, data['companies'], rendered=format_post.with_card_link(base, deal))
    print(text)
    if not write:
        print('\nсухой прогон')
        return
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    import httpx
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    with httpx.Client(timeout=20) as client:
        for chat in send_drafts.send_targets():
            ok = send_drafts.send_one(client, token, chat, text, send_drafts.post_keyboard(deal),
                                      console_topics.thread_id('decision'), html=True)
            print('отправлено в консоль:', ok)


if __name__ == '__main__':
    main('--write' in sys.argv)
