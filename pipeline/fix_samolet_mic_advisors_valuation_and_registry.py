# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `geb343fe1`
(«Группа «Самолет» закрыла покупку застройщика ГК «МИЦ»», 40 млрд ₽,
2023-06-26) — дочитывание нашло консультантов покупателя, независимую
оценку сделки и текущее состояние юрлица продавца.

Проверено (по докладу саб-агента, дословные цитаты):
- erzrf.ru/news/krupneyshaya-sdelka-v-istorii-rossiyskogo-rynka-zhilogo-
  developmenta-gk-samolet-pokupayet-gk-mits-tsena--ot-40-mlrd-rub-do-60-
  mlrd-rub: «для проведения независимой финансовой, налоговой и
  юридической экспертизы, а также предоставления консультационных услуг
  по сделке девелопер привлек компанию Б1 и юридическую фирму Stonebridge
  legal» (в тексте «девелопер» = покупатель, «Самолет») — до этой правки
  `law.adv` нёс только консультанта ПРОДАВЦА (Forward Legal); прямого
  собственного подтверждения от Stonebridge Legal не нашлось (её сайт и
  карточка на pravo.ru эту сделку не упоминают), но связка названа прямым
  текстом отраслевого издания.
- erzrf.ru (тот же материал, со ссылкой на «Ведомости»): «сумма сделки
  оценивалась в 40–60 млрд руб.» — диапазон экспертных оценок ДО закрытия.
- vedomosti.ru/business/news/2023/10/25/1002357-vtb-nazval-stoimost
  (25.10.2023, ПОСЛЕ закрытия): «ВТБ полностью профинансировал сделку
  группы компаний «Самолет» по покупке девелопера МИЦ на сумму 45,6 млрд
  руб.» — фактическая сумма финансирования, выше заявленных на момент
  объявления 40 млрд ₽.
- audit-it.ru/contragent/1127746636951_ooo-gk-mits: головное ООО «ГК
  «МИЦ»» по-прежнему «коммерческая, действующая» (не ликвидирована и не
  реорганизована), но «выручка отсутствовала в 2024–2025 годах,
  численность сотрудников составляет всего 1 человек, чистые активы на
  31.12.2025 были отрицательными».

НЕ ВНЕСЕНО: (1) отдельная независимая оценка МИЦ от профильного оценщика
недвижимости — не найдена, только диапазон СМИ и факт финансирования ВТБ,
уже внесённые; (2) судьба бренда МИЦ и переименование конкретных ЖК —
источники противоречат друг другу (один агрегатор недвижимости показывает
0 строящихся объектов, другой — 4 активных ЖК под старым брендом), прямого
пресс-релиза «Самолета» нет; (3) личная судьба продавцов (Рябинский,
Копылков) после сделки — все найденные материалы идут только с
таблоидных сайтов (kompromat1.online и подобные) с непроверяемыми и
местами прямо ошибочными утверждениями (один источник путает покупателя,
называя «Интер РАО» вместо «Самолета») — недостаточно надёжно для записи;
(4) реестровые данные о форме перехода отдельных проектных юрлиц
(«СЗ МИЦ-N») к «Самолету» — не найдены, только разрозненные упоминания
без деталей.

Запуск: python3 pipeline/fix_samolet_mic_advisors_valuation_and_registry.py
        python3 pipeline/fix_samolet_mic_advisors_valuation_and_registry.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'geb343fe1'

OLD_LAW_ADV = [
    ['Юридический консультант владельцев ГК «МИЦ» (продавца)',
     'Forward Legal',
     'Продажа группе «Самолет» (~40 млрд руб). Эльмира Кондратьева, '
     'Григорий Нистратов, Юлия Фёдорова (Бунигина), Маргарита Баженова. '
     'Источник: pravo.ru'],
]
NEW_ADV_ENTRY = [
    'Финансовый и юридический консультант ГК «Самолет» (покупателя)',
    'Б1 и Stonebridge Legal',
    'Провели независимую финансовую, налоговую и юридическую экспертизу '
    'перед покупкой ГК «МИЦ». Источник: erzrf.ru',
]

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'До закрытия эксперты рынка оценивали сделку в 40–60 млрд ₽ (по '
    'данным «Ведомостей», через erzrf.ru); по факту ВТБ полностью '
    'профинансировал покупку на сумму 45,6 млрд ₽ — выше изначально '
    'объявленных 40 млрд ₽.'
)

OLD_ECO_CONTEXT = (
    'ГК «МИЦ» основана в 1999 году. Её основатель и председатель совета '
    'директоров — Андрей Рябинский.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По данным ЕГРЮЛ (audit-it.ru), головное ООО «ГК '
    '«МИЦ»» продолжает числиться действующим, но выручки в 2024–2025 '
    'годах не имело, а численность сотрудников сократилась до одного '
    'человека.'
)

NEW_SOURCES = [
    ['ERZ.RF', 'https://erzrf.ru/news/krupneyshaya-sdelka-v-istorii-'
               'rossiyskogo-rynka-zhilogo-developmenta-gk-samolet-'
               'pokupayet-gk-mits-tsena--ot-40-mlrd-rub-do-60-mlrd-rub'],
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/10/25/'
                  '1002357-vtb-nazval-stoimost'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_LAW_ADV
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    new_adv = OLD_LAW_ADV + [NEW_ADV_ENTRY]

    print('=== law.adv: станет ===')
    print(new_adv)
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавятся ===')
    print(NEW_SOURCES)

    if write:
        deal['law']['adv'] = new_adv
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        existing = {tuple(s) for s in deal.get('src', [])}
        for s in NEW_SOURCES:
            if tuple(s) not in existing:
                deal.setdefault('src', []).append(s)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
