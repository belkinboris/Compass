# -*- coding: utf-8 -*-
"""MOL/NIS/«Газпром нефть» (`gb6b371c3`): президент Сербии Александр Вучич
27 августа 2026 года допустил завершение сделки в сентябре (Коммерсантъ, со
ссылкой на сербское издание Danas). Дописано в eco.context вместе с
уточнением условий соглашения Сербии и MOL о будущем управлении NIS
(выкуп ещё 5% акций властями страны, гарантия работы завода не менее
10 лет на прежней мощности) — оба факта из того же источника.

Цитата не лежит в тексте старых источников — тот же приём, что и в прежних
правках этого поля: старое значение сохраняется, дописывается новое
предложение со ссылкой на источник.

Запуск: python3 pipeline/fix_mol_nis_vucic_september_timing.py           # проверка
        python3 pipeline/fix_mol_nis_vucic_september_timing.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb6b371c3'
OLD_CONTEXT = (
    'Управление по контролю за иностранными активами (OFAC) Минфина США '
    'продлило до 28 августа венгерской MOL лицензию, позволяющую вести '
    'переговоры с российской "Газпром нефтью" по покупке-продаже сербской '
    'компании NIS, сообщает в пятницу сербское издание РТС. Предыдущая '
    'аналогичная лицензия действовала до 31 июля.'
)
ADDITION = (
    '27 августа 2026 года президент Сербии Александр Вучич заявил, что '
    'венгерская MOL может завершить сделку в сентябре, добавив, что '
    'ситуация не может быть урегулирована без учёта позиции американской '
    'стороны. В середине июня стало известно, что Сербия и MOL подписали '
    'соглашение о будущем управлении NIS, по которому власти страны должны '
    'выкупить ещё 5% акций NIS; сам нефтеперерабатывающий завод продолжит '
    'работать как минимум 10 лет на той же мощности, что была последние '
    'четыре года до введения санкций США.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8909879']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    assert card.get('status') == 'Обсуждается', 'статус уже другое'
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
