#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«Арнест Юнирусь» (gb700e4d9) — не универсальный «покупатель от группы
«Арнест»», а КОНКРЕТНОЕ юрлицо: бывшее ООО «ЮНИЛЕВЕР РУСЬ», переименованное
ПОСЛЕ сделки ge370e8f1 (карточка сама несёт в holding.source ссылку на
TAdviser: «Компания:Арнест_Юнирусь_(ранее_Юнилевер_Русь)»). Кампания
самопроверки ИНН (Этап 14, П3) нашла: этот же профиль стоит покупателем ещё
в ТРЁХ карточках группы «Арнест» (Avon, Ball, Heineken) — но подтверждён
живым egr() ровно для ОДНОГО реального юрлица с одним ИНН, которое физически
не могло называться «Арнест Юнирусь» ДО переименования (октябрь 2024).

Разобрано по каждой карточке отдельно (WebSearch+WebFetch, 29 августа 2026):

  * ge370e8f1 (Unilever, октябрь 2024) — buyer=gb700e4d9 логически замкнут
    сам на себя: это ТА ЖЕ сущность, что и target (ga8cb8878, «Юнилевер
    Русь»), просто под будущим именем. Источники карточки называют
    покупателя только «группой «Арнест»» — buyer переставлен на профиль
    группы (arnest, уже существует, group=true).
  * gc3ab0c7d (Avon, февраль 2026) — НЕ ТРОГАТЬ: buyer=gb700e4d9 дословно
    подтверждён собственными полями карточки (eco.share, eco.context,
    extra цитируют «"Арнест Юнирусь" приобрела...»); к февралю 2026
    переименование уже состоялось, «Арнест Юнирусь» — рабочее название
    подразделения личной гигиены группы, используемое для последующих
    сделок этого профиля.
  * g2dc1ba74 (Ball, сентябрь-октябрь 2022) — buyer=gb700e4d9 анахронизм:
    в 2022 году эта сущность называлась «Юнилевер Русь» и принадлежала
    Unilever, а не «Арнесту». WebFetch (kavkaz.rbc.ru) дал дословную цитату
    с настоящим юрлицом-покупателем: «По данным АО «Арнест», в сентябре по
    итогам тендера право на совершение сделки получило ООО «Арнест
    Менеджмент», входящее в состав группы.» — заведён новый профиль,
    eco.share (была заглушка «—») заполнено этой цитатой.
  * g64eb0e04 (Heineken) — тот же анахронизм (buyer=gb700e4d9), плюс
    отдельная, independentно найденная ошибка: `date` стоял «2022», хотя
    сделка закрыта 25 августа 2023 года (сходятся РИА Новости, Интерфакс,
    Lenta.ru, Meduza, РБК/Уфа, RTVI, Currenttime — семь независимых
    источников, ни один не называет 2022 годом закрытия; РИА: подзаголовок
    «Heineken завершил продажу российских активов группе компаний Arnest»,
    дата публикации 25.08.2023). buyer переставлен на профиль группы
    (arnest), date поднят на подтверждённый год и день.

Запуск:
    python3 pipeline/fix_arnest_buyer_role_confusion.py            # сухой прогон
    python3 pipeline/fix_arnest_buyer_role_confusion.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

NEW_PROFILE_ID = 'arnest-management'
NEW_PROFILE = {
    'name': 'ООО «Арнест Менеджмент»',
    'ind': 'Пищепром и напитки',
    'desc': (
        'Юридическое лицо группы «Арнест», выигравшее тендер на покупку '
        'российских заводов Ball по производству алюминиевых банок в 2022 году.'
    ),
    'kpi': ['Профиль', 'Автоматический'],
    'holding': {
        'id': 'arnest',
        'confidence': 'disclosed',
        'source': ['РБК', 'https://kavkaz.rbc.ru/kavkaz/freenews/632c1ce19a7947fb06f8222f'],
    },
}

BALL_ECO_SHARE_OLD = '—'
BALL_ECO_SHARE_NEW = (
    'По данным АО «Арнест», в сентябре по итогам тендера право на совершение '
    'сделки получило ООО «Арнест Менеджмент», входящее в состав группы.'
)
BALL_SRC_ADD = ['РБК (Кавказ)', 'https://kavkaz.rbc.ru/kavkaz/freenews/632c1ce19a7947fb06f8222f']

HEINEKEN_DATE_OLD = '2022'
HEINEKEN_DATE_NEW = '2023-08-25'
HEINEKEN_SRC_ADD = ['РИА Новости', 'https://ria.ru/20230825/prodazha-1892149466.html']


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    companies = data['companies']

    assert NEW_PROFILE_ID not in companies, 'профиль уже существует'

    unilever = deals['ge370e8f1']
    assert unilever['buyer'] == 'gb700e4d9', 'Unilever: buyer уже не gb700e4d9'
    assert unilever['target'] == 'ga8cb8878'

    ball = deals['g2dc1ba74']
    assert ball['buyer'] == 'gb700e4d9', 'Ball: buyer уже не gb700e4d9'
    assert ball['eco']['share'] == BALL_ECO_SHARE_OLD, 'Ball: eco.share уже не заглушка'
    assert BALL_SRC_ADD not in ball['src']

    heineken = deals['g64eb0e04']
    assert heineken['buyer'] == 'gb700e4d9', 'Heineken: buyer уже не gb700e4d9'
    assert heineken['date'] == HEINEKEN_DATE_OLD, 'Heineken: date уже не 2022'
    assert HEINEKEN_SRC_ADD not in heineken['src']

    # gc3ab0c7d (Avon) НЕ ТРОГАЕМ — buyer=gb700e4d9 там верен и подтверждён
    # собственными полями карточки.
    avon = deals['gc3ab0c7d']
    assert avon['buyer'] == 'gb700e4d9'

    print('Проверки прошли. План:')
    print('  ge370e8f1 (Unilever): buyer gb700e4d9 -> arnest')
    print('  g2dc1ba74 (Ball): buyer gb700e4d9 -> %s (новый профиль), '
          'eco.share заполнено, src +1' % NEW_PROFILE_ID)
    print('  g64eb0e04 (Heineken): buyer gb700e4d9 -> arnest, '
          'date %s -> %s, src +1' % (HEINEKEN_DATE_OLD, HEINEKEN_DATE_NEW))
    print('  gc3ab0c7d (Avon): без изменений')

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = NEW_PROFILE

    unilever['buyer'] = 'arnest'

    ball['buyer'] = NEW_PROFILE_ID
    ball['eco']['share'] = BALL_ECO_SHARE_NEW
    ball['src'].append(BALL_SRC_ADD)

    heineken['buyer'] = 'arnest'
    heineken['date'] = HEINEKEN_DATE_NEW
    heineken['src'].append(HEINEKEN_SRC_ADD)

    assert companies[NEW_PROFILE_ID]['name'] == 'ООО «Арнест Менеджмент»'
    assert deals['ge370e8f1']['buyer'] == 'arnest'
    assert deals['g2dc1ba74']['buyer'] == NEW_PROFILE_ID
    assert deals['g2dc1ba74']['eco']['share'] == BALL_ECO_SHARE_NEW
    assert deals['g64eb0e04']['buyer'] == 'arnest'
    assert deals['g64eb0e04']['date'] == HEINEKEN_DATE_NEW
    assert deals['gc3ab0c7d']['buyer'] == 'gb700e4d9'

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
