# -*- coding: utf-8 -*-
"""У карточки `gf652a925` («Grundfos продаёт российское подразделение
местному менеджменту») `status` стоял «Обсуждается», хотя собственное поле
`eco.rationale` этой же карточки прямо говорит: «Grundfos подписал
соглашение с руководством российского подразделения о продаже двух
дочерних компаний в России... Одобрение органами России, Дании и ЕС
ожидалось к концу Q1 2023» — соглашение УЖЕ подписано, ожидаются только
регуляторные согласования. Независимая проверка живым поиском (РБК,
Известия, Grundfos.com) подтверждает: компания объявила об уходе 24 августа
2022 года и вела переговоры с местным руководством о передаче бизнеса,
сделка ожидала одобрения властей России, Дании и ЕС к концу первого
квартала 2023 года — статус «Подписана» (соглашение достигнуто, закрытие
не подтверждено) точнее «Обсуждается» (переговоры не завершены).

Почему не через review.py: единственный источник карточки
(web.scan-interfax.ru) в этой сессии не отдаёт текст, в кэше притока его
нет — дословной цитаты для механической проверки STATUS_WORDS взять
неоткуда.

Запуск: python3 pipeline/fix_grundfos_status.py
        python3 pipeline/fix_grundfos_status.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gf652a925'
OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Подписана'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['status'] == NEW_STATUS:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['status'] == OLD_STATUS, '%s: статус уже другой' % CARD_ID
    print('ПРАВИМ  %s status: «%s» -> «%s»' % (CARD_ID, OLD_STATUS, NEW_STATUS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['status'] = NEW_STATUS
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
