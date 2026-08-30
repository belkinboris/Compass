# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gfde94a49
(ВкусВилл купил 95% ООО «Обед.ру» – сервис доставки еды в офисы) —
продавец не был назван вовсе, независимая оценка суммы отсутствовала,
`extra` было пустым полем, а судьба сделки после апреля 2024 года не
отражена. Проверено лично прямым WebFetch источника.

1) `seller` (новое поле) — прежние совладельцы 95%. Дословно
(Ведомости): «По 30% в «Обед.ру» ранее принадлежало совладельцам
рекрутингового сервиса Superjob.ru Сергею Габестро и Алексею Захарову,
а также Владимиру Орлову».

2) `eco.val` (новое поле) — независимая оценка. Дословно (Ведомости):
«Генеральный директор «Infoline-аналитики» Михаил Бурмистров оценил
сделку в 200 млн руб. с учетом высокой прибыльности и потенциала
масштабирования концепции».

3) `extra` (заполнено, было пустым) — краткое резюме сделки.

4) `eco.context` (новое поле) — докупка до 100% в октябре 2025 года.
Дословно (Интерфакс): «АО "Вкусвилл" довело до 100% долю в ООО
"Обед.ру"»; «Сервис сотрудничает с более чем 700 работодателями,
включая АО "ГЛОНАСС", SuperJob, Gismeteo и другие». Сумма второй
сделки не раскрыта, продавец 5%-й доли по имени не назван.

НЕ ВКЛЮЧЕНО: точное название кипрской компании, сохранявшей 5% до
октября 2025 (в `law.struct` уже стоит «Transportation Investments
Management» по АК&М/Интерфаксу, а Ведомости называют её «Транспортейшн
инвестментс холдинг лимитед» — это может быть одна и та же структура в
разных переводах, а может быть и нет; расхождение не разрешено, поле
не трогается); консультанты обеих сделок — не найдены ни в одном из 8
проверенных источников; выручка/оборот «Обед.ру» отдельно от группы
ВкусВилл за 2025-2026 год — не найдена.

Запуск: python3 pipeline/fix_vkusvill_obedru_seller_and_progress.py
        python3 pipeline/fix_vkusvill_obedru_seller_and_progress.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfde94a49'

NEW_SELLER = 'Сергей Габестро, Алексей Захаров и Владимир Орлов'

NEW_VAL = (
    '«Генеральный директор «Infoline-аналитики» Михаил Бурмистров '
    'оценил сделку в 200 млн руб. с учетом высокой прибыльности и '
    'потенциала масштабирования концепции» (Ведомости).'
)

OLD_EXTRA = ''
NEW_EXTRA = (
    'ВкусВилл приобрёл 95% ООО «Обед.ру» — сервиса доставки обедов в '
    'офисы — у прежних совладельцев, среди которых сооснователи '
    'Superjob.ru Сергей Габестро и Алексей Захаров.'
)

NEW_CONTEXT = (
    'В октябре 2025 года «АО «Вкусвилл» довело до 100% долю в ООО '
    '«Обед.ру»» (Интерфакс), выкупив оставшиеся 5%; сумма этой сделки '
    'не раскрыта. «Сервис сотрудничает с более чем 700 работодателями, '
    'включая АО «ГЛОНАСС», SuperJob, Gismeteo и другие» (Интерфакс).'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/04/05/1030173-vkusvill-kupil-stareishii'],
    ['Интерфакс', 'https://www.interfax.ru/business/1053739'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') is None
    assert deal['eco']['val'] == '—'
    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['context'] == '—'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== seller: станет {NEW_SELLER!r} ===')
    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = 'text'
        deal['eco']['val'] = NEW_VAL
        deal['extra'] = NEW_EXTRA
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
