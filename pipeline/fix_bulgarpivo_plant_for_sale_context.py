# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g063c2d68 («Балтика» покупает
пивные заводы «Букет Чувашии» и «Булгарпиво», статус «Не состоялась»):
дельта-поиск нашёл, что причина срыва (стороны не сошлись в цене) уже
записана в `law.struct` дословно и совпадает с найденным в Коммерсанте —
новых фактов там нет. Но нашёлся отдельный, новый факт о судьбе одного из
двух несостоявшихся активов: спустя год после срыва сделки завод
«Булгарпиво» выставлен на продажу — «Продавец запросил за все 282 965 000
рублей» (chelny-izvest.ru, публикация 24 января 2026), на фоне финансовых
проблем — задолженность более 390 млн руб. и чистый убыток 234,8 млн руб.
за 2024 год. Статья не упоминает «Балтику» и не связывает продажу напрямую
со срывом прошлогодней сделки, но это следующий, известный шаг в судьбе
актива, который в карточке уже описан. Дословная цитата подтверждена лично
прямым WebFetch.

Запуск: python3 pipeline/fix_bulgarpivo_plant_for_sale_context.py
        python3 pipeline/fix_bulgarpivo_plant_for_sale_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g063c2d68'

OLD_CONTEXT = (
    '«Букет Чувашии» инвестбанкир Илья Шумов тогда оценил в 2 млрд руб., а '
    'гендиректор «Infoline-аналитики» Михаил Бурмистров оценил '
    '«Булгарпиво» в 700 млн руб.'
)
CONTEXT_ADDITION = (
    ' Спустя год после срыва сделки «Булгарпиво» выставлен на продажу: '
    '«Продавец запросил за все 282 965 000 рублей» за производственно-'
    'промышленный комплекс площадью 3329 м² (chelny-izvest.ru, январь '
    '2026) — на фоне финансовых проблем: задолженность более 390 млн '
    'руб. и чистый убыток 234,8 млн руб. за 2024 год. Статья не '
    'связывает продажу напрямую со срывом сделки с «Балтикой».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Челны Известия', 'https://chelny-izvest.ru/news/social/krax-pivnogo-giganta-zavod-bulgarpivo-v-celnax-vystavlen-na-prodazu'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
