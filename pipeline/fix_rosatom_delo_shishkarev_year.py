# -*- coding: utf-8 -*-
"""Карточка gd7c2b9ee («Росатом выкупает 51% акций группы «Дело» у Сергея
Шишкарева») несла год «2025» вместо 2026.

ЧТО СЛОМАНО. Поле `date` стояло «2025» (год без месяца и дня). Коммерсантъ
датирует решение Росатома 6 июля 2026 года и восстанавливает всю цепочку
событий: «зимой начали процедуру «корпоративной рулетки»... «Росатом»
20 февраля сделал оферту господину Шишкареву... 30 июня истек срок,
отведенный на выкуп... Инициатива перешла к госкорпорации» — то есть офер,
дедлайн и итоговое решение Росатома целиком лежат в 2026 году, а не в 2025.
Год-заглушка компактного импорта поставила не тот год — родня cb50ea645,
g2369d101, gf9b54ee7.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником, а не автоматической правкой в общей таблице.

Карточка остаётся в 2026 году после переноса (выходит из среза 2025).

Запуск:
    python3 pipeline/fix_rosatom_delo_shishkarev_year.py            # сухой прогон
    python3 pipeline/fix_rosatom_delo_shishkarev_year.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'gd7c2b9ee'
OLD_DATE = '2025'
NEW_DATE = '2026-07-06'
QUOTE = ('Коммерсантъ, 06.07.2026, 20:45: «"Росатом" принял корпоративное '
         'решение выкупить у Сергея Шишкарева его 51% в ГК "Дело"»; далее '
         'по тексту: «"Росатом" 20 февраля сделал оферту... 30 июня истек '
         'срок, отведенный на выкуп»')


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
