# -*- coding: utf-8 -*-
"""Приток 25 сентября 2026 (14:20 МСК), ge957fc7b (штаб-квартира «Швабе»,
торги закрыты): enrich.py механически добавил событие «closed» по
заголовку источника, но с пустой заметкой (`note`) — событие без текста
на сайте не показывает, откуда оно взялось. Заполняю дословной цитатой;
заодно eco.context — то, что актив ушёл по стартовой цене (без превышения)
и что учредитель покупателя — Илья Клебанов.

`events[i].note` не адресуется через таблицу FIXES (там нет пути внутрь
списка) — тот же случай, что уже решался прямым скриптом для дописывания
уже заполненных полей.

Источник: https://realty.ria.ru/20260925/rostehi-2120243766.html,
прочитан целиком, кэш в data/inbox/raw/2026-09-25-articles.jsonl.

Запуск: python3 pipeline/fix_shvabe_hq_event_note_2026_09_25.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge957fc7b'

EVENT_NOTE = (
    'Согласно протоколу торгов, актив достался ООО «Оптика Мира». '
    '«Оптика Мира», учредителем которой является Илья Клебанов, получит '
    'актив по начальной цене, составляющей 1,8 миллиарда рублей.'
)

OLD_CONTEXT = (
    '«Ростех» уже искал инвестора на этот комплекс в 2022 году. Тогда '
    'компания рассчитывала выручить за него 1,77 млрд ₽, но инвестор мог '
    'предложить и меньше — вплоть до 1,57 млрд ₽. Торги признали '
    'несостоявшимися: заявок не поступило.'
)
QUOTE_ADD = (
    'Илья Клебанов — бывший полномочный представитель президента в '
    'Северо-Западном федеральном округе.'
)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert card['events'][0]['note'] == ''
    card['events'][0]['note'] = EVENT_NOTE

    assert card['eco']['context'] == OLD_CONTEXT
    card['eco']['context'] = OLD_CONTEXT + ' ' + QUOTE_ADD

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: заметка события заполнена, eco.context дополнен.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
