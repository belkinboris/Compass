# -*- coding: utf-8 -*-
"""У карточки `g39752167` («Highland Gold приобрела 100% российских активов
Kinross Gold») `sum`/`eco.sum` несли «$680 млн» — это ПЕРВОНАЧАЛЬНО
объявленная цена. Собственное поле `law.appr» этой же карточки уже честно
рассказывает, что случилось дальше: «Российская подкомиссия по контролю за
иностранными инвестициями одобрила сделку лишь на сумму не более $340 млн,
и итоговая цена была снижена вдвое: $300 млн Kinross получила при закрытии,
ещё $40 млн — через год» — источники (kommersant.ru/doc/5411619,
vedomosti.ru) подтверждают дословно: «которая одобрила сделку при условии,
что ее стоимость не будет превышать 340 миллионов долларов США». Тот же
класс дефекта, что уже чинили для Nokian/«Татнефть» в партии 1 (первичная
цена вместо фактически одобренной/уплаченной).

Почему не через review.py: `sum_is_supported()` проверяет формат только
для рублёвых сумм («N[–M] млн|млрд ₽») — валютные суммы в долларах через
таблицу FIXES провести нельзя (тот же формат-барьер, что и у €285 млн для
Nokian).

Запуск: python3 pipeline/fix_highland_gold_kinross_sum.py
        python3 pipeline/fix_highland_gold_kinross_sum.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g39752167'
OLD_SUM = '$680 млн'
NEW_SUM = '$340 млн'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['sum'] == NEW_SUM and card['eco']['sum'] == NEW_SUM:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['sum'] == OLD_SUM, '%s: sum уже другой' % CARD_ID
    assert card['eco']['sum'] == OLD_SUM, '%s: eco.sum уже другой' % CARD_ID
    print('ПРАВИМ  %s sum и eco.sum: «%s» -> «%s» (фактически одобрено и '
          'уплачено, а не изначально объявленная цена)' % (CARD_ID, OLD_SUM, NEW_SUM))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
