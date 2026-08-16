# -*- coding: utf-8 -*-
"""Дочитывание REVISION_BRIEF, партия 6: структурные дефекты
gmru-vtb-otkrytie-office-rwb, не укладывающиеся в модель review.py.

ЧТО СЛОМАНО И ПОЧЕМУ. `title` нёс не только заголовок, но и приклеенное
описание объекта («...у ВТБ Об объекте сделки Офисный комплекс площадью
24,4 тыс. кв. м...») — похоже на артефакт разбора, склеивший заголовок с
подзаголовком статьи-источника. Тот же обрывок текста, ещё и оборванный на
середине предложения («...До интеграции банка «Открытие» в ВТБ»), лежал в
`events[0].note`. `sum` нёс единое число «13,5 млрд ₽» без пометки об
оценке, хотя стороны сумму не раскрыли — источник приводит ДВЕ разные
экспертные оценки (11–13,5 млрд у IBC Real Estate, ~7,7 млрд у Ricci), и
карточка выдавала верхнюю границу одной оценки за факт. `seller` был
неточен: стороной сделки по выписке ЕГРН выступил не ВТБ как материнская
структура, а «БМ-банк» (входит в ВТБ). `date`/`events[0].date` несли
10 августа, тогда как три независимых источника (Коммерсантъ, Retail.ru,
Mperspektiva) сходятся на 4 августа как дате регистрации смены владельца в
ЕГРН.

Найдено саб-агентом партии 6 (16 августа 2026). Не через review.py: правки
переписывают уже заполненные поля целиком (не переносят цитату в пустое
поле), а `title`/`events[0].note` требуют вырезания лишнего текста, а не
добавления нового — обе операции вне модели review.py.

Запуск:
    python3 pipeline/fix_vtb_otkrytie_office_rwb.py            # сухой прогон
    python3 pipeline/fix_vtb_otkrytie_office_rwb.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gmru-vtb-otkrytie-office-rwb'

OLD_TITLE = (
    'RWB купила бывший офис банка «Открытие» у ВТБ Об объекте сделки '
    'Офисный комплекс площадью 24,4 тыс. кв. м в составе БЦ класса А '
    'Vivaldi Plaza (Летниковская ул., 2, Москва), рядом с Павелецким '
    'вокзалом')
NEW_TITLE = 'RWB купила бывший офис банка «Открытие» у ВТБ'

OLD_SHARE = (
    'Бывший офис банка «Открытие» входит в состав бизнес-центра Vivaldi '
    'Plaza. Общая площадь здания составляет около 24,4 тыс. кв. м.')
NEW_SHARE = (
    'Бывший офис банка «Открытие» входит в состав бизнес-центра класса А '
    'Vivaldi Plaza (Летниковская ул., 2, Москва), рядом с Павелецким '
    'вокзалом. Общая площадь здания составляет около 24,4 тыс. кв. м.')

OLD_SUM = '13,5 млрд ₽'
NEW_SUM = '11–13,5 млрд ₽ (по оценке)'
OLD_ECO_SUM = '—'
OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'RWB мог заплатить за офисный центр на Летниковской улице 11–13,5 '
    'млрд руб. с учетом НДС, оценивает заместитель руководителя '
    'департамента по работе с офисными помещениями IBC Real Estate '
    'Артем Соломеннов. Партнер Ricci Дмитрий Антонов считает, что сумма '
    'сделки составила около 7,7 млрд руб.')

OLD_SELLER = 'ВТБ'
NEW_SELLER = 'БМ-банк (входит в ВТБ)'
# `seller_id` ссылался на профиль компании «ВТБ» — рендер плашки берёт
# ИМЕННО связанный профиль, если он есть, игнорируя текстовое `seller`
# (см. static/index.html, dealPlate: `d.seller_id && co(d.seller_id) ? ... :
# d.seller ? ...`). Без снятия ссылки правка seller выше была бы невидима на
# экране — карточка продолжала бы показывать «ВТБ». Профиля «БМ-банк» в базе
# нет, а плодить его ради одной сделки не нужно (это финансовая «дочка», а
# не отдельный игрок рынка) — снимаем ссылку, оставляем точный текст.
OLD_SELLER_ID = 'gcafc31dc'

OLD_DATE = '2026-06-30'
NEW_DATE = '2026-08-04'

OLD_EVENT_DATE = '2026-08-10'
NEW_EVENT_DATE = '2026-08-04'
OLD_EVENT_NOTE = (
    'RWB купила бывший офис банка «Открытие» у ВТБ Об объекте сделки '
    'Офисный комплекс площадью 24,4 тыс. кв. м в составе БЦ класса А '
    'Vivaldi Plaza (Летниковская ул., 2, Москва), рядом с Павелецким '
    'вокзалом. Построен в 2011 году. До интеграции банка «Открытие» в ВТБ')
NEW_EVENT_NOTE = (
    'RWB купила бывший офис банка «Открытие» у ВТБ. Офисный комплекс '
    'площадью 24,4 тыс. кв. м в составе БЦ класса А Vivaldi Plaza '
    '(Летниковская ул., 2, Москва), рядом с Павелецким вокзалом. Построен '
    'в 2011 году.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert card['title'] == OLD_TITLE, 'title уже другой: %r' % card['title']
    assert card['eco']['share'] == OLD_SHARE
    assert card['sum'] == OLD_SUM
    assert card['eco']['sum'] == OLD_ECO_SUM
    assert card['eco']['val'] == OLD_ECO_VAL
    assert card['seller'] == OLD_SELLER
    assert card.get('seller_id') == OLD_SELLER_ID
    assert card['date'] == OLD_DATE
    assert len(card['events']) == 1
    assert card['events'][0]['date'] == OLD_EVENT_DATE
    assert card['events'][0]['note'] == OLD_EVENT_NOTE

    print('%s  %s' % ('ПИШЕМ' if write else 'ПРАВИМ (сухой прогон)', CARD_ID))
    print('  title: убрано приклеенное описание объекта')
    print('  eco.share: класс А + адрес')
    print('  sum/eco.sum: %r -> %r' % (OLD_SUM, NEW_SUM))
    print('  eco.val: %r -> обе экспертные оценки' % OLD_ECO_VAL)
    print('  seller: %r -> %r' % (OLD_SELLER, NEW_SELLER))
    print('  seller_id: %r -> снята (профиля «БМ-банк» в базе нет)' % OLD_SELLER_ID)
    print('  date/events[0].date: %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  events[0].note: обрыв предложения снят')

    if write:
        card['title'] = NEW_TITLE
        card['eco']['share'] = NEW_SHARE
        card['sum'] = NEW_SUM
        card['eco']['sum'] = NEW_SUM
        card['eco']['val'] = NEW_ECO_VAL
        card['seller'] = NEW_SELLER
        card.pop('seller_id', None)
        card['date'] = NEW_DATE
        card['events'][0]['date'] = NEW_EVENT_DATE
        card['events'][0]['note'] = NEW_EVENT_NOTE
        if card.get('party_evidence', {}).get('seller'):
            for ev in card['party_evidence']['seller']:
                if ev.get('value') == OLD_SELLER:
                    ev['value'] = NEW_SELLER
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1,
                   ensure_ascii=False)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
