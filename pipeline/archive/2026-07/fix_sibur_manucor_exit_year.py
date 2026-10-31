# -*- coding: utf-8 -*-
"""Карточка g2369d101 («Дочка Сибура вышла из капитала итальянского
производителя БОПП-пленки Manucor») несла год «2025» вместо 2023.

ЧТО СЛОМАНО. Поле `date` стояло «2025-01-16» — день и месяц совпадают с
источником, а год нет. Interfax прямо пишет: «A complex operation was
completed on 16 January 2023 and, as a result, Biaxplen LLC, a company in
the Russian Sibur Group, exited Manucor's shareholding structure» (сделка
2019 года о ВХОДЕ Сибура в капитал Manucor уже описана Ведомостями отдельно
— здесь речь о ВЫХОДЕ, и он состоялся именно 16 января 2023, а не 2025).
Число и месяц («16 января») в карточке верны — год-заглушка компактного
импорта поставила не тот год, ровно как у cb50ea645 (см.
fix_sayanskhimplast_auction_year.py) и серии fix_2025_bulk_year_placeholder*.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником, а не автоматической правкой в общей таблице.

Карточка этим переносом выходит из среза 2025 года (переходит в 2023).

Запуск:
    python3 pipeline/fix_sibur_manucor_exit_year.py            # сухой прогон
    python3 pipeline/fix_sibur_manucor_exit_year.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'g2369d101'
OLD_DATE = '2025-01-16'
NEW_DATE = '2023-01-16'
QUOTE = ('Interfax: "A complex operation was completed on 16 January 2023 '
         'and, as a result, Biaxplen LLC, a company in the Russian Sibur '
         'Group, exited Manucor\'s shareholding structure"')


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
