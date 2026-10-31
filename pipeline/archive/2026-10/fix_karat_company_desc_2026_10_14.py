# -*- coding: utf-8 -*-
"""Профиль компании `gd2c01a84` (Завод «Карат») держал только половину
истории — «Продан Александром Клячиным Александру Вознесенскому» — и
всплыл устаревшим в посте новой карточки `g62577a1d` (покупка
Павловского молочного завода): с декабря 2024 года владелец сменился
еще раз, на ЗПИФ «Формула доверия». Источник — тот же материал РБК
(через Mail.ru), что и у новой карточки.

Запуск:
    python3 fix_karat_company_desc_2026_10_14.py            # сухой прогон
    python3 fix_karat_company_desc_2026_10_14.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
COMPANY_ID = 'gd2c01a84'

OLD = 'Продан Александром Клячиным Александру Вознесенскому.'
NEW = ('Московский производитель плавленых и творожных сыров (бренды «Дружба», «Янтарь», '
       'Violette, «Карат Домашний»), работает с 1934 года. С декабря 2024 года принадлежит '
       'ЗПИФ «Формула доверия» (управляющая компания — «Солид Менеджмент») через ООО '
       '«Карат Инвестиции»; до этого, с сентября 2023 года, владельцем был Александр '
       'Вознесенский, купивший завод у структуры Александра Клячина.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    company = data['companies'][COMPANY_ID]
    assert company['desc'] == OLD

    print('ПРАВКА %s: desc' % COMPANY_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    company['desc'] = NEW
    fresh = json.load(open(DATA, encoding='utf-8'))
    assert fresh['companies'][COMPANY_ID]['desc'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh['companies'][COMPANY_ID] = company
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
