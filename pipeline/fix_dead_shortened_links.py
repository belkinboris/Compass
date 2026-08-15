# -*- coding: utf-8 -*-
"""Каталог вычитки, класс E6: мёртвая сокращённая ссылка vdmsti.ru.

Найдено чтением у cc16fce80 (круг 4, уже починена): vdmsti.ru/qQ7T
отвечал 404, подпись — имя канала-агрегатора вместо издания. Сплошной
прогон по домену vdmsti.ru нашёл ещё три — все три отвечают 404 (curl,
https, проверено дважды: http-версия одной из ссылок сначала попала на
блок прокси этой сессии, а не на ответ сайта, — перепроверена по https).

Каждая заменена статьёй о ТОМ ЖЕ событии, живой (curl, 200), дата и факты
сверены с карточкой:

  * gb6b371c3 (MOL/NIS, 19 января 2026) — на Ъ, дата события совпадает.
  * g8e46beea (Агрокомплекс Ткачева/«Сельком», ноябрь 2024) — на настоящую
    статью Ведомостей о том же событии (у карточки уже было два живых
    источника, vdmsti.ru был третьим и лишним, но подпись «Ведомости»
    обязана вести на статью издания, а не на 404).
  * c1aa8b20d (Fesco/порт Камчатки, 20 октября 2025) — на Интерфакс,
    дата публикации совпадает день в день.

Запуск:
    python3 pipeline/fix_dead_shortened_links.py            # сухой прогон
    python3 pipeline/fix_dead_shortened_links.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

REPLACE = [
    ('gb6b371c3',
     ['Ведомости', 'https://vdmsti.ru/tkQx'],
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8362366']),
    ('g8e46beea',
     ['Ведомости', 'http://vdmsti.ru/oNe1'],
     ['Ведомости',
      'https://www.vedomosti.ru/business/articles/2025/01/16/1086465-agrokompleks-semi-tkacheva-ofitsialno-vishel-v-dnr']),
    ('c1aa8b20d',
     ['@dealsma (Telegram)', 'https://vdmsti.ru/r8nO'],
     ['Интерфакс', 'https://www.interfax.ru/business/1053521']),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, old, _new in REPLACE:
        assert old in by_id[cid]['src'], '%s: старой записи src нет' % cid

    print('Замен мёртвых ссылок: %d' % len(REPLACE))
    for cid, old, new in REPLACE:
        print('  %s %r -> %r' % (cid, old, new))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, old, new in REPLACE:
        src = by_id[cid]['src']
        src[src.index(old)] = new

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
