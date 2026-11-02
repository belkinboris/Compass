# -*- coding: utf-8 -*-
"""Сводка за октябрь 2026: текст владельца, 2 ноября 2026.

Владелец переписал сводку ответом на черновик «[сводка 2026-10]», а обработчика
таких ответов не было (app/console.py, исправлено в тот же день) — текст
пропал. Он сохранен здесь по сообщению владельца в чате сессии и лежит в
`telegram_digests['2026-10']['owner_text']`: рутина публикации выпустит сводку
этим текстом в ближайшее окно (`send_telegram.digest_owner_text`), как если бы
решение дошло. Три строки «самых дорогих» — ссылки на карточки, как в нашем
формате (id — по сводке на момент черновика).

    python3 pipeline/fix_digest_owner_text_2026_11_02.py           # сухой прогон
    python3 pipeline/fix_digest_owner_text_2026_11_02.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
KEY = '2026-10'
SITE = 'https://projectcompass.ru'
TOP = [('g5eb6ff22', '«Росатом» завершил выкуп у Сергея Шишкарева 51% в группе компаний «Дело»', '77 млрд ₽'),
       ('g1f8414a3', '«ЭсЭфАй» выиграла повторные торги за банк «Агропромкредит»', '1,427 млрд ₽'),
       ('gc04356ba', 'Хабаровская «Сила Востока» выиграла аукцион Роснедр на золоторудный участок Нетчен-Хая', '1,125 млрд ₽')]


def owner_html():
    top = '\n\n'.join('%d. <a href="%s/#/deal/%s">%s</a> — %s' % (i, SITE, cid, title, price)
                      for i, (cid, title, price) in enumerate(TOP, 1))
    return ('📊 <b>Рынок слияний и поглощений в октябре 2026</b>\n\n'
            'За октябрь мы рассказали о 115 сделках.\n\n'
            '<b>Самые дорогие сделки</b>\n\n' + top + '\n\n'
            '<b>В каких отраслях больше всего сделок:</b> недвижимость — 44, ГМК и добыча — 12, '
            'пищепром и напитки — 8.\n\n'
            '<b>Особенности месяца:</b> продажа с торгов — 52, национализация / иск Генпрокуратуры — 10.\n\n'
            '#статистика #MA')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    ids = {d['id'] for d in data['deals']}
    missing = [c for c, _t, _p in TOP if c not in ids]
    assert not missing, 'нет карточек: %s' % missing
    state = data.setdefault('telegram_digests', {}).get(KEY)
    assert state and not state.get('message_id'), 'сводка %s уже вышла или черновика нет: %r' % (KEY, state)
    print('owner_text для %s:\n%s' % (KEY, owner_html()))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))          # перечитать прямо перед записью
    state = data['telegram_digests'][KEY]
    assert not state.get('message_id')
    state['owner_text'] = owner_html()
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
