# -*- coding: utf-8 -*-
"""Приток 22 сентября 2026: g2dacdd88 (Mergers.ru) и g076af76a (CNews) —
одна и та же новость (смена основного владельца ООО «Здоровье города»,
платформа «Здоровье.ру»), пришедшая двумя изданиями и не пойманная
dup_in_batch (разные заголовки, ни одного общего названия в кавычках).
Оставляем g076af76a (богаче источник), переносим адрес Mergers.ru туда
вторым источником, убираем дубль из очереди — «одна новость в двух
изданиях — одно сообщение в консоли».

Запуск: python3 pipeline/merge_zdorovie_ru_dup_2026_09_22.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)) + '/..'
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DROP_ID = 'g2dacdd88'
KEEP_ID = 'g076af76a'
MERGERS_SRC = ['Mergers.ru',
               'https://mergers.ru/news/Platforma-Zdoroveru-zakryla-sdelku-po-vykupu-'
               'rannih-investorov-i-privlekla-investicii-na-masshtabirovanie-'
               'novoj-biznes-modeli-87557']


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = data['cards']
    by_id = {c['id']: c for c in cards}
    assert DROP_ID in by_id, 'g2dacdd88 не в pending.json — уже обработана?'
    assert KEEP_ID in by_id, 'g076af76a не в pending.json'
    keep = by_id[KEEP_ID]
    srcs = keep.get('src') or []
    assert not any(s[1] == MERGERS_SRC[1] for s in srcs), 'источник уже привязан'
    srcs.append(MERGERS_SRC)
    keep['src'] = srcs
    data['cards'] = [c for c in cards if c['id'] != DROP_ID]
    assert len(data['cards']) == len(cards) - 1
    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: %s убрана из очереди, источник перенесён на %s.' % (DROP_ID, KEEP_ID))
    else:
        print('Сухой прогон: %s ушла бы, источник перенёсся бы на %s (--write, чтобы записать).'
              % (DROP_ID, KEEP_ID))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
