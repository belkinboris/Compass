# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — две карточки без `status` вовсе
(та же болезнь, что у `c43cb8f80`/Нижфарм и `c4e275305`/ФЕСКО в
предыдущие два часа — замер по всей базе в прошлый час нашёл 75 таких
карточек).

1) `c29710ac5» (ЭФКО через Эксойл покупает МЭЗ Bunge под Воронежем,
   «Масленица»). Личный WebFetch (interfax.ru/business/1044618,
   29.08.2025): «Компания "ЭФКО" увеличила с 31,4% до 100% долю в ООО
   "Агроинвест", которая контролирует ООО "Масленица"» — то есть ЭФКО
   владеет «Масленицей» не напрямую, а через промежуточную структуру
   «Агроинвест»; «Изменения отражены в ЕГРЮЛ с 27 августа». Дата
   уточнена с «2025» (год) до «2025-08-27», статус — «Закрыта»,
   структурная деталь про «Агроинвест» добавлена в `law.appr`.

2) `ce7b84bec» (Сбербанк Капитал/КР Плюс выставили на торги «Юг
   Девелопмент» с «Даниловской мануфактурой»). Собственный текст
   карточки в `eco.context` уже описывает состоявшуюся продажу («18
   декабря... прошла... продажа... Цена продажи — 12,3 млрд рублей»,
   источник — РИА Недвижимость от 22.12.2025) — карточка лишь не
   получила `status`. Выставлено «Закрыта».

Поля `eco.context` (обе карточки) уже проходили вычитку — за основу
взят ТЕКУЩИЙ текст с диска.

Запуск:
    python3 pipeline/fix_efko_maslenitsa_and_danilovskaya_status.py            # сухой прогон
    python3 pipeline/fix_efko_maslenitsa_and_danilovskaya_status.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_DATE_1 = '2025'
NEW_DATE_1 = '2025-08-27'
OLD_APPR_1 = (
    'ГК «Эфко» получила разрешение ФАС на приобретение ООО «Масленица». '
    'Доля группы в этой компании вырастет с нынешних 31,4% до 100%.'
)
NEW_APPR_1 = OLD_APPR_1 + (
    ' По данным ЕГРЮЛ, доля увеличена не напрямую, а через контролирующую '
    'структуру ООО «Агроинвест»: изменения отражены в реестре с 27 '
    'августа 2025 года.'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    c1 = by_id['c29710ac5']
    c2 = by_id['ce7b84bec']

    assert c1.get('status') is None, 'c29710ac5 status уже занят: %r' % (c1.get('status'),)
    assert c1['date'] == OLD_DATE_1, 'c29710ac5 date уже другая: %r' % (c1['date'],)
    assert c1['law']['appr'] == OLD_APPR_1, 'c29710ac5 law.appr уже другой: %r' % (c1['law']['appr'],)
    assert c2.get('status') is None, 'ce7b84bec status уже занят: %r' % (c2.get('status'),)

    print('c29710ac5: status None -> "Закрыта"; date %r -> %r; law.appr дополнен' %
          (OLD_DATE_1, NEW_DATE_1))
    print('ce7b84bec: status None -> "Закрыта"')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    c1['status'] = 'Закрыта'
    c1['date'] = NEW_DATE_1
    c1['law']['appr'] = NEW_APPR_1
    c2['status'] = 'Закрыта'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
