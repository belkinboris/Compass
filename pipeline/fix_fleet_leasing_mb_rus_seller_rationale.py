# -*- coding: utf-8 -*-
"""«Флит Лизинг»/МБ РУС Финанс (`gab0f3dde`): почасовой отсев сомнительного
сырья 22 августа нашёл среди старых нерешённых черновиков вторую статью
Коммерсанта о ТОЙ ЖЕ сделке (doc/8875136, от 07.08.2026) — с цитатой
ПРОДАВЦА (гендиректор «Автодома» Андрей Ольховский), которой в карточке
не было: `eco.rationale` уже нёс цитату покупателя (Сергей Савинов),
из ДРУГОГО источника (doc/8864724). review.py проверяет `new` целиком
против ОДНОЙ цитаты из ОДНОГО кэшированного текста — слить две цитаты из
двух разных статей в одно поле через таблицу FIXES нельзя технически
(та же граница, что уже документирована для fix_okto_zapadnaya_followup.py).
Разовый скрипт: конкатенация с assert на исходное значение, тем же
приёмом.

Запуск: python3 pipeline/fix_fleet_leasing_mb_rus_seller_rationale.py           # проверка
        python3 pipeline/fix_fleet_leasing_mb_rus_seller_rationale.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gab0f3dde'

OLD_RATIONALE = (
    '«Флит Лизинг последовательно реализует стратегию роста, сочетая '
    'органическое развитие с точечными сделками по приобретению '
    'лизинговых активов. Это позволяет ускорить масштабирование бизнеса. '
    'Для клиентов МБ РУС Финанс мы обеспечим преемственность обслуживания '
    'и доступ ко всей линейке продуктов и сервисов компании», — отмечает '
    'гендиректор «Флит Лизинга» Сергей Савинов.')
NEW_RATIONALE = OLD_RATIONALE + (
    ' Гендиректор «Автодома» Андрей Ольховский сообщил "Ъ", что решение о '
    'продаже «связано с изменением среднесрочных прогнозов в части '
    'развития компании». «На текущий момент нами выбрана стратегия '
    'продажи ряда активов для сокращения финансовых обязательств и '
    'формирования финансовой подушки»,— добавил он, также отказавшись '
    'раскрыть сумму сделки.')

NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8875136']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('rationale') == OLD_RATIONALE, (
        'eco.rationale уже изменилось: %r' % card['eco'].get('rationale'))
    existing_srcs = [tuple(s) for s in card.get('src') or []]
    assert tuple(NEW_SRC) not in existing_srcs, 'источник уже привязан'

    print('ДО:', card['eco']['rationale'])
    print('ПОСЛЕ:', NEW_RATIONALE)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['rationale'] = NEW_RATIONALE
    card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
