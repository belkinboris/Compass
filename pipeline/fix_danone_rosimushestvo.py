# -*- coding: utf-8 -*-
"""У карточки `c7fd83d05» («Переход акций Danone Россия под управление
Росимущества») `eco.context`/`extra` заканчивались протёкшей служебной
пометкой сторон «(Государство (Росимущество), осуществляло временное
управление активами)» — тот же класс дефекта, что и другие протёкшие теги
этой партии. Заодно у карточки отсутствовал `status`: передача во
временное управление по указу президента — уже свершившийся факт (та же
логика, что у карточек CanPack/Rockwool, тоже переданных во временное
управление и получивших status «Закрыта»), поэтому верный статус —
«Закрыта», а не отсутствие статуса вовсе.

Почему не через review.py: текст поля — пересказ, написанный при более
раннем проходе, а не дословная цитата источника (reader.rbc.ru не отдаёт
текст в этой сессии, дословного кэша для проверки нет).

Запуск: python3 pipeline/fix_danone_rosimushestvo.py
        python3 pipeline/fix_danone_rosimushestvo.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c7fd83d05'
NEW_STATUS = 'Закрыта'
TAG = (' (Государство (Росимущество), осуществляло временное управление '
       'активами)')
OLD_CONTEXT = (
    'Новым генеральным директором переименованной компании Life & '
    'Nutrition назначен Якуб Закриев (племянник главы Чечни Рамзана '
    'Кадырова), в совет директоров вошли приближенные Кадырова.' + TAG
)
NEW_CONTEXT = OLD_CONTEXT[:-len(TAG)]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card.get('status') == NEW_STATUS and card['eco']['context'] == NEW_CONTEXT:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert 'status' not in card, '%s: status уже задан' % CARD_ID
    assert card['eco']['context'] == OLD_CONTEXT, '%s: eco.context уже другой' % CARD_ID
    print('ПРАВИМ  %s: status -> «%s», снята протёкшая пометка сторон' % (CARD_ID, NEW_STATUS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['status'] = NEW_STATUS
    card['eco']['context'] = NEW_CONTEXT
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
