"""Пост «Александр Калин вышел из капитала «Яндекса»» (g9368796b): новый проект в
консоль после правки заголовка и строки «Предмет» по решению владельца (26 ноября
2026: «назвать не „утратил контроль“, а „вышел из капитала“… в предмете столько-то
акций Яндекса»). Текст уже лежит в `post_preview` (снимок, который уходит по кнопке;
не `post_override`, тот считается одобрением). Скрипт только показывает проект с
обычными кнопками.

    python3 pipeline/archive/2026-11/g9368796b_post_subject.py [--write]
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


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == 'g9368796b')
    assert 'g9368796b' not in data.get('telegram_posts', {}), 'пост уже вышел'
    assert not deal.get('post_override') and not deal.get('post_approved')
    base = deal['post_preview']
    assert 'вышел из капитала' in base and '6,51% акций МКПАО «Яндекс»' in base
    text = send_drafts.post_message_text(deal, data['companies'], rendered=format_post.with_card_link(base, deal))
    print(text)
    if not write:
        print('\nсухой прогон')
        return
    import httpx
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    with httpx.Client(timeout=20) as client:
        for chat in send_drafts.send_targets():
            ok = send_drafts.send_one(client, token, chat, text, send_drafts.post_keyboard(deal),
                                      console_topics.thread_id('decision'), html=True)
            print('отправлено в консоль:', ok)


if __name__ == '__main__':
    main('--write' in sys.argv)
