# -*- coding: utf-8 -*-
"""SoftwareONE/Awara IT/WONE IT (`gfc7e5649`): месячный дообыск нашёл
судьбу объединённой компании — резкий обвал выручки в первый год после
слияния и текущее название юрлица. Источник — структурированная
карточка TAdviser (не пересказ поисковика, страница скачана и прочитана
целиком). `eco.context` уже занято другим предложением из другого
источника — дословно объединить для `review.py` нельзя, правка разовым
скриптом.

Запуск: python3 pipeline/fix_softwareone_wone_it_followup.py           # проверка
        python3 pipeline/fix_softwareone_wone_it_followup.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gfc7e5649'
OLD_CONTEXT = (
    'Швейцарская ИТ-компания SoftwareONE, уходя с российского рынка, '
    'продала российские активы отечественному интегратору Awara IT, '
    'породив совместную мультивендорную ИТ-компанию полного цикла под '
    'брендом WONE IT.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Объединённая компания сегодня работает как ООО «Ван Ай Ти '
    'Трейд» под брендом Wone IT; в 2022 году, первом после слияния, её '
    'выручка обвалилась на 70,9% — до 2,9 млрд рублей (для сравнения, '
    'выручка одной только российской «дочки» SoftwareONE в 2021 году '
    'составляла почти 9,97 млрд рублей). Доли собственников с момента '
    'сделки не изменились: 60% у Александра Ермакова, 40% у Юрия '
    'Шумакова.')
NEW_SRC = ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:'
           'Wone_IT_(Ван_Ай_Ти_Трейд,_ранее_SoftwareONE_Россия,_'
           'СофтвэрУАН_и_Awara_IT_Russia,_Авара_Ай_Ти_Солюшенс)']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    print('ПРАВИМ  %s: eco.context — судьба WONE IT после слияния' % CARD_ID)
    if write:
        card['eco']['context'] = NEW_CONTEXT
        if NEW_SRC not in src:
            src.append(NEW_SRC)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
