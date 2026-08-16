# -*- coding: utf-8 -*-
"""Дочитывание REVISION_BRIEF, партия 6: adv-erlan несёт неверный год.

Карточка стояла `date: "2026-01-30"`. Источник, УЖЕ указанный в `src` самой
карточки (Sostav.ru), несёт дословную дату публикации «04.07.2025 в 16:03»:
«В состав акционеров медийного контура АДВ вошла группа стратегических
инвесторов АО «Эрлан»». Независимо подтверждено вторым источником
(adpass.ru): «Группа стратегических инвесторов АО «Эрлан» вошла в состав
акционеров медийного контура АДВ в июле 2025 года — уже в разгар
корпоративного конфликта».

Расхождение и по году, и по месяцу — `review.py` намеренно не умеет менять
год (см. докстрока `date_is_supported()`): смена года слишком похожа на
«утверждение нового», чтобы проходить лёгким механическим путём уточнения
дня. Прецедент того же класса — `fix_osnova_sviblovo_date.py`.

Запуск:
    python3 pipeline/fix_adv_erlan_date.py            # сухой прогон
    python3 pipeline/fix_adv_erlan_date.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_DATE = '2026-01-30'
NEW_DATE = '2025-07-04'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'adv-erlan')
    assert card['date'] == OLD_DATE, 'дата уже другая: %r' % card['date']
    print('%s  adv-erlan.date: %r -> %r'
          % ('ПИШЕМ' if write else 'ПРАВИМ (сухой прогон)', OLD_DATE, NEW_DATE))
    print('  + источник в src карточки (Sostav.ru) датирован 04.07.2025, '
          'независимо подтверждено adpass.ru («в июле 2025 года»)')
    if write:
        card['date'] = NEW_DATE
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1,
                   ensure_ascii=False)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
