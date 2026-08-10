# -*- coding: utf-8 -*-
"""У карточки `g8f638d63» («Новосталь-М приобрела металлотрейдера «Ариэль
Металл»») `date` стоял «2022» — единственный источник карточки сам
датирован 17 апреля 2023 года («AK&M 17 апреля 2023») и озаглавлен
«Новосталь-М МОЖЕТ купить «Ариэль Металл»» (ФАС только удовлетворила
ходатайство). Независимая проверка живым поиском подтверждает: сама
сделка была закрыта в МАРТЕ 2023 года («Торговая Компания Новосталь-М
завершила сделку по приобретению металлотрейдера Ариэль Металл»,
metalinfo.ru), а не в 2022-м. Точный день закрытия источники не называют
— в дату идёт только год, тот же принцип, что и у других заглушек.

Почему не через review.py: перенос в другой год не поддержан намеренно
(см. прецедент `fix_osnova_sviblovo_date.py`), а факт о марте 2023 года
подтверждён живым поиском, а не дословным кэшем притока.

Запуск: python3 pipeline/fix_novostal_ariel_metall_date.py
        python3 pipeline/fix_novostal_ariel_metall_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g8f638d63'
OLD_DATE = '2022'
NEW_DATE = '2023'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == OLD_DATE, '%s: дата уже другая' % CARD_ID
    print('ПРАВИМ  %s date: «%s» -> «%s»' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
