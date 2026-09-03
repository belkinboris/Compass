# -*- coding: utf-8 -*-
"""Продолжение `fix_vk_ufirst_extra_and_structure.py` (та же карточка,
`g9be8d398», тот же прогон) — обнаружено сразу при Playwright-проверке
своей же правки: дата одобрения ФАС (28 декабря 2023 года), которую я
записал в `extra`, не попадает на экран вовсе. `extraHtml()` в
static/index.html сравнивает каждое предложение `extra` со всеми полями
`eco`/`law` (кроме `adv`) и вырезает то, что уже сказано похожими словами
(родня урока CLAUDE.md «Тот же дедуп ломается и на КОРОТКОМ ЭТАЛОНЕ») —
моё предложение про одобрение ФАС делит с уже существовавшим `law.appr`
слова «ФАС», «одобрила», «VK», и всё предложение целиком вырезается как
повтор; второе предложение про «техническую сторону» дословно повторяет
`eco.rationale` и тоже вырезается. В итоге дата нигде не видна.

Правильное место для факта о дате согласования — само поле `law.appr`
(«Согласования»), а не `extra`: там уже жила общая фраза «ФАС одобрила
сделку...» без даты и без имени заявителя. Дописываю оба факта прямо
туда, откуда их не выкинет дедуп «Дополнительного контекста» (правило
«Одно поле — одна линза»/«Что искать для линзы Юрист» уже требует это).

Запуск: python3 pipeline/fix_vk_ufirst_appr_date.py
        python3 pipeline/fix_vk_ufirst_appr_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9be8d398'

OLD_LAW_APPR = 'ФАС одобрила сделку по покупке бывшей English First компанией VK.'
NEW_LAW_APPR = (
    'ФАС одобрила сделку по покупке бывшей English First компанией VK: '
    'ходатайство ООО «Учи.Ру Плюс» (дочерней структуры VK) зарегистрировано '
    '20 ноября 2023 года, одобрено 28 декабря 2023 года.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_LAW_APPR

    print('=== law.appr: станет ===')
    print(NEW_LAW_APPR)

    if write:
        deal['law']['appr'] = NEW_LAW_APPR
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
