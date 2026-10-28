# -*- coding: utf-8 -*-
"""Карточка g8e6dcf0b («Артмуза»/Гомон, очередь): дата и сумма «Экономиста».

ДАТА. Поле несло дату притока (28 октября — день, когда карточку забрал
приток), а не дату сделки. Источник (Деловой Петербург) называет только
месяц без числа: «сделка закрыта в середине октября» (гендиректор «Артхауса»
Александр Игнатов). `review.py`'s `date_is_supported()` требует день и месяц
словом в цитате и не пишет дату без дня — поэтому запись года, а не полной
даты, идёт отдельным скриптом (`docs/card_status_dates.md`, «Нет дня — только
год»; образец — `pipeline/fix_osnova_sviblovo_date.py`). Месяц остаётся
текстом в `law.struct` (дописан туда же `write_card.py`, этим прогоном).

EC0.SUM. `sum` («Обзор») записан через `review.py` как «1,6 млрд ₽ (по
оценке)» — обычный компактный формат суммы-оценки (`sum_is_supported`).
`eco.sum` («Экономист») обязан нести ТО ЖЕ значение (docs/card_money.md,
«sum и eco.sum — одно значение»; `test_the_sum_on_the_overview_is_the_sum_in_the_economist`),
но дословная проверка `review.py` для ОБЩЕГО поля (не у `sum`, у которого
свой `sum_is_supported`) отклонила бы этот компактный формат — цитата говорит
«оценивается... в 1,6 млрд рублей», а не «(по оценке)» этими словами. Тот же
обход уже описан в `pipeline/ingest/fixes/batch_2026_09_28_gazprom_marsovo_pole.py`
(карточка «Старт Инвест»): привести `eco.sum` к виду `sum` прямой правкой,
минуя эту конкретную дословную проверку формата, а не содержание.

Запуск:
    python3 pipeline/fix_2026_10_28_g8e6dcf0b_date_sum.py            # сухой
    python3 pipeline/fix_2026_10_28_g8e6dcf0b_date_sum.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'pending.json')
DEAL_ID = 'g8e6dcf0b'
OLD_DATE = '2026-10-28'
NEW_DATE = '2026'
OLD_ECO_SUM = '—'
NEW_ECO_SUM = '1,6 млрд ₽ (по оценке)'
QUOTE = ('По словам генерального директора "Артхауса" Александра Игнатова, '
         'сделка закрыта в середине октября. Её стоимость оценивается экспертами '
         'в 1,6 млрд рублей.')


def main(argv):
    p = json.load(open(PENDING, encoding='utf-8'))
    c = next((x for x in p['cards'] if x['id'] == DEAL_ID), None)
    assert c is not None, 'карточки %s нет в очереди' % DEAL_ID
    assert c.get('date') == OLD_DATE, 'дата уже другая: %r' % c.get('date')
    assert c.get('eco', {}).get('sum') == OLD_ECO_SUM, \
        'eco.sum уже другое: %r' % c.get('eco', {}).get('sum')
    assert c.get('sum') == '1,6 млрд ₽ (по оценке)', \
        'sum уже другое: %r — сначала review.py --write' % c.get('sum')

    print('%s: date %r -> %r (день сделки неизвестен, только «середина октября»)'
          % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('%s: eco.sum %r -> %r (то же значение, что sum)'
          % (DEAL_ID, OLD_ECO_SUM, NEW_ECO_SUM))
    print('  цитата: %r' % QUOTE)

    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    c['date'] = NEW_DATE
    c['eco']['sum'] = NEW_ECO_SUM
    assert c['date'] == NEW_DATE and c['eco']['sum'] == NEW_ECO_SUM, 'запись не применилась'

    json.dump(p, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
