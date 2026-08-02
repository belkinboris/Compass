# -*- coding: utf-8 -*-
"""Засеять `telegram_posts`, чтобы канал не публиковал старый бэклог.

ЧТО РЕШЕНО (владелец, 2 августа 2026). Бот и канал заведены, но публиковать
существующие ~1350 карточек разом (даже с ограничением скорости из
`send_telegram.py`) не нужно — читатель, подписавшийся на канал сегодня, не
должен получить историю рынка за три года постами один за другим. Канал
начинает с сегодняшнего дня: публикуются только сделки, появившиеся ПОСЛЕ
включения токена.

КАК ЭТО РАБОТАЕТ. `telegram_posts` — словарь id сделки -> id сообщения в
канале; `send_telegram.py` считает «новой для отправки» любую сделку, которой
нет в этом словаре. Этот скрипт добавляет в словарь ВСЕ сделки, существующие
на момент запуска, со значением `null` — не настоящим id сообщения (такого
сообщения не существует), а меткой «эта карточка — бэклог, не публиковать».
`send_telegram.py` теперь явно пропускает записи с пустым значением — не
пытается ни опубликовать их, ни отредактировать, если бэклог-карточка
поздние получит новый факт.

КОГДА ЗАПУСКАТЬ. Один раз, непосредственно перед первым включением
`TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHANNEL_ID` в бою. Если запустить повторно —
ничего не сломает (уже засеянные записи просто останутся как есть), но и
разумного повода запускать дважды нет.

Запуск:
    python3 pipeline/publish/seed_telegram_posts_backlog.py            # сухой прогон
    python3 pipeline/publish/seed_telegram_posts_backlog.py --write    # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    posts = data.setdefault('telegram_posts', {})

    already = len(posts)
    to_seed = [d['id'] for d in data['deals'] if d['id'] not in posts]

    print('уже в telegram_posts: %d' % already)
    print('засеваем как бэклог (не публикуется): %d' % len(to_seed))
    print('всего карточек в базе: %d' % len(data['deals']))

    if write:
        for did in to_seed:
            posts[did] = None
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
        print('С этого момента новыми для канала будут только сделки, добавленные ПОСЛЕ этого прогона.')
    else:
        print('\nСухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
