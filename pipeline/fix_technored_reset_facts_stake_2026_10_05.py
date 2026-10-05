# -*- coding: utf-8 -*-
"""Качество, 5 октября 2026 — продолжение отмены ошибочной правки
(`fix_technored_revert_stake_51_2026_10_05.py`): `eco.share` и
`stake_acquired` уже вернули к 49%, но `facts.stake` остался в `basis=
'stale'` со вчерашними (сегодняшними) показаниями читателей на 51% —
слой фактов сознательно не пересчитывает `stale` обратно в `rule`
автоматически (защита от бага 21 сентября, `KNOWN_ISSUES.md»), это
верно для настоящего «карточка изменилась, нужно перечитать», но здесь
сама правда не менялась — откатываю руками к состоянию до сегодняшнего
подтверждения фактов (`basis='rule', value=49.0`, тот же `card_hash`,
что был в HEAD перед сегодняшним прогоном).

Запуск:
    python3 pipeline/fix_technored_reset_facts_stake_2026_10_05.py            # сухой прогон
    python3 pipeline/fix_technored_reset_facts_stake_2026_10_05.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'technored']
    assert len(target) == 1, target
    card = target[0]
    assert card['eco']['share'] == 'Размер выкупа — 49%, контрольного пакета у «Вартона» нет.', card['eco']['share']
    assert card['facts']['stake'].get('basis') == 'stale', card['facts']['stake']
    assert card['facts']['stake'].get('value') == 51.0, card['facts']['stake']

    card['facts']['stake'] = {'basis': 'rule', 'card_hash': '51f0c826dda7', 'value': 49.0}

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('facts.stake карточки technored возвращён к basis=rule/49.0. ЗАПИСАНО.')
    else:
        print('Сухой прогон: вернул бы facts.stake к basis=rule/49.0. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
