# -*- coding: utf-8 -*-
"""Карточка `g688aa290` («Michelin продаёт завод по производству шин в
России компании Пауэр Интернешнл») несла сразу три связанных дефекта,
все из одного и того же устаревшего снимка сделки:

- `date`=«2022» — единственный источник (interfax.ru/business/903364)
  сам датирован «13:18, 26 мая 2023», то есть сделка более чем на год
  младше заглушки компактного импорта.
- `status`=«Обсуждается» при заголовке источника «Michelin ПРОДАЛА
  российский бизнес» — сделка уже закрыта, а не обсуждается.
- `eco.rationale`/`extra` дословно повторяли друг друга и несли фразу
  «Статус: в процессе закрытия» — устаревшую формулировку, прямо
  противоречащую заголовку источника («продала», а не «продаёт»/«в
  процессе»). Заменены описанием закрытой сделки с именем покупателя,
  его бенефициара и вошедших в периметр активов.
- `eco.target_fin` стоял прочерком — источник называет выручку цели
  за 2022 год.

Почему не через review.py: перенос в другой год не поддержан
`date_is_supported()` намеренно (см. прецедент
`fix_osnova_sviblovo_date.py`); переписанный `eco.rationale` — не
дословный перенос одного непрерывного куска цитаты (в источнике между
нужными предложениями врезана ссылка на другую статью «Экономика 28
июня 2022 Производитель шин Michelin решил уйти из РФ...»), а сборка
факта из уже подтверждённых частей текста, поэтому проверяется `assert`
на исходное состояние, а не `quote_is_real()`.

Запуск: python3 pipeline/fix_michelin_power_international.py
        python3 pipeline/fix_michelin_power_international.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g688aa290'
OLD_TEXT = ('Статус: в процессе закрытия. Возможна опция обратного выкупа '
            'в условиях контракта.')
NEW_TEXT = ('Michelin продала российский бизнес местному дистрибьютору '
            'ООО «Пауэр Интернэшнл-шины» (100% долей — у предпринимателя '
            'Евгения Дробницы): производственную компанию «Мишлен» '
            '(шинный завод в подмосковном Давыдове) и Camso CIS. Сумма '
            'сделки не раскрывается. Возможна опция обратного выкупа в '
            'условиях контракта.')
NEW_TARGET_FIN = ('Выручка ООО «Пауэр Интернэшнл-шины» по итогам 2022 '
                   'года превысила 31 млрд руб. (+15%).')


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    done = (card['date'] == '2023-05-26' and card['status'] == 'Закрыта'
            and card['eco']['rationale'] == NEW_TEXT
            and card['eco']['target_fin'] == NEW_TARGET_FIN)
    if done:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['date'] == '2022', 'дата уже другая'
    assert card['status'] == 'Обсуждается', 'статус уже другой'
    assert card['eco']['rationale'] == OLD_TEXT, 'eco.rationale уже другое'
    assert card['extra'] == OLD_TEXT, 'extra уже другое'
    assert card['eco']['target_fin'] == '—', 'eco.target_fin уже другое'
    print('ПРАВИМ  %s date: «2022» -> «2023-05-26»' % CARD_ID)
    print('ПРАВИМ  %s status: «Обсуждается» -> «Закрыта»' % CARD_ID)
    print('ПРАВИМ  %s eco.rationale/extra: устаревшая формулировка заменена' % CARD_ID)
    print('ПРАВИМ  %s eco.target_fin: заполнена выручка цели' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['date'] = '2023-05-26'
    card['status'] = 'Закрыта'
    card['eco']['rationale'] = NEW_TEXT
    card['extra'] = NEW_TEXT
    card['eco']['target_fin'] = NEW_TARGET_FIN
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
