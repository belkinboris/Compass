# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — дочитывание карточки
`c2adff6d3» («Qiwi завершила консолидацию российских активов и
разделение бизнеса», 1 августа 2023, weekly_researched 10 августа
2026). Карточка описывала только сам этап разделения бизнеса на
российский и международный сегменты — что случилось с активами
дальше (в частности, отзыв банковской лицензии в 2024 году), было
неизвестно.

Дельта-поиск (саб-агент + личная проверка WebFetch) нашёл всю
дальнейшую хронологию.

Личный WebFetch подтвердил дословно:

1) Отзыв лицензии (cbr.ru,
   https://www.cbr.ru/press/pr/?file=638441030839855571BANK_SECTOR.htm):
   «Банк России приказом от 21.02.2024 № ОД-266 отозвал лицензию на
   осуществление банковских операций»; причины — «вовлеченностью в
   проведение высокорисковых операций», «направленные на обеспечение
   расчетов между физическими лицами и теневым бизнесом»,
   «систематически допускал нарушения требований законодательства в
   области противодействия легализации», «многочисленные случаи
   открытия банком QIWI-кошельков с использованием персональных
   данных физических лиц без их ведома».

2) Завершение расчётов по продаже АО «КИВИ» (interfax.ru,
   https://www.interfax.ru/business/1087961): «Fusion Factor Fintech
   Limited завершила расчеты с NanduQ за российские активы» —
   «4 млрд рублей» и «29,288 млн ее акций класса B»; «У сторон не
   осталось непогашенных обязательств» (6 мая 2026). Изначальная сумма
   сделки (январь 2024) — 23,75 млрд ₽; после отзыва лицензии сумма
   была пересмотрена в меньшую сторону.

3) Делистинг с Московской биржи (interfax.com,
   https://interfax.com/newsroom/top-stories/114120/): «The company
   has currently no operational activities in Russia and has neither
   carried out nor declared a re-domiciliation... will keep Astana
   International Exchange as the key listing venue for its ADRs».

НЕ внесено дословно (саб-агент не смог получить прямую цитату — 401 на
RBC/mergers.ru): продажа ROWI Т-Банку в июне 2024 года — упомянута
только в пересказе, требует отдельной проверки; делистинг с Nasdaq
(SEC Form 25-NSE) — не проверялся лично в этом заходе.

Запуск:
    python3 pipeline/fix_qiwi_license_revoked_and_final_settlement.py            # сухой прогон
    python3 pipeline/fix_qiwi_license_revoked_and_final_settlement.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Статья описывает реструктуризацию Qiwi: первый этап консолидации '
    'российских активов (ROWI, RealWeb, КИВИ Финанс, КИВИ Лаб, КИВИ '
    'Технологии, КИВИ Платежи, Ракета Вселенная, ООО МФК Полет Фи) на '
    'баланс АО КИВИ. Планируется разделение российских и '
    'международных активов до 30 августа 2023 года, казахстанский '
    'бизнес переведён в QIWI plc.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' 21 февраля 2024 года Банк России отозвал лицензию у КИВИ Банка '
    '(приказ № ОД-266) — из-за вовлечённости в расчёты между физлицами '
    'и теневым бизнесом, нарушений в области противодействия '
    'легализации доходов и открытия QIWI-кошельков без ведома '
    'владельцев персональных данных. Ещё в январе 2024 года АО «КИВИ» '
    'было продано гонконгской Fusion Factor Fintech Limited (структура '
    'бывшего гендиректора Qiwi plc Андрея Протопопова) за 23,75 млрд ₽; '
    'после отзыва лицензии сумма была пересмотрена в меньшую сторону, '
    'и 6 мая 2026 года стороны полностью завершили расчёты — Fusion '
    'Factor заплатила 4 млрд ₽ и передала 29,288 млн акций класса B '
    'NanduQ, непогашенных обязательств не осталось. Международный '
    'сегмент (бывшая QIWI plc) сменил имя на NanduQ plc и ушёл с '
    'Московской биржи, оставив основным местом листинга Astana '
    'International Exchange в Казахстане.'
)

NEW_SRC = [
    ['cbr.ru', 'https://www.cbr.ru/press/pr/?file=638441030839855571BANK_SECTOR.htm'],
    ['Интерфакс', 'https://www.interfax.ru/business/1087961'],
    ['Interfax (EN)', 'https://interfax.com/newsroom/top-stories/114120/'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c2adff6d3']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'c2adff6d3 eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('c2adff6d3: eco.context дополнен (отзыв лицензии КИВИ Банка, '
          'продажа Fusion Factor Fintech и завершение расчётов в 2026 '
          'году, переименование в NanduQ, делистинг с MOEX); добавлены '
          'источники cbr.ru, interfax.ru, interfax.com')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
