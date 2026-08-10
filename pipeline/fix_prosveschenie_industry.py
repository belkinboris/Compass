# -*- coding: utf-8 -*-
"""Карточка gf9932079 («ВЭБ.РФ консолидировал 75% издателя учебников
«Просвещение»») несла отрасль «Пищепром и напитки» вместо «Образование».

ЧТО СЛОМАНО. `ind` стояло «Пищепром и напитки» — предмет сделки при этом сам
профиль компании (g690e043b, «Издательский холдинг «Просвещение»») несёт
`ind: «Образование»`, и источник (kommersant.ru/doc/8009248) прямо называет
«Просвещение» «крупнейшим в России издателем школьных учебников». Издатель
учебников — не пищепром ни по одному признаку; похоже, при автоматическом
разборе досталась случайная отрасль.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `industry_is_supported()` для поля `ind` ищет
либо слово словаря `industry_by_words` в цитате (в словаре «Образование» нет
стема на «учебник»/«издатель», расширять словарь ради одной карточки не
нужно), либо имя профиля компании в цитате БЕЗ родового слова холдинга
(«Издательский холдинг «Просвещение»» в цитате не встречается целиком, только
«Просвещение») — оба пути молча отклоняют дословно верную правку. Источник
классификации здесь не текст цитаты, а сам профиль предмета сделки, уже
проверенный (`ind: «Образование»`) — отдельный одноразовый скрипт с `assert`
на исходное значение, а не запись в общей таблице.

Запуск:
    python3 pipeline/fix_prosveschenie_industry.py            # сухой прогон
    python3 pipeline/fix_prosveschenie_industry.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'gf9932079'
TARGET_ID = 'g690e043b'
OLD_IND = 'Пищепром и напитки'
NEW_IND = 'Образование'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('ind') == OLD_IND, \
        'отрасль уже другая: %r, ожидали %r' % (deal.get('ind'), OLD_IND)
    target = data['companies'].get(TARGET_ID)
    assert target is not None, 'нет профиля предмета %s' % TARGET_ID
    assert target.get('ind') == NEW_IND, \
        'профиль предмета несёт другую отрасль: %r' % target.get('ind')

    print('%s: ind %r -> %r (по профилю предмета %s)'
          % (DEAL_ID, OLD_IND, NEW_IND, TARGET_ID))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['ind'] = NEW_IND
    assert deal['ind'] == NEW_IND, 'отрасль не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
