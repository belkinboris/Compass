# -*- coding: utf-8 -*-
"""Побочная находка при чистке жаргона «Dealsma» (карточка c2d0c1dcd,
«Ростех выставил на продажу имущество НПК «Северная заря»»): проверка
источника (rt-capital.ru — сама площадка торгов, а не Telegram) вскрыла
три отдельных дефекта одной и той же карточки:

1. `status` отсутствовал вовсе, хотя площадка прямо пишет «Актив
   реализован» — аукцион завершён, а не только объявлен.
2. `sum`/`eco.sum` несли «1,115 млрд ₽» — это СТАРТОВАЯ цена лота
   («Стартовая цена: 1 115 000 000 рублей» на странице торгов), а не
   цена продажи. Настоящая цена продажи (892 млн ₽) уже верно стояла в
   `eco.val`, просто не была продублирована в headline-поле суммы — та
   же ошибка класса «стартовая цена вместо цены сделки», что уже
   чинилась для карточки «Открытие»/«Харьяга» (g66bb0d00) в этом же
   заходе месячной очереди.
3. `src` был подписан «@dealsma (Telegram)», хотя ссылка ведёт на
   rt-capital.ru — сайт самой площадки торгов, а не на Telegram-пост;
   и `eco.context` дословно дублировал «Telegram-канал dealsma
   опубликовал информацию...» — тот же класс жаргона, что уже почищен
   в этом заходе в четырёх других карточках (см. `fix_dealsma_jargon_
   leak_in_extra.py`), только здесь копия сидела в `eco.context`,
   а не в `extra`.

Проверено лично прямым WebFetch (rt-capital.ru/deals/19192/):
«Земельно-имущественный комплекс г. Санкт-Петербург»; «Стартовая
цена: 1 115 000 000 рублей», «Цена реализации: 892 000 000 рублей»,
«Статус: Актив реализован», «Победитель торгов: ООО «АНТРЕСОЛЬ»» —
это официальная площадка АО «РТ-Капитал» (актив «Ростеха»),
организующая продажу непрофильного имущества.

Запуск: python3 pipeline/fix_severnaya_zarya_price_status_and_source.py
        python3 pipeline/fix_severnaya_zarya_price_status_and_source.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'c2d0c1dcd'

OLD_SUM = '1,115 млрд ₽'
NEW_SUM = '892 млн ₽'

OLD_ECO_CONTEXT = (
    'Telegram-канал dealsma опубликовал информацию о выставлении на '
    'продажу имущества научно-производственного комплекса «Северная '
    'заря», принадлежащего Ростеху.'
)
NEW_ECO_CONTEXT = (
    'Стартовая цена лота на торгах составляла 1,115 млрд ₽ — итоговая '
    'цена продажи (892 млн ₽) оказалась ниже стартовой.'
)

OLD_SRC = [['@dealsma (Telegram)', 'https://rt-capital.ru/deals/19192/']]
NEW_SRC = [['РТ-Капитал', 'https://rt-capital.ru/deals/19192/']]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert 'status' not in deal
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print('Закрыта')
    print('\n=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = 'Закрыта'
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
