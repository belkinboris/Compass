# -*- coding: utf-8 -*-
"""Предложить правку УЖЕ ВЫШЕДШЕГО поста — в консоль, с кнопками.

    python3 pipeline/publish/propose_post_edit.py <id сделки> [--write]

Зачем (29 октября 2026). Пост об «Агропромкредите» (g1f8414a3) вышел 27 октября
текстом владельца, без суммы; через два дня карточка узнала цену 1,427 млрд ₽.
Автоправка посты с текстом владельца не трогает (Swordfish Security, 21 октября:
«выложили не тот пост, который я в консоль отправил»), а второй пост о той же
сделке владелец запретил («дублирующий пост не нужен, его просто нужно
изменить с указанием новых вводных»). Третий путь — предложение: текст поста
по текущей карточке уходит в консоль с кнопками «Пост в канал» / «Без поста»;
нажали «в канал» — рутина публикации правит пост там, где он вышел, и
запоминает новый текст как текст владельца (`post_override`).

Предложение хранится в карточке (`post_edit_proposal`), решение приходит тем
же мостом, что у вех: `deal_id` решения — `<id>~edit`
(`send_telegram.post_edit_decisions`). Без --write — показать текст.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import format_post  # noqa: E402
import send_drafts  # noqa: E402
import console_topics  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def keyboard(deal_id):
    combo = '%s~edit' % deal_id
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:%s:post_ok' % combo},
        {'text': '🔕 Без поста', 'callback_data': 'mod:%s:post_no' % combo},
    ]]}


def message(deal, text):
    posted = deal.get('telegram_posted_at') or ''
    return ('✏️ [правка поста %s] — пост о сделке уже вышел в канале%s; '
            'предлагаю заменить его текст на этот. «Пост в канал» — заменить, '
            '«Без поста» — оставить как есть.\n\n%s' % (deal['id'], (' ' + posted[:10]) if posted else '', text))


def build(data, deal_id):
    deal = next((d for d in data['deals'] if d['id'] == deal_id), None)
    if deal is None:
        raise SystemExit('Карточки %s нет в базе.' % deal_id)
    if not (data.get('telegram_posts') or {}).get(deal_id) \
            and not (data.get('telegram_posts_realty') or {}).get(deal_id):
        raise SystemExit('Пост о %s не выходил — править нечего, это обычный первый пост.' % deal_id)
    text = format_post.render(deal, data.get('companies') or {})
    return deal, text


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    deal_id, write = argv[0], '--write' in argv
    data = json.load(io.open(DATA, encoding='utf-8'))
    deal, text = build(data, deal_id)
    print(text)
    if not write:
        print('\nСухой прогон. Отправка в консоль и запись предложения — с ключом --write.')
        return 0
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chats = send_drafts.send_targets()
    if not (token and chats):
        print('Нет TELEGRAM_BOT_TOKEN или адреса консоли — не отправляю.')
        return 1
    import httpx
    with httpx.Client(timeout=20) as client:
        ok = all(send_drafts.send_one(client, token, chat, message(deal, text), keyboard(deal_id),
                                      console_topics.thread_id('decision'), html=True) for chat in chats)
    if not ok:
        print('Консоль не приняла сообщение — предложение не записано.')
        return 1
    # Перечитать базу прямо перед записью: пока слали, ее мог изменить другой прогон.
    data = json.load(io.open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == deal_id)
    deal['post_edit_proposal'] = text
    json.dump(data, io.open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Предложение ушло в консоль и записано в карточку (post_edit_proposal). '
          'Решение применит рутина публикации.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
