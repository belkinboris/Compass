# -*- coding: utf-8 -*-
"""Приёмка карточки g29d31edd (НМГ/«Лайм», 2026-09-11, приток 15:20 МСК) —
карточка была прочитана и провычитана ещё 8 сентября, но не прошла новый
гейт `accept_card.py`: покупатель и предмет стояли только текстом (профилей
не было — ни НМГ, ни «Лайм» ни разу не встречались в базе раньше), а отрасль
несла заглушку «Не определена», которую пост не имеет права показывать.

Источники (WebFetch на iz.ru, mergers.ru) не называют ЮРЛИЦО ни одной из
сторон — ни ИНН, ни ОГРН, ни точное наименование ООО/АО. Профили заводятся
как бренды (тот же класс, что и у большинства крупных холдингов в базе —
«Яндекс», «Сбербанк»), без записи в реестре ИНН: этого источники не дают.

Отрасль — «Развлечения», а не отрасль покупателя (медиа) и не «ИТ»: предмет
сделки — платформа, автоматизирующая парки аттракционов, аквапарки и
термальные комплексы (текст уже стоит в eco.context), то есть технология
ДЛЯ индустрии развлечений, а не сама по себе ИТ-продукция на продажу.
Тот же принцип, что уже применён к Аэромару («отрасль сделки — не отрасль
покупателя, а по предмету»).

Запуск: python3 pipeline/fix_nmg_laim_profiles_and_industry.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g29d31edd'
BUYER_ID = 'gnmg'
TARGET_ID = 'glaim'


def main(write=False):
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    assert BUYER_ID not in base['companies'], 'профиль %s уже есть' % BUYER_ID
    assert TARGET_ID not in base['companies'], 'профиль %s уже есть' % TARGET_ID

    card = next((c for c in base['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена' % CARD_ID
    assert card.get('buyer') is None and card.get('target') is None, \
        'стороны уже привязаны к профилям'
    assert card['ind'] == 'Не определена', 'отрасль уже другая'

    card['buyer'] = BUYER_ID
    card['target'] = TARGET_ID
    card['ind'] = 'Развлечения'

    base['companies'][BUYER_ID] = {
        'name': 'Национальная Медиа Группа',
        'ind': 'Медиа',
        'desc': ('Российский медиахолдинг: телеканалы, издательские и '
                 'цифровые активы; с 2026 года развивает направление '
                 'офлайн-развлечений.'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    base['companies'][TARGET_ID] = {
        'name': '«Лайм»',
        'ind': 'Развлечения',
        'desc': ('Технологическая платформа для парков аттракционов, '
                 'аквапарков, термальных комплексов и других объектов '
                 'досуга: кассовые и онлайн-продажи, бронирование, '
                 'контроль доступа, абонементы и отчётность.'),
        'kpi': ['Профиль', 'Автоматический'],
    }
    base.setdefault('match_keys', {})[BUYER_ID] = ['национальная медиа группа', 'нмг']
    base.setdefault('match_keys', {})[TARGET_ID] = ['лайм']

    print('Правка %s: buyer=%s, target=%s, ind=Развлечения.' %
          (CARD_ID, BUYER_ID, TARGET_ID))

    if write:
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
