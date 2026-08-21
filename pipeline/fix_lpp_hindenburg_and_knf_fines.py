# -*- coding: utf-8 -*-
"""LPP/Reserved/Far East Services FZCO (`gfa14411d`): месячный дообыск
нашёл крупный, юридически НЕ УРЕГУЛИРОВАННЫЙ спор вокруг сделки —
Hindenburg Research (март 2024) утверждает, что уход LPP из России был
фикцией (Far East Services зарегистрирована за день до сделки, товары
из Польши продолжали идти в Россию — задокументировано таможенными
данными на $706,5 млн за 2022-2023, штрихкоды перекодировались). LPP
категорически отрицает обвинение и добилась расследования против самой
Hindenburg (подозрение в манипуляции акциями); следствие польской
прокуратуры по состоянию на середину 2026 года ПРИОСТАНОВЛЕНО в
ожидании международной правовой помощи США. Формулировка в карточке —
намеренно НЕЙТРАЛЬНАЯ и атрибутированная (кто что утверждает), без
вынесения вердикта, которого нет ни у одного суда.

ОТДЕЛЬНО, чище фактически: два штрафа польского регулятора KNF —
1) июль 2025, 1,8 млн злотых — за НЕСВОЕВРЕМЕННОЕ раскрытие условий
   сделки (сама компания подчёркивает, что это не связано с отчётом
   Hindenburg);
2) апрель 2026, 15 млн злотых — за ошибку в учёте момента списания
   стоимости активов в России и на Украине (другой вопрос, не про
   сокрытие сделки; решение обжалуется, не окончательное).
Оба — как записи `events[]`, не как приговор о характере сделки.

НЕ ТРОНУТО осознанно: расхождение суммы сделки (карточка несёт ≈$382
млн, notesfrompoland.com со ссылкой на решение KNF называет $135,5 млн
«в рассрочку до конца 2026», плюс отдельно «свыше 1 млрд злотых за
товар» и погашение займа €26,5 млн) — эти цифры относятся, похоже, к
РАЗНЫМ компонентам сделки (сама доля vs товарные остатки vs заём), а не
однозначно противоречат друг другу, но это не выяснено до конца в этом
прогоне. Записано отдельно как известная проблема в PRODUCT_ROADMAP.md
для следующего дочитывания — переписывать `sum` наугад не стали.

Запуск: python3 pipeline/fix_lpp_hindenburg_and_knf_fines.py           # проверка
        python3 pipeline/fix_lpp_hindenburg_and_knf_fines.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gfa14411d'
OLD_CONTEXT = (
    'Компания FES Retail по примеру других крупных fashion-операторов '
    'планирует оптимизировать бизнес, отказавшись от части своих '
    'магазинов. Под закрытие попадает около 50 точек.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' В марте 2024 года исследовательская компания Hindenburg Research '
    'опубликовала отчёт с утверждением, что уход LPP из России был '
    'фиктивным: Far East Services была зарегистрирована в Дубае за '
    'день до объявления о сделке, а по данным таможенной статистики, '
    'с сентября 2022 по декабрь 2023 года в Россию через связанные '
    'компании было экспортировано товаров LPP на сумму не менее $706,5 '
    'млн. LPP категорически отрицает обвинения, называя отчёт '
    'организованной атакой на котировки акций, и добилась расследования '
    'против самой Hindenburg по подозрению в манипулировании рынком '
    '— следствие польской прокуратуры по состоянию на середину 2026 '
    'года приостановлено в ожидании международной правовой помощи США.')
NEW_EVENTS = [
    {
        'kind': 'other',
        'date': '2025-07-11',
        'title': 'Польский регулятор оштрафовал LPP на 1,8 млн злотых',
        'note': ('LPP согласилась заплатить штраф 1,8 млн злотых '
                  '(€420 тыс.) для урегулирования расследования '
                  'Комиссии по финансовому надзору (KNF) — регулятор '
                  'счёл, что компания несвоевременно раскрыла ключевые '
                  'условия и структуру продажи российского бизнеса в '
                  '2022 году. Сама компания подчёркивает, что выводы '
                  'регулятора не связаны с отчётом Hindenburg Research '
                  '2024 года.'),
        'source': ['Notes from Poland', 'https://notesfrompoland.com/'
                   '2025/07/11/polish-retail-giant-lpp-accepts-1-8m-'
                   'zloty-fine-over-disclosure-failings-linked-to-'
                   'russia-exit/'],
    },
    {
        'kind': 'other',
        'date': '2026-04-21',
        'title': 'Второй штраф KNF — 15 млн злотых за ошибку в учёте',
        'note': ('KNF наложила на LPP штраф 15 млн злотых за '
                  'нарушения в раскрытии периодической отчётности — '
                  'спор о моменте отражения списания стоимости активов '
                  'в России и на Украине после начала войны. Решение '
                  'не окончательное, компания подала на пересмотр.'),
        'source': ['Omnichannel News', 'https://omnichannelnews.pl/'
                   '2026/04/22/bledy-ksiegowe-lpp-knf-naklada-15-mln-'
                   'zl-kary/'],
    },
]
NEW_SRCS = [
    ['Hindenburg Research', 'https://hindenburgresearch.com/lpp/'],
    ['Notes from Poland', 'https://notesfrompoland.com/2025/07/11/'
     'polish-retail-giant-lpp-accepts-1-8m-zloty-fine-over-disclosure-'
     'failings-linked-to-russia-exit/'],
    ['Omnichannel News', 'https://omnichannelnews.pl/2026/04/22/'
     'bledy-ksiegowe-lpp-knf-naklada-15-mln-zl-kary/'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert not card.get('events'), 'events уже не пуст: %r' % card.get('events')
    src = card.setdefault('src', [])
    to_add = [s for s in NEW_SRCS if s not in src]
    print('ПРАВИМ  %s: eco.context — обвинение Hindenburg Research (нейтрально)' % CARD_ID)
    print('ДОБАВИМ %s: 2 записи events[] — штрафы KNF' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['eco']['context'] = NEW_CONTEXT
        card['events'] = NEW_EVENTS
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
