# -*- coding: utf-8 -*-
"""Дневная очередь дочитывания (G7, первый уровень, полный обыск),
19 сентября 2026: карточка `g88dfc8c8» («"Дом.РФ" продаёт старинную усадьбу
в Оренбурге») — «Цель сделки» стояла честной пустотой, хотя причина продажи
прямо названа в независимом источнике, которого раньше не было в `src`.

АиФ-Оренбург (oren.aif.ru, ранее в `src` не значился) объясняет прямо, зачем
«Дом.РФ» выставляет объект на продажу: здание годами стоит заброшенным и
разрушается. Проверено лично прямым WebFetch перед записью — цитата лежит
в источнике дословно.

Запуск: python3 pipeline/fix_orenburg_manor_sale_rationale.py           # проверка
        python3 pipeline/fix_orenburg_manor_sale_rationale.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g88dfc8c8'
OLD_RATIONALE = '—'

QUOTE = 'Вот уже несколько лет здание фактически заброшено и разрушается.'
NEW_RATIONALE = QUOTE

AIF_URL = 'https://oren.aif.ru/society/byvshiy-korpus-orenburgskogo-universiteta-hotyat-prodat-za-36-mln-rubley'


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card['eco'].get('rationale') == OLD_RATIONALE, (
        'eco.rationale уже другой: %r' % card['eco'].get('rationale'))
    assert flat(NEW_RATIONALE) in flat(QUOTE), 'значение не лежит дословно в цитате'

    print('НОВОЕ eco.rationale:')
    print(NEW_RATIONALE)

    if not write:
        print()
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['eco']['rationale'] = NEW_RATIONALE
    urls = {s[1] for s in (card.get('src') or []) if isinstance(s, list) and len(s) > 1}
    if AIF_URL not in urls:
        card.setdefault('src', []).append(['АиФ-Оренбург', AIF_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
