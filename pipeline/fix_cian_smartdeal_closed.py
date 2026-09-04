# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gff93974e` («ЦИАН через «Айриэлтор» приобретает 100% SmartDeal»,
статус «Обсуждается», 2023-05-02) — сделка реально закрылась в
сентябре 2023 года, статус и дата остались в форме намерения.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- cnews.ru/news/top/2025-05-15_tsian_zaplatit_do_milliarda: «за 100%
  долю в ООО «Практика Успеха» было заплачено 754 млн руб.»; «Из этой
  суммы отложенное возмещение составляет 640 млн руб., условное
  возмещение — 114 млн руб.»; «Общая стоимость условного возмещения
  может достичь 478 млн руб. Соответственно, вся сумма сделки может
  составить 1 млрд руб.»; «ЦИАН консолидировала результаты работы
  SmartDeal за период с 19 сентября по 31 декабря 2023 г.»; «К концу
  2024 г. справедливая стоимость условного возмещения составляла уже
  194 млн руб., что было связано с достижением SmartDeal определённых
  показателей за 2023 г.»
- smart-lab.ru/blog/news/942501.php (19 сентября 2023 года): «Циан»
  получил разрешение от регулирующих органов в соответствии с
  предварительным договором, заключённым сторонами в апреле 2023
  года»; «сообщает о закрытии основного этапа сделки по приобретению
  100% долей в уставном капитале SmartDeal».

НЕ ВНЕСЕНО: (1) точная дата подписания финального договора купли-
продажи (известен только месяц — апрель 2023, до этого — предыдущий,
сорвавшийся по срокам согласования договор 2021 года); (2)
юридический/финансовый консультант — ноль по всем источникам.

Запуск: python3 pipeline/fix_cian_smartdeal_closed.py
        python3 pipeline/fix_cian_smartdeal_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gff93974e'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2023-05-02'
NEW_DATE = '2023-09-19'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '754 млн ₽ (до 1 млрд ₽ с учётом условного возмещения)'

OLD_LAW_APPR = (
    'Закрытие сделки зависит от ряда условий, в том числе от согласия '
    'комиссии Минфина.'
)
NEW_LAW_APPR = (
    'Осенью 2023 года Правительственная комиссия по контролю за '
    'иностранными инвестициями одобрила сделку, после чего она была '
    'завершена.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'Из 754 млн ₽ базовой суммы отложенное возмещение составило 640 '
    'млн ₽, условное возмещение (earn-out) — 114 млн ₽ на момент '
    'сделки; максимальная величина earn-out может достичь 478 млн ₽.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'К концу 2024 года справедливая стоимость условного возмещения '
    'выросла до 194 млн ₽ — SmartDeal достиг определённых показателей '
    'за 2023 год.'
)

OLD_SRC = [['Интерфакс', 'https://www.interfax.ru/amp/898723']]
NEW_SRC = OLD_SRC + [
    ['CNews', 'https://www.cnews.ru/news/top/2025-05-15_tsian_zaplatit_do_milliarda'],
    ['Smart-Lab', 'https://smart-lab.ru/blog/news/942501.php'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['sum'] == OLD_SUM
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== sum: станет ===')
    print(NEW_SUM)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['sum'] = NEW_SUM
        deal['law']['appr'] = NEW_LAW_APPR
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
