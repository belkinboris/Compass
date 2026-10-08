# -*- coding: utf-8 -*-
"""Пост № 189 (`g51fa80ce`, «Голдрупп» / участок россыпного золота): вернуть
разметку тексту, который владелец прислал ответом 8 октября 2026.

ЗАЧЕМ. Бот брал из ответа владельца только `text`, а жирный и ссылка лежат в
Telegram отдельно (`entities`): пост ушёл без жирных подписей, «ПРАЙМ» —
не ссылкой. Причина починена в main.py (`_telegram_text_as_html`); здесь —
этот пост. Текст владельца не меняется ни на букву: только подписи жирным
(как в черновике), заголовок жирным и ссылка источника из `src` карточки.

    python3 pipeline/fix_g51fa80ce_post_formatting.py           # показать
    python3 pipeline/fix_g51fa80ce_post_formatting.py --write   # записать и поправить пост
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
import format_post  # noqa: E402
import send_telegram  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g51fa80ce'
LABELS = ('Покупатель', 'Продавец', 'Предмет', 'Сумма', 'Статус', 'Отрасль', 'Источник')


def formatted(plain, src_url):
    lines = plain.split('\n')
    out = ['<b>%s</b>' % html.escape(lines[0], quote=False)]
    for line in lines[1:]:
        m = re.match(r'^(%s):\s?(.*)$' % '|'.join(LABELS), line)
        if not m:
            out.append(html.escape(line, quote=False))
            continue
        label, value = m.group(1), m.group(2)
        val = html.escape(value, quote=False)
        if label == 'Источник':
            val = '<a href="%s">%s</a>' % (html.escape(src_url, quote=True), val)
        out.append('<b>%s:</b> %s' % (label, val))
    return '\n'.join(out)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    old = deal.get('post_override') or ''
    assert old.startswith('«Голдрупп» выиграла аукцион') and '<b>' not in old, old[:80]
    assert old.rstrip().endswith('#торги') and '\nИсточник: ПРАЙМ\n' in old
    src = deal['src'][0]
    assert src[0] == 'ПРАЙМ' and src[1].startswith('https://1prime.ru/'), src
    mid = data['telegram_posts'].get(DEAL)
    assert mid == 189, mid
    new = formatted(old, src[1])
    assert re.sub(r'<[^>]+>', '', html.unescape(new)) == html.unescape(old), 'текст владельца поменялся'
    print(new)
    if not write:
        print('\nСухой прогон. Запись и правка поста — с ключом --write.')
        return 0
    deal['post_override'] = new
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat = send_telegram.channel_address()
    assert token and chat, 'нет токена или адреса канала'
    with send_telegram._client() as client:
        send_telegram.edit_message(client, token, chat, mid, new, buttons=format_post.render_buttons(deal))
    print('\nзаписано; пост № %s поправлен' % mid)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
