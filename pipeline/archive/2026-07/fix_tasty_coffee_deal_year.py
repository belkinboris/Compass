# -*- coding: utf-8 -*-
"""Карточка gf9b54ee7 («Фонд «Восток Инвестиции» купил 20% в производителе
спешелти-кофе Tasty Coffee») несла год «2025» вместо 2026.

ЧТО СЛОМАНО. Поле `date` стояло «2025» (год без месяца и дня) — источник,
на который ссылается сама карточка (Forbes), пересказан и Коммерсантом, и
Ведомостями, и оба прямо датируют сделку 22 апреля 2026 года. Коммерсантъ:
«22.04.2026, 10:57 ... Частный инвестхолдинг «Восток Инвестиции» купил 20%
бизнеса по производству и поставке свежеобжаренного кофе в зернах Tasty
Coffee». Ведомости независимо подтверждают дату (WebFetch того же URL):
«22 апреля 2026 года». Год-заглушка компактного импорта поставила не тот
год — родня cb50ea645 и g2369d101 (fix_sayanskhimplast_auction_year.py,
fix_sibur_manucor_exit_year.py), только здесь исходно не было и месяца/дня,
их приносит эта же правка.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником, а не автоматической правкой в общей таблице.

Карточка этим переносом выходит из среза 2025 года (переходит в 2026).

Запуск:
    python3 pipeline/fix_tasty_coffee_deal_year.py            # сухой прогон
    python3 pipeline/fix_tasty_coffee_deal_year.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'gf9b54ee7'
OLD_DATE = '2025'
NEW_DATE = '2026-04-22'
QUOTE = ('Коммерсантъ, 22.04.2026, 10:57: «Частный инвестхолдинг «Восток '
         'Инвестиции» купил 20% бизнеса по производству и поставке '
         'свежеобжаренного кофе в зернах Tasty Coffee»; Ведомости '
         'независимо подтверждают дату публикации 22 апреля 2026 года')


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
