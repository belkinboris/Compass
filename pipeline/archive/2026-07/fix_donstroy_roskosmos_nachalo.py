# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g97f0244e` («Донстрой купил у Роскосмоса участок на Пресне в
Москве», закрыта, 2022-12-15) — не было названо ни точное юрлицо-
продавец, ни судьба участка после сделки.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- list-org.com/company/12586265: «ФИЛИАЛ АКЦИОНЕРНОГО ОБЩЕСТВА "ЦЕНТР
  ЭКСПЛУАТАЦИИ ОБЪЕКТОВ НАЗЕМНОЙ КОСМИЧЕСКОЙ ИНФРАСТРУКТУРЫ" -
  "КОНСТРУКТОРСКОЕ БЮРО "МОТОР"»; зарегистрирован 30 января 2020 года
  как филиал АО «ЦЭНКИ» (структура Роскосмоса);
- finance.rambler.ru/realty/50322949 (перепечатка Ведомостей):
  «Предприятие продолжит оставаться арендатором площадки до августа
  2024 года»; оценка Тимура Рывкина (Nikoliers) — «рыночная стоимость
  площадки на Макеева оценивается в 11-13 миллиардов рублей»; план
  застройки — «жилой комплекс общей площадью 200-230 тысяч квадратных
  метров»;
- donstroy.moscow/press/news/donstroy-postroit-novyy-proekt-premium-
  klassa-nachalo/: «"Донстрой" построит новый проект премиум-класса
  "Начало"» (20.11.2025), «общей площадью более 218,8 тыс. кв. м» (962
  квартиры, свыше 100 тыс. кв. м), компания «получила разрешение на
  строительство»;
- novostroev.ru/novostroyki/moskva/cao/presnenskiy/nachalo/: адрес
  «ул. Сергея Макеева, 7/1» (совпадает с историческим адресом ФГУП КБ
  «Мотор»), стадия — «на стадии котлована», срок сдачи «1 кв. 2030».

НЕ ВНЕСЕНО: (1) официальная сумма сделки — не раскрыта ни одной из
сторон, везде фигурирует только оценка Рывкина; (2) причина продажи со
стороны Роскосмоса именно этого участка — есть только общий контекст
(секвестр космического бюджета), не прямое заявление госкорпорации по
этой сделке; (3) консультанты и согласования (Росимущество,
наблюдательный совет Роскосмоса) — ноль по всем проверенным
источникам; (4) число квартир в продаже на конкретную дату и точные
сроки ввода очередей — взяты только через WebSearch-сниппеты
(novostroy-m.ru), не вносятся без дословной проверки.

Запуск: python3 pipeline/fix_donstroy_roskosmos_nachalo.py
        python3 pipeline/fix_donstroy_roskosmos_nachalo.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g97f0244e'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Продавец — филиал АО «Центр эксплуатации объектов наземной '
    'космической инфраструктуры» (ЦЭНКИ, структура Роскосмоса) '
    '«Конструкторское бюро "Мотор"», зарегистрированный как филиал 30 '
    'января 2020 года. После продажи КБ продолжало арендовать площадку '
    'до августа 2024 года.'
)

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Официальная сумма сделки не раскрыта; директор департамента '
    'жилой недвижимости и девелопмента земли Nikoliers Тимур Рывкин '
    'оценивал рыночную стоимость участка в 11–13 млрд ₽.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'В ноябре 2025 года «Донстрой» анонсировал на участке премиальный '
    'жилой комплекс «Начало» общей площадью более 218,8 тыс. кв. м (962 '
    'квартиры) — разрешение на строительство получено, проект на '
    'стадии котлована, ввод намечен на 2029–2030 годы.'
)

OLD_SRC = [['Ведомости', 'https://www.vedomosti.ru/realty/articles/2023/03/06/965329-struktura-roskosmosa-prodala-krupnii-uchastok']]
NEW_SRC = OLD_SRC + [
    ['Донстрой (пресс-релиз)', 'https://donstroy.moscow/press/news/donstroy-postroit-novyy-proekt-premium-klassa-nachalo/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
