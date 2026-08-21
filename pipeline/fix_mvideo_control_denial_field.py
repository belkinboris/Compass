# -*- coding: utf-8 -*-
"""М.видео, второй раунд допэмиссии (`gb5d8a18a`): официальное опровержение
смены контроля лежало в `eco.fin` — а это поле на экране подписано
«Форма расчётов». Отрицание смены контроля — не форма расчётов: факт
дословный и верный, но записан в чужое поле. Тот же класс, что вчерашний
`law.terms` у HeadHunter/Happy Job (дословность не означает уместность в
поле) — только мягче: факт релевантен сделке, промахнулась лишь полка.

Правильная полка — «Структура» (`law.struct`): там уже стоит родное
предложение о том, что покупатели размещения — сама компания и структуры
текущих собственников, и опровержение смены контроля его прямо дополняет.
Переносим вторым предложением туда, `eco.fin` возвращаем в честную
заглушку.

Заодно — подпись источника: рутина подписала ссылку на
finance.rambler.ru именем «ComNews» (издание-первоисточник перепечатки).
Правило площадки — подпись по ДОМЕНУ ссылки («Источник — то, что
подтверждает факт»); домен добавлен в таблицу `source_names.py`
(«Рамблер»), подпись исправляется по ней.

Запуск: python3 pipeline/fix_mvideo_control_denial_field.py           # проверка
        python3 pipeline/fix_mvideo_control_denial_field.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import source_names  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb5d8a18a'
DENIAL = ('В компании отметили, что решение не связано с изменениями '
          'структуры контроля или какими-либо корпоративными '
          'изменениями подобного рода.')
STRUCT = ('Покупатели размещения - не новые инвесторы с открытого '
          'рынка, а сама компания и структуры, связанные с ее '
          'текущими собственниками.')
RAMBLER_URL = ('https://finance.rambler.ru/business/56905711-m-video-sygraet-'
               'v-zakrytuyu-kompaniya-namerena-poluchit-aktsiyami-30-mlrd-rub/')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('fin') == DENIAL, (
        'ожидали eco.fin с опровержением, сейчас %r' % card['eco'].get('fin'))
    assert card['law'].get('struct') == STRUCT, (
        'ожидали law.struct с одним предложением о покупателях, сейчас %r'
        % card['law'].get('struct'))
    src_entry = next((s for s in card.get('src') or []
                      if len(s) > 1 and s[1] == RAMBLER_URL), None)
    assert src_entry is not None, 'ссылка на rambler не найдена в src'
    new_label = source_names.edition_label(RAMBLER_URL)
    assert new_label == 'Рамблер', 'таблица доменов не знает rambler: %r' % new_label

    print('ПРАВИМ %s:' % CARD_ID)
    print('  law.struct += опровержение смены контроля (из eco.fin)')
    print('  eco.fin -> «—» (поле «Форма расчётов» — не место для этого факта)')
    print('  src: %r -> %r (подпись по домену ссылки)' % (src_entry[0], new_label))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['law']['struct'] = STRUCT + ' ' + DENIAL
    card['eco']['fin'] = '—'
    src_entry[0] = new_label
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
