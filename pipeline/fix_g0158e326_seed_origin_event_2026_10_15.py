# -*- coding: utf-8 -*-
"""Карточка g0158e326 (МГКЛ/крупный инвестор) была собрана отдельным
скриптом с заполненным `src`, но без `events` — и `enrich.py`'s дедуп по
URL сверяет только `events[].source`, не `src`. Та же пара статей
(Ведомости + Frank Media), на которых карточка построена, на прогоне
12:20 15 октября предложила СЕБЯ как «новый подтвержденный этап» — пустой
`events` ничего не знал о них. Класс риска шире одной карточки: любая
карточка, собранная мимо `promote.to_card()` без события-первоисточника
в `events`, уязвима к тому же самоповтору. Документировано в
KNOWN_ISSUES.md. Чиним точечно: добавляем событие-первоисточник.

Запуск:
    python3 pipeline/fix_g0158e326_seed_origin_event_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_g0158e326_seed_origin_event_2026_10_15.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g0158e326'
NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-10-15',
    'title': 'Переговоры',
    'note': 'Крупный инвестор обсуждает с МГКЛ вхождение в капитал и финансирование покупки банка.',
    'source': ['Ведомости', 'https://www.vedomosti.ru/finance/articles/2026/10/15/1237169-mgkl-nashla-investora'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert not card.get('events'), 'events уже не пуст: %r' % card.get('events')
    print('events[0] <- %r' % NEW_EVENT)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_card = next(d for d in fresh['deals'] if d['id'] == CARD_ID)
    assert not fresh_card.get('events'), 'events поменяли параллельно — перечитайте'
    fresh_card['events'] = [NEW_EVENT]
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
