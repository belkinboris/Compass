# -*- coding: utf-8 -*-
"""«Фаберлик»/«Воентекстильпром» (`gbc0b68bd`): `sum` и `eco.sum` несли
«150 млн ₽» как раскрытую цену сделки. Оба уже процитированных источника
карточки (Ведомости, Retail.ru) прямо говорят обратное: «Цена сделки по
продаже ООО «Фэшн фэктори» на текущий момент времени неизвестна.
Гендиректор «INFOLine-аналитики» Михаил Бурмистров оценил стоимость
актива в сумму не более 150 млн руб.» (Retail.ru) — это экспертная
оценка, а не факт, компании цену не раскрывали. По правилу CLAUDE.md
(«Сумма пишется одним способом», пометка недостоверности — только
«(по оценке)», без имени оценщика) добавляем пометку.

`sum` проверяется `sum_is_supported()` в review.py — эта проверка САМА
ТРЕБУЕТ пометку «(по оценке)», когда цитата говорит об оценке, и приняла
бы эту правку через FIXES. `eco.sum` идёт через общую дословную проверку
без скидки на смысл (см. уже записанный урок в CLAUDE.md про разные
проверки sum/eco.sum) — «150 млн ₽ (по оценке)» не лежит в цитате
дословно как непрерывный кусок, поэтому оба поля правятся здесь разовым
скриптом для единообразия, а не raздельно.

Запуск: python3 pipeline/fix_faberlik_voentekstilprom_sum_estimate.py           # проверка
        python3 pipeline/fix_faberlik_voentekstilprom_sum_estimate.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbc0b68bd'
OLD_SUM = '150 млн ₽'
NEW_SUM = '150 млн ₽ (по оценке)'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('sum') == OLD_SUM, 'sum изменился с ожидаемого: %r' % card.get('sum')
    assert card['eco'].get('sum') == OLD_SUM, (
        'eco.sum изменился с ожидаемого: %r' % card['eco'].get('sum'))
    print('ПРАВИМ  %s: sum — добавлена пометка «(по оценке)»' % CARD_ID)
    print('ПРАВИМ  %s: eco.sum — та же пометка' % CARD_ID)
    if write:
        card['sum'] = NEW_SUM
        card['eco']['sum'] = NEW_SUM
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
