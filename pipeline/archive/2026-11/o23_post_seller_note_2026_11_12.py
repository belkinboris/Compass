# -*- coding: utf-8 -*-
"""Карточка очереди g90767425 («О23» / Ozon): справка о продавце в проекте поста.

Правка владельца 12 ноября 2026: в строке продавца коротко сказать, чем известен
Чачава, — только по источникам карточки. Frank Media: «Чачава — управляющий партнер
инвестфирмы LETA Capital… Кроме пакета акций Ozon, в портфеле у Чачавы на апрель 2026
года было 19,69% акций «Яндекса»»; РБК: «В феврале этого года структуры Чачавы увеличили
долю в «Яндексе» с 15,97 до 19,69%». My.Games не называем: ее в тот же день выкупают
менеджеры. Меняется одна строка заданного текста поста (`post_override`).

    python3 pipeline/archive/2026-11/o23_post_seller_note_2026_11_12.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'g90767425'
OLD = '<b>Продавец:</b> Александр Чачава\n'
NEW = ('<b>Продавец:</b> Александр Чачава — управляющий партнер LETA Capital, акционер «Яндекса» '
       '(19,69% на апрель 2026 года)\n')


def apply(doc):
    c = next(x for x in doc['cards'] if x['id'] == CID)
    text = c['post_override']
    if NEW in text:
        return False
    assert text.count(OLD) == 1, text
    c['post_override'] = text.replace(OLD, NEW)
    return True


def main(write):
    changed = apply(json.loads(open(PENDING, encoding='utf-8').read()))
    if not write:
        print('Сухой прогон: строка продавца %s. Запись — с ключом --write.' % ('будет заменена' if changed else 'уже заменена'))
        return 0
    fresh_raw = open(PENDING, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    if apply(fresh):
        with open(PENDING, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
