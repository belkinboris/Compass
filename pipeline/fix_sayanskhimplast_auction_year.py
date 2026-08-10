# -*- coding: utf-8 -*-
"""Карточка cb50ea645 («Продажа имущества АО «Саянскхимпласт» и дочерних
компаний на аукционе ПСБ») несла год «2025» вместо 2026.

ЧТО СЛОМАНО. Поле `date` стояло «2025-04-13» — день и месяц совпадают с
источником, а год нет. AK&M прямо датирует материал «03 апреля 2026 16:20»
и пишет об аукционе как о предстоящем событии этого же года: «ПСБ 4 апреля
открывает приём заявок... Приём заявок заканчивается 10 апреля, аукцион в
формате онлайн пройдёт 13 апреля». Число и месяц («13 апреля») в карточке
верны — год-заглушка компактного импорта поставила не тот год.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником (см. уроки CLAUDE.md про gd6b3c796, ge0f7b957,
серию fix_2025_bulk_year_placeholder*.py), а не автоматической правкой в
общей таблице.

Карточка этим переносом выходит из среза 2025 года.

Запуск:
    python3 pipeline/fix_sayanskhimplast_auction_year.py            # сухой прогон
    python3 pipeline/fix_sayanskhimplast_auction_year.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'cb50ea645'
OLD_DATE = '2025-04-13'
NEW_DATE = '2026-04-13'
QUOTE = ('AK&M датирует материал «03 апреля 2026 16:20»; «ПСБ 4 апреля '
         'открывает приём заявок... аукцион в формате онлайн пройдёт '
         '13 апреля»')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('date') == OLD_DATE, \
        'дата уже другая: %r, ожидали %r' % (deal.get('date'), OLD_DATE)

    print('%s: date %r -> %r' % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('  цитата: %r' % QUOTE)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['date'] = NEW_DATE
    assert deal['date'] == NEW_DATE, 'дата не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
