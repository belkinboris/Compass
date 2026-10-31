# -*- coding: utf-8 -*-
"""Приток 08:20 МСК 12 октября 2026: оператор сервисных офисов Aspace
заинтересовался покупкой сети гибких офисов Multispace (4 коворкинга в
Москве — Dinamo, Pravda, Tverskaya, Dubinin'Sky, ~18,2 тыс. кв. м).
Коммерсантъ со ссылкой на три источника; Aspace подтвердил интерес, но
заявил, что пока не владеет Multispace ни прямо, ни косвенно — сделка не
закрыта, только рассматривается. Ворота не распознали: оба названия
латиницей, признак российского рынка (ООО, рубли) есть в тексте статьи, но
не в заголовке.

Запуск: python3 pipeline/build_aspace_multispace_2026_10_12.py [--write]
"""
import json
import sys

sys.path.insert(0, 'pipeline/ingest')
import promote  # noqa: E402

PENDING = 'static/data/pending.json'
URL = 'https://www.kommersant.ru/doc/9024274'

DRAFT = {
    'draft_id': 'd-aspace-multispace-2026-10-12',
    'title': 'Aspace хочет купить сеть коворкингов Multispace в Москве',
    'date': '2026-10-12',
    'src': [['Коммерсантъ', URL]],
    'sum': None,
    'type': 'M&A',
    'status': 'Обсуждается',
    'events': [],
    'buyer_name': 'Aspace',
    'asset': 'сеть гибких офисов Multispace (4 коворкинга в Москве)',
    'seller': 'ООО «Флекс Капитал»',
    'parsed_parties': {'buyer': 'Aspace',
                        'asset': 'сеть гибких офисов Multispace (4 коворкинга в Москве)',
                        'seller': 'ООО «Флекс Капитал»'},
    'ind': 'Недвижимость',
    'needs_review': True,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    existing = {c['id'] for c in pending['cards']}
    deal_id = promote.new_id(existing)
    card = promote.to_card(DRAFT, deal_id)
    card['eco']['share'] = (
        'В лот могут войти сразу все четыре площадки сети — на Динамо, Правде, Тверской и '
        'Дубининской (бренды Multispace Dinamo/Pravda/Tverskaya/Dubinin’Sky); суммарная площадь — '
        'около 18,2 тыс. кв. м.'
    )
    card['eco']['val'] = (
        'Гендиректор «Infoline-Аналитики» Михаил Бурмистров оценивает операционный бизнес этих '
        'площадок в 800–950 млн ₽; при заполнении арендаторами на 90% выручка собственника могла '
        'бы достигать 1,4 млрд ₽ в год.'
    )
    card['eco']['context'] = (
        'В августе 2026 года девелопер Pridex, создавший сеть, продал ее «группе '
        'профессиональных частных инвесторов». По данным СПАРК, все четыре юрлица сети '
        '(«Мультиспейс Скайлайн», «Мультиспейс Правда», «Мультиспейс Тверская», «Мультиспейс '
        'Динамо» — все ООО) целиком принадлежат одной фирме, ООО «Флекс Капитал»: 90,1% в ней у '
        'ее бенефициара и гендиректора Ксении Болотовой, 9,9% — у Владислава Бондаренко. '
        'Aspace сообщил изданию: доли в Multispace у компании сейчас нет никакой — ни прямой, '
        'ни через третьих лиц, но компания ищет способы вырасти, не исключая и покупку активов '
        'Multispace; в самой Multispace запрос издания оставили без ответа.'
    )
    card['themes'] = ['M&A']
    card['pending_since'] = '2026-10-12T08:20:00+00:00'
    if not write:
        print('Сухой прогон. Карточка была бы: %s' % deal_id)
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return
    pending['cards'].append(card)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('Записано: %s добавлена в pending.json' % deal_id)


if __name__ == '__main__':
    main('--write' in sys.argv)
