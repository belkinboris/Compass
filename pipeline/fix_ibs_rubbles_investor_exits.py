# -*- coding: utf-8 -*-
"""IBS/Rubbles (`gda6baa02`): почасовой приток 24 августа нашёл второй
источник о той же сделке (mergers.ru, отсылка Русского венчура) с историей
выхода венчурных инвесторов — МТС Венчурного фонда (2022, 200 млн ₽, не
более 10%) и FinSight Ventures (вышел в 2024-м), которой в карточке не
было: `eco.context` уже нёс историю партнёрства IBS/Rubbles из ДРУГОГО
источника (CNews). review.py проверяет `new` целиком против ОДНОЙ цитаты
из ОДНОГО кэшированного текста — слить две цитаты из двух разных статей в
одно поле через таблицу FIXES нельзя технически (та же граница, что уже
документирована для fix_okto_zapadnaya_followup.py и
fix_fleet_leasing_mb_rus_seller_rationale.py). Разовый скрипт: конкатенация
с assert на исходное значение, тем же приёмом.

Запуск: python3 pipeline/fix_ibs_rubbles_investor_exits.py           # проверка
        python3 pipeline/fix_ibs_rubbles_investor_exits.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gda6baa02'

OLD_CONTEXT = (
    'На протяжении последних трех лет IBS и Rubbles находились в статусе '
    'технологических партнеров и реализовывали совместные проекты, в ходе '
    'которых разработки Rubbles подтвердили свою эффективность и '
    'надежность в решении прикладных бизнес-задач.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Как отмечает Русский венчур, это экзит для венчурного фонда МТС, '
    'который в 2022 году вложил в проект 200 млн рублей. Тогда в МТС '
    'заявили, что получили не более 10% компании. В 2016 году стартап '
    'закрыл первый раунд инвестиций на $1,5 млн от фонда FinSight '
    'Ventures, одним из основателей которого является Виктор Ремша, '
    'создатель "Финама". В декабре 2021 года стартап получил $6 млн от '
    'фондов Elbrus Capital Fund III и FinSight Ventures. Средства '
    'планировалось потратить в том числе на выход на рынки Западной '
    'Европы, Ближнего Востока и Юго-Восточной Азии, но компания отложила '
    'эти планы из-за нестабильной геополитической обстановки. В FinSight '
    'Ventures подтвердили, что фонд вышел из капитала Rubbles еще в '
    '2024 году.')

NEW_SRC = ['Mergers.ru',
           'https://mergers.ru/news/IBS-priobrela-razrabotchika-IT-'
           'reshenij-na-baze-iskusstvennogo-intellekta-Rubbles-87419']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context уже изменилось: %r' % card['eco'].get('context'))
    existing_srcs = [tuple(s) for s in card.get('src') or []]
    assert tuple(NEW_SRC) not in existing_srcs, 'источник уже привязан'

    print('ДО:', card['eco']['context'])
    print('ПОСЛЕ:', NEW_CONTEXT)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
