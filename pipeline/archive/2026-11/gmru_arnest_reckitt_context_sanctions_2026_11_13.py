# -*- coding: utf-8 -*-
"""Добавление к eco.context карточки gmru-arnest-reckitt (ДОБАВЛЕНИЕ к уже
непустому полю — review.py check() валидирует квотой ВСЕ поле целиком,
включая старые числа 2025 года выручки «Арнеста», обеспеченные другой,
более ранней правкой; тот же класс ограничения, что встречался в этом
дне у c51d0bb64/g4afd35d0). Источник — Коммерсантъ (уже в src карточки),
дочитан по кэшу data/inbox/raw/2026-11-13-articles.jsonl."""
import json
import os
import sys

ROOT = '/home/user/Compass'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gmru-arnest-reckitt'

OLD_CONTEXT = ('Выручка АО «Арнест», основного юрлица группы, за 2025 год — 17,5 млрд ₽, на 12,9% больше, чем годом ранее; '
               'чистая прибыль — 4 млрд ₽, на 15,7% меньше. Сколько может заплатить «Арнест», основатель SharesPro Денис '
               'Астафьев оценивает в 25–40 млрд ₽ с учетом взноса в бюджет в размере 35% стоимости актива.')
ADDED_CONTEXT = (' По неофициальным данным, на решение не передавать бренды мог повлиять 18-й пакет санкций ЕС, '
                  'запретивший продажу основных брендов и технологий Reckitt Benckiser на российском рынке. Сама '
                  'площадка в Клину потребует вложений — Reckitt не инвестировала в нее четыре года и вовсе '
                  'остановила инвестиции в российский бизнес.')
NEW_CONTEXT = OLD_CONTEXT + ADDED_CONTEXT


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card['eco']['context'] == OLD_CONTEXT

    print('ПРАВКА %s' % CARD_ID)
    print('  eco.context : +%r' % ADDED_CONTEXT)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['eco']['context'] = NEW_CONTEXT

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card['eco']['context'] == OLD_CONTEXT, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
