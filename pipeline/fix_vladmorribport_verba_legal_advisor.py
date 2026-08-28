# -*- coding: utf-8 -*-
"""Сергей Дарькин/«Владморрыбпорт» (`gmru-darkin-vladmorribport`): юридический
консультант сделки не был назван (`law.adv` пуст) — VERBA LEGAL сама объявила
о завершении сопровождения сделки (t.me/LawFirms/11307, 26 августа 2026),
назвав себя стороной покупателя, размер активов группы (>45 млрд руб.),
проведённую комплексную экспертизу (due diligence) и то, что согласование с
ФАС имело критическое значение. Дополнительно эта же фраза о ФАС переносится
в `law.appr`, где раньше стоял прочерк — согласование регулятора упоминается
прямо, хотя и без слова «одобрила».

Поле `law.adv` — список [роль, имя, примечание], не проходит общую проверку
review.py на дословность целиком списком (сравнивается str() всего списка),
поэтому правка идёт тем же путём, что и другие структурные списки — прямой
записью с `assert` на исходное состояние, а не через таблицу FIXES.

Запуск: python3 pipeline/fix_vladmorribport_verba_legal_advisor.py           # проверка
        python3 pipeline/fix_vladmorribport_verba_legal_advisor.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gmru-darkin-vladmorribport'
NEW_ADV_ROW = [
    'Юридический консультант покупателя',
    'VERBA LEGAL',
    'Команда завершила сопровождение сделки: due diligence портовой группы '
    '(более 10 компаний), согласование сделки с ФАС России, договоры '
    'купли-продажи акций и долей с несколькими продавцами. Проектную '
    'команду возглавил старший партнёр Александр Рудяков.',
]
NEW_APPR = (
    'Согласование сделки с ФАС России имело критическое значение, что '
    'потребовало от консультантов глубокого погружения в специфику бизнеса '
    'для оперативного реагирования на все запросы регулятора.'
)
NEW_SRC = ['Телеграм-канал: LawFirms', 'https://t.me/LawFirms/11307']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['law']['adv'] == [], 'law.adv уже не пуст: %r' % card['law']['adv']
    assert card['law']['appr'] == '—', 'law.appr уже другое: %r' % card['law']['appr']
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДОБАВЛЕНО В law.adv:', NEW_ADV_ROW)
    print('ЗАПИСАНО В law.appr:', NEW_APPR)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['law']['adv'] = [NEW_ADV_ROW]
    card['law']['appr'] = NEW_APPR
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
