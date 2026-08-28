# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка ge3bc7c98 (ООО «Юнирест»
купило 90,01% долей ООО «ЭЙ КЕЙ РАША», ~97 ресторанов KFC, декабрь 2024):
дельта-поиск нашёл, что заявленный в `law.terms` план («не планирует
переименовывать свои точки... до 2035 года») НЕ подтвердился на практике —
Fontanka (15 января 2026) прямым текстом: «завершила ребрендинг точек KFC.
Заведений под старым брендом в России больше не осталось». Договорное право
использовать бренд до 2035 года никуда не делось (это отдельный факт про
условия), но реальный исход к началу 2026 года — полный ребрендинг, а не
сохранение вывески. Не через review.py: цитата из НОВОГО источника уточняет
(а не дословно продолжает) уже записанный факт.

Запуск: python3 pipeline/fix_unirest_kfc_rebrand_completed_law_terms.py
        python3 pipeline/fix_unirest_kfc_rebrand_completed_law_terms.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge3bc7c98'

OLD_TERMS = (
    'Именно «Эй Кей Раша», управляющая около 100 заведениями, заявляла, что '
    'не планирует переименовывать свои точки, большинство из которых могут '
    'использовать бренд KFC до 2035 года.'
)
TERMS_ADDITION = (
    ' На практике ребрендинг завершён раньше срока: по данным «Фонтанки» '
    '(15 января 2026 года), «Юнирест» «завершила ребрендинг точек KFC. '
    'Заведений под старым брендом в России больше не осталось» — все точки '
    'работают под брендом Rostic\'s.'
)
NEW_TERMS = OLD_TERMS + TERMS_ADDITION

NEW_SRC = [
    ['Фонтанка', 'https://www.fontanka.ru/2026/01/15/76215964/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['terms'] == OLD_TERMS
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.terms: станет ===')
    print(NEW_TERMS)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['terms'] = NEW_TERMS
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
