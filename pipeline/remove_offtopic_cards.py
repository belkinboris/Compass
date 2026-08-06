# -*- coding: utf-8 -*-
"""Убрать две карточки, которые не место в базе сделок M&A.

ЧТО ЧИНИТ. По решению владельца 6 августа удаляются:
  * g6fe74673 «Группа ЛСР продала вторую очередь элитного ЖК на Петровском
    острове» — продажа очереди ЖК покупателям квартир, не сделка M&A;
  * g94617d17 «Мэрия Екатеринбурга продаст подвалы и участки на окраинах» —
    план приватизации мелкого муниципального имущества, не сделка рынка.

ПОЧЕМУ ОНИ В БАЗЕ. Обе попали коммитом 9ee7824 (5 августа), когда promote
ещё писал прошедшие ворота карточки прямо в базу — консоль модерации
появилась позже, и владелец по ним не голосовал. Сегодня такие карточки
пришли бы в группу с кнопкой «🗑 Выкинуть».

ПОЧЕМУ ПРОСТО УДАЛЕНИЕ, БЕЗ ПЕРЕНАПРАВЛЕНИЯ. Правило «слияние не должно
обрывать ссылку» здесь не применимо: это не дубли, перенаправлять не на
что. Карточки прожили на сайте меньше двух суток, постов в канал не было
(telegram_posts их не знает), профили компаний на них не ссылаются
(продавец записан текстом), в match_keys и merged их нет — скрипт это
проверяет assert'ами, а не верит на слово.

Запуск:
    python3 pipeline/remove_offtopic_cards.py            # сухой прогон
    python3 pipeline/remove_offtopic_cards.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

REMOVE = {
    'g6fe74673': 'Группа ЛСР продала вторую очередь элитного ЖК',
    'g94617d17': 'Мэрия Екатеринбурга продаст подвалы и участки',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    found = {d['id']: d for d in deals if d['id'] in REMOVE}
    assert set(found) == set(REMOVE), 'ожидали обе карточки, нашли: %s' % sorted(found)

    raw = json.dumps(data, ensure_ascii=False)
    for cid, expect in REMOVE.items():
        card = found[cid]
        assert expect.split()[0] in str(card.get('title')), (cid, card.get('title'))
        # Ссылок на карточку быть не должно нигде, кроме самой записи в deals:
        # иначе удаление оборвало бы чужой указатель.
        assert raw.count(cid) == 1, 'на %s есть ссылки вне deals' % cid
        assert cid not in data.get('telegram_posts', {}), '%s знает канал' % cid
        assert cid not in data.get('merged', {}).values(), '%s — цель merged' % cid
        print('  УДАЛЯЕМ %s %s' % (cid, str(card.get('title'))[:60]))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    data['deals'] = [d for d in deals if d['id'] not in REMOVE]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Удалено: %d. Сделок в базе: %d.' % (len(found), len(data['deals'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
