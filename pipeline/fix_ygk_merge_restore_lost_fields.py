# -*- coding: utf-8 -*-
"""Слияние gdcc03f9d -> cc16fce80 (16 августа 2026, `fix_deep_batch1_manual.py`)
перенесло только ССЫЛКИ src, а не содержимое полей — владелец справедливо
указал на общий принцип: «найденный в другом источнике факт про уже
существующую карточку — повод обогатить оригинал, не просто сослаться».

Сравнение по git-истории (gdcc03f9d до удаления, коммит 42821d1^) против
текущей cc16fce80 показало реальную потерю — четыре поля были у дубля и
отсутствуют у выжившей карточки целиком:

  * eco.target_fin — имплицитная оценка пакета и прочих активов лота
    аналитиками Freedom Global (у cc16fce80 такого поля не было вовсе).
  * law.appr — единственный факт о согласовании во всей карточке (спор
    вокруг предписания ЦБ Росимуществу о выкупе акций у миноритариев) —
    особенно обидная потеря: линза «Юрист» и так пуста у 75% карточек
    базы, а тут заполненное поле буквально выбросили.
  * law.terms — условие задатка на аукционе.
  * events — три датированных этапа сделки (аукцион объявлен / оплачен
    пакет / оформлено владение) с собственными источниками mergers.ru;
    структурированного поля такого типа у cc16fce80 не было вовсе.

eco.rationale и eco.share НЕ переносятся: у cc16fce80 уже стоят СВОИ,
не менее содержательные версии (цитата Силуанова, актуальный состав
пакета), дублировать значило бы просто разросить карточку тем же самым
другими словами — родня урока CLAUDE.md «Одно поле — одна линза».

Запуск:
    python3 pipeline/fix_ygk_merge_restore_lost_fields.py            # сухой прогон
    python3 pipeline/fix_ygk_merge_restore_lost_fields.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'cc16fce80'

TARGET_FIN = ('По оценке аналитиков Freedom Global, пакет 67,25% акций '
              'ЮГК в составе лота имплицитно оценён примерно в 80,8 млрд '
              'руб. (~0,54 руб. на акцию); прочие активы лота оценены '
              'отдельно: 100% УК ЮГК — 9,1 млрд руб., 100% «Хоум» — 10,4 '
              'млрд руб., 80% «Арбат-Сити» — 1 руб.')
LAW_APPR = ('Банк России направлял предписание Росимуществу о выкупе '
            'акций у миноритариев, однако ведомство отказалось, '
            'сославшись на ограничения Бюджетного кодекса.')
LAW_TERMS = ('Участие в аукционе требовало внесения задатка (заявка без '
             'задатка была отклонена на третьем этапе торгов).')
EVENTS = [
    {
        'kind': 'negotiations',
        'date': '2026-06-11',
        'title': 'Объявлен голландский аукцион',
        'note': ('Росимущество объявило голландский аукцион по продаже '
                  'ЮГК со стартовой ценой 81,01 млрд ₽, итоги — 19 июня.'),
        'source': ['mergers.ru',
                   'https://mergers.ru/news/Rosimuschestvo-provedet-'
                   'gollandskij-aukcion-po-prodazhe-YuGK-i-obyavit-'
                   'itogi-19-iyunya-87063'],
    },
    {
        'kind': 'closed',
        'date': '2026-07-06',
        'title': 'Оплачен контрольный пакет',
        'note': ('АО «БТС-Мост Холдинг» оплатило Росимуществу стоимость '
                  '67,2% акций ЮГК (93,16 млрд ₽ по данным mergers.ru) и '
                  'долей связанных структур.'),
        'source': ['mergers.ru',
                   'https://mergers.ru/news/BTS-Most-Holding-oplatil-'
                   'kontrolnyj-paket-akcij-YuGK-87151'],
    },
    {
        'kind': 'closed',
        'date': '2026-07-17',
        'title': 'Оформлено владение 67,2489% акций',
        'note': ('АО «БТС-Мост Холдинг» стало собственником 67,2489% '
                  'акций ПАО «Южуралзолото Группа Компаний».'),
        'source': ['mergers.ru',
                   'https://mergers.ru/news/BTS-Most-Holding-stal-'
                   'vladelcem-672-YuGK-87227'],
    },
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    card = {d['id']: d for d in data['deals']}[CARD_ID]

    assert 'target_fin' not in card['eco'], 'eco.target_fin уже стоит'
    assert 'appr' not in card['law'], 'law.appr уже стоит'
    assert 'terms' not in card['law'], 'law.terms уже стоит'
    assert 'events' not in card, 'events уже стоят'

    print('%s: восстанавливаем eco.target_fin, law.appr, law.terms, events '
          '(потеряны при слиянии gdcc03f9d)' % CARD_ID)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    card['eco']['target_fin'] = TARGET_FIN
    card['law']['appr'] = LAW_APPR
    card['law']['terms'] = LAW_TERMS
    card['events'] = EVENTS

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
