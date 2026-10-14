# -*- coding: utf-8 -*-
"""Второе чтение карточки g420352ff («Дом.РФ»/КРТ в Петра Дубраве) нашло:
`extra` — чистый повтор того, что уже сказано в eco.val (цена), eco.share
(52,31 га, 200,3 тыс. кв. м), law.struct (15 лет) и law.terms (школа и
сады) — ни одного факта сверх уже разложенного по полям. Честная пустота
(снятие ключа, как у 278 карточек базы без `extra`) вместо пересказа.

Запуск:
    python3 pipeline/fix_samara_krt_extra_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_samara_krt_extra_2026_10_14.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g420352ff'

OLD = ('За стартовую цену 11,19 млн ₽ инвестор получает право застроить 52,31 га и '
       'обязуется за 15 лет возвести не менее 200,3 тыс. кв. м жилья, школу на 1,1 тыс. '
       'мест и детские сады на 460 мест.')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card.get('extra') == OLD, card.get('extra')

    print('СНИМАЕМ %s: extra (чистый повтор eco.val/eco.share/law.struct/law.terms)' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    assert fresh_card.get('extra') == OLD, 'кто-то уже поправил — перечитайте'
    fresh_card.pop('extra', None)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
