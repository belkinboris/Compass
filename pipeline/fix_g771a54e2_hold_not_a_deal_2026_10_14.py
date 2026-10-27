# -*- coding: utf-8 -*-
"""`g771a54e2` («Частные инвесторы в сентябре вложили в облигации 210,6
млрд ₽», источник — пресс-релиз Мосбиржи через ПРАЙМ) — та же порода
находки, что уже стоит на `ga0dd6563` («ЦБ РФ... купил юаней...», тот же
`hold_reason`): механический гейт заполнил `buyer_name`/`asset` из
заголовка статистической сводки, но это агрегированная рыночная
статистика биржи, а не сделка M&A — ни стороны, ни предмета, ни суммы
конкретной транзакции здесь нет, только объем за месяц по всем частным
инвесторам сразу.

Запуск:
    python3 pipeline/fix_g771a54e2_hold_not_a_deal_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_g771a54e2_hold_not_a_deal_2026_10_14.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g771a54e2'
HOLD_REASON = (
    'Рыночная статистика Мосбиржи (совокупный объем покупки облигаций частными '
    'инвесторами за сентябрь), а не сделка M&A. Механически «покупатель» и «предмет» '
    'заполнились из заголовка сводки о рынке, но это агрегированная цифра по всем '
    'инвесторам сразу, не конкретная сторона и не конкретная покупка. Та же порода '
    'находки, что уже стоит на ga0dd6563 (ЦБ РФ/юани). Рекомендую 🗑 выкинуть, но '
    'решение за владельцем.'
)


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert not card.get('hold_reason'), card.get('hold_reason')

    print('ПРОСТАВЛЯЕМ %s: hold_reason' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    if fresh_card.get('hold_reason'):
        print('кто-то уже поправил — перечитайте')
        return 1
    fresh_card['hold_reason'] = HOLD_REASON
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
