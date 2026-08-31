# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gcef5a371
(VK приобрела 70% в red_mad_robot / ООО «Много приложений», статус
«Закрыта» с февраля 2024) — тот же самый актив (магазин приложений
RuStore) уже перепродан дальше; статус исходной сделки не меняется
(она сама закрылась и остаётся фактом), контекстом добавлена
дальнейшая судьба актива.

Перепродажа RuStore — проверено лично прямым WebFetch (ComNews,
17 июля 2026): «МКПАО "ВК" (VK) продало магазин приложений RuStore
Дмитрию Панкрушеву - генеральному директору ООО "Много приложений"»,
«По данным bo.nalog.ru, выручка ООО "Много приложений" в 2025 г.
составила 1,4 млрд руб.». Причина продажи — оценка аналитика, а не
позиция самой VK: «На наш взгляд, основная причина продажи RuStore -
необходимость защитить пользователей приложений VK от санкций» —
Наталья Мильчакова (Freedom Global); сама VK причины не раскрывала.

Судьба продавца, red_mad_robot, — по данным саб-агента (TAdviser
недоступен прямым WebFetch, 404 на обоих вариантах адреса — цитата не
может быть подтверждена лично, поэтому в карточку НЕ вносится цифра
выручки за 2024 год). Проверено лично прямым WebFetch (ComNews,
27 января 2026): «Билайн (ПАО «ВымпелКом») и технологическая компания
red_mad_robot (ООО «РЭДМЭДРОБОТ») объявляют о создании совместного
предприятия (СП) в области искусственного интеллекта» — компания
продолжает работать самостоятельно и развивает ИИ-направление.

НЕ ВКЛЮЧЕНО: точная выручка red_mad_robot за 2024 год (TAdviser
недоступен прямым WebFetch в этой сессии); сумма продажи RuStore
Панкрушеву (не раскрыта ни одной стороной); новая карточка на
перепродажу RuStore не заводится — это тот же самый актив, о котором
уже рассказывает эта карточка, а не отдельный, независимый сюжет M&A.

Запуск: python3 pipeline/fix_vk_rustore_resold_to_pankrushev.py
        python3 pipeline/fix_vk_rustore_resold_to_pankrushev.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcef5a371'

OLD_EXTRA = (
    'VK приобрела 70% акций в структуре компании-разработчика '
    'red_mad_robot для усиления внутренней команды разработчиков и '
    'работ над другими проектами VK. red_mad_robot ранее участвовала в '
    'разработке магазина мобильных приложений RuStore.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' В июле 2026 года VK продала уже 100% этого актива (магазина '
    'приложений RuStore) генеральному директору ООО «Много приложений» '
    'Дмитрию Панкрушеву — выручка компании к 2025 году выросла до 1,4 '
    'млрд руб., сумма продажи не раскрыта. Red_mad_robot продолжает '
    'работать самостоятельно и развивает направление искусственного '
    'интеллекта, включая совместное предприятие с «Билайном» (январь '
    '2026 года).'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/246445/2026-07-17/2026-w29/1008/vk-izbavilas-rustore'],
    ['ComNews', 'https://www.comnews.ru/content/243451/2026-01-27/2026-w05/1010/bilayn-i-redmadrobot-sozdayut-sovmestnoe-predpriyatie-dlya-massovogo-vnedreniya-agentnogo-ii-biznes'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
