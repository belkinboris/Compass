# -*- coding: utf-8 -*-
"""Заголовки двух карточек, где заголовок расходился с источником (16 октября 2026).

1. ga13c3ea7 — «Viterra продала 50% Зернового терминального комплекса Тамань
   компании Илья Косых»: имя в именительном падеже после «компании» и без
   кавычек у названия комплекса. По «Коммерсанту» (kommersant.ru/doc/6612078)
   долю купила компания «Доставка морем» — это подтвердила ее гендиректор
   Наталья Тугалева; Илья Косых — собственник «Доставки морем» и, по
   отчетности ЗТКТ, косвенный владелец более 25% комплекса. Viterra в отчете
   за 2023 год показала продажу 50% ЗТКТ за $40 млн. Профиль покупателя
   («Илья Косых») не трогаем: задача — заголовок; смена профиля на
   юрлицо — отдельное решение.

2. g0dea398b — «Sminex приобрел финскую Fazer у производителя хлеба»:
   покупатель назван неверно и смысл перевернут. По «Интерфаксу»
   (interfax.ru/business/838754, 29 апреля 2022) Fazer подписал соглашение
   о продаже российской «дочки» БКХ «Коломенский», а владелец «Коломенского»
   Алексей Тулупов — он же президент девелопера Sminex (там же; msk1.ru,
   29 апреля 2022, — сделка по ООО «Хлебный Дом»). Покупатель в карточке
   уже верный (профиль БКХ «Коломенский»), правится только заголовок; оба
   адреса добавляются в источники.

Заголовок — структурное поле: review.py требует, чтобы он дословно лежал в
цитате, а исправленный заголовок собирается из слов карточки, поэтому —
разовый скрипт с assert на старое значение (docs/card_editing.md).

Запуск: python3 pipeline/fix_four_card_titles_2026_10_16.py          # сухой
        python3 pipeline/fix_four_card_titles_2026_10_16.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    'ga13c3ea7': (
        'Viterra продала 50% Зернового терминального комплекса Тамань компании Илья Косых',
        'Viterra продала 50% Зернового терминального комплекса «Тамань» компании '
        '«Доставка морем» Ильи Косых',
    ),
    'g0dea398b': (
        'Sminex приобрел финскую Fazer у производителя хлеба',
        'БКХ «Коломенский» Алексея Тулупова, владельца Sminex, купил российский '
        'бизнес финской Fazer',
    ),
}

NEW_SRC = {
    'g0dea398b': [
        ['Интерфакс', 'https://www.interfax.ru/business/838754'],
        ['Msk1.ru', 'https://msk1.ru/text/business/2022/04/29/71298113/'],
    ],
}


def main(write=False):
    # Файл перечитывается прямо перед записью — чужие пуши не затираются.
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    cards = {d['id']: d for d in data['deals']}
    changed = 0
    for deal_id, (old, new) in TITLES.items():
        card = cards[deal_id]
        if card['title'] == new:
            print('%s: заголовок уже исправлен' % deal_id)
            continue
        assert card['title'] == old, (deal_id, card['title'])
        print('%s: %s\n        -> %s' % (deal_id, old, new))
        card['title'] = new
        changed += 1
    for deal_id, pairs in NEW_SRC.items():
        card = cards[deal_id]
        have = {s[1] for s in card.get('src') or []}
        for pair in pairs:
            if pair[1] not in have:
                print('%s: + источник %s' % (deal_id, pair[1]))
                card.setdefault('src', []).append(pair)
                changed += 1
    if not changed:
        print('Править нечего.')
        return
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано: %d изменений.' % changed)
    else:
        print('Сухой прогон — запись с ключом --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
