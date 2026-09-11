# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (14:20 МСК) — реальная сделка, которую ворота
спрятали ложным признаком дубля: черновик «"Дом.РФ" продал старинные
палаты в центре Москвы» (realty.ria.ru) получил причину «похоже на уже
описанную сделку g3ecb7b86» — тот же класс, что уже описан в CLAUDE.md
(«Название в кавычках — часто не предмет сделки, а продавец»): «Дом.РФ»
продаёт десятки разных активов, а `g3ecb7b86» — это ПОКУПКА лифтового
бизнеса тем же «Дом.РФ», совершенно другой актив и другая роль (там
Дом.РФ покупатель, здесь — продавец на торгах).

Источник прочитан целиком (WebFetch): «Дом.РФ» продал на торгах палаты
Кожевенной слободы XVII века (объект культурного наследия федерального
значения, 525,7 кв. м, Москва, Кожевническая ул., 19, стр. 6, с арендой
участка 0,18 га) компании «Бриз», которую источник связывает с
девелопером «Крост» (формулировка источника — «связываемой», не
подтверждённое владение, поэтому профиль на «Крост» не заводится).
Итоговая цена — около 100,5 млн ₽ при начальной цене торгов 67,4 млн ₽.

Запуск: python3 pipeline/fix_add_dom_rf_palaty_briz.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

SRC_URL = 'https://realty.ria.ru/20260911/briz-2117122443.html'
DRAFT_ID = 'd40825725'

QUOTE_MAIN = ('«Дом.РФ» продал на торгах палаты Кожевенной слободы XVII '
              'века постройки в Замоскворечье — объект культурного '
              'наследия федерального значения площадью 525,7 кв. м. '
              'Новым владельцем стала компания «Бриз», связываемая с '
              'девелопером «Крост».')
QUOTE_SUM = ('Итоговая цена лота составила около 100,5 млн ₽ при '
             'стартовой цене торгов 67,4 млн ₽.')


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    existing_ids = {c['id'] for c in pending['cards']}
    assert not any('палаты' in (c.get('title') or '').lower()
                   for c in pending['cards']), \
        'карточка про палаты уже есть в pending.json'

    new_id = promote.new_id(existing_ids)
    card = {
        'id': new_id,
        'date': '2026-09-11',
        'title': '«Дом.РФ» продал на торгах палаты Кожевенной слободы XVII века',
        'ind': 'Недвижимость',
        'type': 'Продажа с торгов',
        'status': 'Закрыта',
        'src': [['РИА Недвижимость', SRC_URL]],
        'from_ingest': True,
        'eco': {'sum': '100,5 млн ₽', 'share': '—', 'val': '—',
                'target_fin': '—', 'fin': '—', 'rationale': '—',
                'context': ('Памятник архитектуры можно приспособить под '
                             'ресторан, офис или использовать с иными '
                             'коммерческими целями. В лот включена аренда '
                             'земельного участка 0,18 гектара.'),
                'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'seller': '«Дом.РФ»',
        'buyer_name': '«Бриз»',
        'asset': 'палаты Кожевенной слободы (Москва, Кожевническая, 19с6)',
        'sum': '100,5 млн ₽',
        'events': [{
            'kind': 'closed',
            'date': '2026-09-11',
            'title': 'Торги завершены',
            'note': QUOTE_MAIN + ' ' + QUOTE_SUM,
            'source': ['РИА Недвижимость', SRC_URL],
        }],
    }

    pending['cards'].append(card)
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'take'

    print('Добавлена карточка %s: «Дом.РФ»/«Бриз», палаты Кожевенной '
          'слободы.' % new_id)

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
