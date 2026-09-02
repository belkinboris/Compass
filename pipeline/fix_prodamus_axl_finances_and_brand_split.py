# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g7a750c03 («Платежный сервис Prodamus купил платформу онлайн-курсов
AXL», закрыта 2023) — не переносились финансовые показатели сторон на
момент сделки, судьба самого бренда AXL и цель роста выручки.

Проверено лично прямым WebFetch (RB.ru,
https://rb.ru/news/prodamus-axl-deal/): «Оценка актива производилась
на основе темпов роста выручки AXL, которая в первом полугодии
текущего года достигла 47 млн рублей. За весь 2022 год «10Х
ИТ-решения» получил выручку по РСБУ в 35 млн рублей», «ООО «Продамус»
получил выручку в 1 млрд рублей, чистая прибыль составила 240,7 млн
рублей» (2022 год), «планирует в результате сделки нарастить выручку
в 12 раз к 2025–2026 году».

Проверено лично прямым WebFetch (vc.ru,
https://vc.ru/u/1639419-zakulise-infobiznesa/797802-prodamus-axl-novost-goda,
цитата Дмитрия Юрченко): «Бренд AXL останется у первоначальных
владельцев (основателей AXL: Падре и Даниила) и будет использоваться
на иностранных рынках. Новые собственники (Продамус) выберут новое
название и анонсируют его», «Даниил Мусатов ещё долгое время будет
отвечать за развитие функционала ИТ-платформы, все ваши хотелки будут
реализовываться как и прежде».

Проверено лично прямым WebFetch (prodamus.ru/xl): продукт жив и
работает под новым именем — «1 500+ активных школ уже с нами».

НЕ ВКЛЮЧЕНО: цифра «выручка 10Х ИТ-решения за 2025 год — 90,5 млн ₽»
— встретилась только в сниппете поисковой выдачи, а не в скачанном
тексте источника, не переношу без дословной цитаты; достижение цели
«рост в 12 раз к 2025-2026» — расчёт по неподтверждённым цифрам, не
прямая цитата источника, не переношу; юридический консультант сделки
— не назван нигде.

Запуск: python3 pipeline/fix_prodamus_axl_finances_and_brand_split.py
        python3 pipeline/fix_prodamus_axl_finances_and_brand_split.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7a750c03'

NEW_ECO_TARGET_FIN = (
    'Оценка актива производилась на основе темпов роста выручки AXL: в '
    'первом полугодии 2023 года она достигла 47 млн ₽, за весь 2022 год '
    '«10Х ИТ-решения» получило выручку по РСБУ в 35 млн ₽.'
)

NEW_ECO_FIN = (
    'По итогам 2022 года ООО «Продамус» получило выручку в 1 млрд ₽, '
    'чистая прибыль составила 240,7 млн ₽. Компания рассчитывала '
    'нарастить выручку AXL в 12 раз к 2025–2026 году.'
)

NEW_LAW_STRUCT = (
    'Бренд AXL остался у первоначальных основателей (Дмитрия Юрченко и '
    'Даниила Мусатова) и используется ими на иностранных рынках — '
    'Prodamus получил только российское юрлицо и выбрал для него новое '
    'название (сейчас продукт работает как Prodamus.XL). Мусатов '
    'продолжил отвечать за развитие функционала ИТ-платформы.'
)

OLD_ECO_CONTEXT = (
    'Согласно данным «СПАРК-Интерфакса», единственным собственником ООО '
    '«10Х ИТ-решения» (российское юрлицо AXL) является Дмитрий Юрченко. '
    'Но в AXL пояснили, что кроме своей доли в активе, Юрченко также '
    'номинально владеет в нём долей второго совладельца компании — '
    'Даниила Мусатова'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    '. Спустя три года после продажи российской части оба основателя '
    'продолжают вместе развивать международный AXL под собственным '
    'брендом на других рынках.'
)

NEW_SRC = [
    ['RB.ru', 'https://rb.ru/news/prodamus-axl-deal/'],
    ['vc.ru', 'https://vc.ru/u/1639419-zakulise-infobiznesa/797802-prodamus-axl-novost-goda'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == '—'
    assert deal['eco']['fin'] == '—'
    assert deal['law']['struct'] == '—'
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.fin: станет ===')
    print(NEW_ECO_FIN)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['fin'] = NEW_ECO_FIN
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
