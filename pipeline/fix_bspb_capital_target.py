# -*- coding: utf-8 -*-
"""Разовая правка: у сделки «Александровский»/«БСПБ Капитал» предметом стоял продавец.

КАК НАШЛОСЬ. Не глазами и не отдельной проверкой, а ПОБОЧНЫМ ЭФФЕКТОМ другой
правки. `fix_party_name_case.py` заменил у этой карточки продавца «Банка
«Санкт-Петербург»» на «Банк «Санкт-Петербург»» — и сразу упал давно стоящий
тест `test_asset_is_not_a_party`: имя продавца текстом совпало с названием
профиля, на который ссылается `target`. До правки падежа совпадения не было
(«Банка» против «Банк»), и дефект восемь месяцев лежал невидимым.

ЧТО СЛОМАНО. Заголовок: «Банк „Александровский" купил „БСПБ Капитал" у Банка
„Санкт-Петербург"». Предмет сделки — управляющая компания «БСПБ Капитал», а в
`target` стоял профиль ПРОДАВЦА. На экране это значит, что карточка вела на
страницу «Банка „Санкт-Петербург"» как на купленный актив, а сам «БСПБ
Капитал» не существовал в базе вовсе.

ЧТО ДЕЛАЕМ. Заводим профиль «БСПБ Капитал» (описание — по тексту самой
карточки, ничего не досочиняя), ставим его в `target`, а продавца связываем
с его профилем через `seller_id`. Текстовое поле `seller` остаётся: у
карточки может быть и ссылка, и имя.

Запуск:
    python3 pipeline/fix_bspb_capital_target.py            # сухой прогон
    python3 pipeline/fix_bspb_capital_target.py --write    # применить
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL = 'ga06c75e2'
SELLER_PROFILE = 'gf881a88f'          # Банк «Санкт-Петербург»
NEW_PROFILE = 'gbspbcapital'
NEW_NAME = '«БСПБ Капитал»'
# Описание собрано ТОЛЬКО из текста самой карточки — ничего сверх него.
NEW_DESC = ('Управляющая компания: доверительное управление активами и '
            'инвестиционное консультирование. До 2025 года входила в группу '
            'банка «Санкт-Петербург».')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    card = deals.get(DEAL)
    assert card, 'карточки %s нет в базе' % DEAL
    assert card.get('target') == SELLER_PROFILE, \
        'предмет уже не продавец: %r' % card.get('target')
    assert card.get('seller') == 'Банк «Санкт-Петербург»', \
        'продавец уже другой: %r' % card.get('seller')
    assert card.get('seller_id') is None, \
        'у продавца уже есть ссылка: %r' % card.get('seller_id')
    assert NEW_PROFILE not in companies, 'профиль %s уже существует' % NEW_PROFILE
    assert 'БСПБ Капитал' in card['title'], 'предмет не назван в заголовке'

    print('  сделка   %s' % card['title'])
    print('  предмет  %s (%s)  ->  %s (%s)'
          % (companies[SELLER_PROFILE]['name'], SELLER_PROFILE, NEW_NAME, NEW_PROFILE))
    print('  продавец текстом «%s»  ->  плюс ссылка на профиль %s'
          % (card['seller'], SELLER_PROFILE))
    print('  новый профиль: %s — %s' % (NEW_NAME, NEW_DESC))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    companies[NEW_PROFILE] = {'name': NEW_NAME, 'desc': NEW_DESC, 'ind': 'Банки'}
    card['target'] = NEW_PROFILE
    card['seller_id'] = SELLER_PROFILE
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО: предмет сделки исправлен, профиль %s заведён.' % NEW_PROFILE)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
