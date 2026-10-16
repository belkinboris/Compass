# -*- coding: utf-8 -*-
"""Карточка gd09e0945 собрана автоматически из заголовка "Игровую студию
«Леста» приобрела компания «Промышленные сооружения»" — разборщик спутал
стороны: «Леста» стояла в заголовке в винительном падеже (кого купили),
а подлежащим («кто купил») было «компания «Промышленные сооружения»».
Сборка записала наоборот: buyer_name="Игровую студию «Леста»",
asset="«Промышленные сооружения»". Исследование (десять источников —
Коммерсантъ, Ведомости, Frank Media, Sostav, 3DNews, App2Top, DTF,
Sports.ru, WotExpress, Серебряный Дождь) подтвердило: покупатель — АО
«Промышленные сооружения» (консорциум частных инвесторов, рег. ноябрь
2024, гендир. с 15 октября 2026 — Захар Кислых), предмет — группа
компаний «Леста Игры» (три юрлица: ООО «Леста», ООО «Леста Геймс
Эдженси», ООО «Леста Геймс Москва»). Продавец — Росимущество: летом
2025 года группу национализировали по суду (экстремистская деятельность/
поддержка ВСУ, установленная в отношении прежних владельцев Малика
Хатажаева и Виктора Кислого), с тех пор держало на себе. Сделка
закрыта — переход уже отражён в ЕГРЮЛ. Сумма не раскрыта ни одним
источником (135 млрд ₽ и ~50 млрд ₽ — оценки актива, не цена сделки;
«до 10 млрд ₽» — заявленные планы покупателя по будущим инвестициям в
отрасль, тоже не цена).

Запуск:
    python3 pipeline/fix_lesta_parties_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_lesta_parties_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'gd09e0945'

OLD = {
    'buyer_name': 'Игровую студию «Леста»',
    'asset': '«Промышленные сооружения»',
    'seller': None,
    'ind': 'Не определена',
}
NEW = {
    'buyer_name': 'АО «Промышленные сооружения»',
    'asset': 'группа компаний «Леста Игры» (ООО «Леста», ООО «Леста Геймс Эдженси», '
             'ООО «Леста Геймс Москва»)',
    'seller': 'Росимущество',
    'ind': 'ИТ и интернет',
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards[CARD_ID]
    for field, old in OLD.items():
        assert card.get(field) == old, '%s: %s уже не %r (сейчас %r)' % (CARD_ID, field, old, card.get(field))
        print('%s: %s %r -> %r' % (CARD_ID, field, old, NEW[field]))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    for field, old in OLD.items():
        assert fc.get(field) == old, '%s: %s поменяли параллельно — перечитайте' % (CARD_ID, field)
        fc[field] = NEW[field]
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
