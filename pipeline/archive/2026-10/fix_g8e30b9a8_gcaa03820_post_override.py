# -*- coding: utf-8 -*-
"""Снимает `post_override` у `g8e30b9a8` и `gcaa03820` — записью 549ddbea
(14 августа 2026, прогон публикации) туда лег не ответ владельца, а
дословный текст СОБСТВЕННОГО сообщения-запроса бота («📣 [пост …] — В
канал, на проверку… Ответ на это сообщение своим текстом ЗАМЕНИТ пост»,
с ссылками на карточку и лупы «Экономист»/«Юрист» — так не пишет человек,
это формат черновика на проверку). Это и держит оба поста уже два месяца:
`check_post.py` ловит в нем строку «Отрасль: Не определена» (заглушка из
старого снимка карточки на момент отправки черновика) и отказывается
публиковать.

Свежий `format_post.render()` обоих карточек сейчас чист (обе стороны,
сумма где есть, статус, отрасль — без единой находки check_post.check()):
данные с 14 августа дозрели, просто автоформат не мог пробиться через
чужой post_override. Откуда взялся дословный текст запроса в поле ответа —
вопрос к `docs/moderation_console_tech.md` (сайт/вебхук), не к данным;
здесь чинится только симптом — разблокируется автоформат.

Без ключа — сухой прогон, запись — `--write`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TARGETS = {
    'g8e30b9a8': '📣 [пост g8e30b9a8]',
    'gcaa03820': '📣 [пост gcaa03820]',
}


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    changed = []
    for deal in data['deals']:
        if deal['id'] not in TARGETS:
            continue
        override = deal.get('post_override') or ''
        marker = TARGETS[deal['id']]
        assert marker in override, (
            '%s: ожидали в post_override текст запроса бота (%r), не нашли — '
            'поле уже изменилось, скрипт не трогает' % (deal['id'], marker))
        changed.append(deal['id'])
        if write:
            del deal['post_override']

    print('Карточки с найденным дефектом: %s' % ', '.join(changed))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('post_override снят у %d карточек.' % len(changed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
