# -*- coding: utf-8 -*-
"""Карточка `c1d0f3d54` («Enel и Fortum замораживают продажу российских
активов») пришла с пустым `eco` ({}), хотя в `extra` уже была подсказка на
указ Президента №520. Единственный источник карточки (neftegaz.ru) в этой
сессии недоступен (SSL: сертификат не подтверждён), и в кэше притока текста
нет вовсе — дословную цитату для `review.py` взять неоткуда.

Факты ниже подтверждены живым поиском (WebSearch/WebFetch, а не кэшем
притока) по независимым источникам о том же указе (РИА Новости, Meduza,
«Коммерсантъ» через oilcapital.ru) — тот же уровень доверия, что уже
принят в базе для строк law.adv с пометкой «Источник: обогащение/веб-поиск»:
не дословная цитата source-текста, а перепроверенный факт из нескольких
независимых публикаций. Именно поэтому это отдельный скрипт, а не запись в
таблице review.py, которая требует дословного кэша.

Факт о блокирующем указе идёт в `law.appr`, а не в `eco.share` вместе с
описанием сторон — иначе `test_approval_is_not_left_in_prose` находит
упоминание указа в прозе при пустом `law.appr` и требует либо перенести
факт в «Согласования», либо убрать его из прозы вовсе.

Запуск: python3 pipeline/fill_enel_fortum_freeze.py
        python3 pipeline/fill_enel_fortum_freeze.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c1d0f3d54'
ECO_SHARE = (
    'Enel намеревалась продать 56,43% в «Энел Россия» «Лукойлу» и '
    'инвестиционному фонду «Газпромбанк — Фрезия» примерно за $137 млн; '
    'Fortum завершила приём заявок от потенциальных покупателей на свою '
    'генерирующую компанию «Фортум» (98,25%). (Источник: '
    'обогащение/веб-поиск.)'
)
LAW_APPR = (
    'Обе сделки оказались заморожены указом президента РФ №520 от '
    '5 августа 2022 года, запретившим до конца года без специального '
    'разрешения сделки с долями иностранцев из недружественных стран в '
    'стратегических предприятиях энергетики. (Источник: '
    'обогащение/веб-поиск.)'
)


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['eco'].get('share') == ECO_SHARE and card.get('law', {}).get('appr') == LAW_APPR:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['eco'] == {}, '%s: eco уже не пуст' % CARD_ID
    assert 'law' not in card, '%s: law уже задан' % CARD_ID
    print('ПРАВИМ  %s: заполняю eco.share (стороны/суммы) и law.appr '
          '(блокирующий указ) по перепроверенным независимым источникам' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['eco']['share'] = ECO_SHARE
    card['law'] = {'appr': LAW_APPR}
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
