# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gadbed4b9` («Аквариус приобрел 67,8% в Аэродиск», июнь 2023, Закрыта)
— `eco.context` был заглушкой («—»), хотя есть хорошо задокументированный
факт интеграции после сделки: серийное производство СХД «Аэродиска» на
заводе «Аквариуса».

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- cnews.ru/news/top/2024-12-23_aerodisk_uvelichil_proizvodstvo
  (23.12.2024): «Компания «Аэродиск» начала серийное производство
  систем хранения данных (СХД) на заводе «Аквариуса» в Твери»;
  «Возможности этой площадки позволят «Аэродиску» в первое время
  производить до 500 СХД в год. В дальнейшем компания планирует
  увеличить объемы производства до 1,5 тыс. устройств в год».

НЕ ВНЕСЕНО: (1) реализация упомянутого в карточке права «Аквариуса» на
выкуп оставшейся доли (32,2%) — прямого объявления о новой сделке не
нашлось; реестровый след (обнуление долей прежних совладельцев в
августе 2024, закрытие состава участников для публики) не позволяет
однозначно отличить «доля перешла Аквариусу» от «прежние совладельцы
просто засекретили себя» без прямой выписки ЕГРЮЛ; (2) финансовые
показатели «Аэродиска» за 2023-2025 годы — источники дают
противоречивые порядки величин (например, прибыль 2022 года названа то
239 тыс., то 239 млн ₽ в разных пересказах одного и того же
агрегатора) и требуют личной проверки прямой выпиской, а не
пересказом; (3) дальнейшая продуктовая линейка (новые модели СХД 2025-
2026 годов) — известна только по агрегированным сниппетам поиска, не
проверена личным чтением.

Запуск: python3 pipeline/fix_akvarius_aerodisk_tver_production.py
        python3 pipeline/fix_akvarius_aerodisk_tver_production.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gadbed4b9'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'В декабре 2024 года «Аэродиск» начал серийное производство систем '
    'хранения данных на заводе «Аквариуса» в Твери — сначала до 500 '
    'устройств в год, с планом увеличить выпуск до 1,5 тыс. в год.'
)

OLD_SRC = [['CNews', 'https://www.cnews.ru/news/top/2023-06-26_akvarius_kupil_razrabotchika?ysclid=ljd77ce38n23024680']]
NEW_SRC = OLD_SRC + [
    ['CNews', 'https://www.cnews.ru/news/top/2024-12-23_aerodisk_uvelichil_proizvodstvo'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
