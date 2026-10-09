# -*- coding: utf-8 -*-
"""Карточка g5b4e85aa (агробизнес Боброва/Бикова, национализация, повторные
торги) — комиссия определила победителя повторных торгов: ООО «Бизнес-
Эксперт» (Верхняя Пышма), 285,6 млн ₽ (ровно половина стартовой цены),
решение единогласное, опубликовано на ГИС «Торги» (URA.RU). Переводим
карточку в «Закрыта», как «Исток» (docs/card_status_dates.md, «Обратный
ход бывает») и по прямому прецеденту g51fa80ce (тот же вид сделки, та же
неделя).
"""
import json

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g5b4e85aa'

OLD_TITLE = 'Аукцион по продаже изъятого у Алексея Боброва агробизнеса не состоялся'
NEW_TITLE = '«Бизнес-Эксперт» выиграла повторные торги по агробизнесу, изъятому у Боброва и Бикова'

OLD_SUM = '571,2 млн ₽'
NEW_SUM = '285,6 млн ₽'

OLD_CONTEXT = (
    'ПСБ пытался продать 100% акций в четырёх структурах с начальной ценой '
    '571,2 млн ₽. Заявки принимали с 21 по 25 сентября, итоги должны были '
    'подвести 29 сентября, но покупателя не нашлось.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Повторные торги прошли через публичное предложение со снижением цены '
    'вплоть до половины стартовой; на второй раунд поступили две заявки '
    '2 октября, к участию допустили обе 7 октября. Комиссия единогласно '
    'признала победителем ООО «Бизнес-Эксперт» (Верхняя Пышма) с '
    'предложением 285,6 млн ₽ — ровно минимально допустимая цена по условиям '
    'лота.'
)

NEW_EVENT = {
    'kind': 'closed',
    'date': '2026-10-09',
    'title': 'Торги завершены, определён победитель',
    'note': (
        'Покупателем четырёх национализированных уральских агропредприятий, '
        'ранее связанных с Алексеем Бобровым и Артёмом Биковым, стала '
        'компания «Бизнес-Эксперт» из Верхней Пышмы — её предложение в '
        '285,6 млн ₽ (вдвое ниже стартовой цены) комиссия признала '
        'победившим единогласно, решение опубликовано на портале ГИС «Торги».'
    ),
    'source': ['URA.RU', 'https://ura.news/news/1053134719'],
}

NEW_SRC = ['URA.RU', 'https://ura.news/news/1053134719']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card['title'] == OLD_TITLE, card['title']
    assert card['status'] == 'Не состоялась', card['status']
    assert card['sum'] == OLD_SUM, card['sum']
    assert card['eco']['sum'] == OLD_SUM, card['eco']['sum']
    assert card['eco']['context'] == OLD_CONTEXT, card['eco']['context']

    card['title'] = NEW_TITLE
    card['status'] = 'Закрыта'
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    card['eco']['context'] = NEW_CONTEXT
    card['buyer_name'] = 'ООО «Бизнес-Эксперт»'
    card['buyer_src'] = 'text'
    card.setdefault('party_evidence', {})['buyer'] = [{
        'value': 'ООО «Бизнес-Эксперт»',
        'field': 'buyer_name',
        'method': 'human_review',
        'url': 'https://ura.news/news/1053134719',
    }]
    if not any(s[1] == NEW_SRC[1] for s in card['src']):
        card['src'].append(NEW_SRC)
    card['events'].append(NEW_EVENT)
    card.setdefault('accepted_notes', {}).setdefault('no_profile', {})['buyer'] = (
        'ООО «Бизнес-Эксперт» (Верхняя Пышма) — победитель повторных торгов; '
        'профиль консалтинговой фирмы, купившей лот ради актива, не заводим '
        'в рамках прогона притока (решение о профиле — за рутиной «качество», '
        'данные о собственниках из решения комиссии не проверены независимым '
        'реестром в этом прогоне).'
    )
    print('Карточка переведена в «Закрыта», sum/title/buyer/context/events обновлены.')
    if not write:
        print('(сухой прогон, для записи — --write)')
        return
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
