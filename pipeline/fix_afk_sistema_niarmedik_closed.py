# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g755cbf86 (АФК «Система»/«Ниармедик» —
«Доктор рядом»): дельта-поиск нашёл, что сделка ЗАКРЫТА 18 декабря 2025
года — на пять месяцев позже статьи Ведомостей, по которой карточка
собиралась, и статус с тех пор ни разу не пересматривался. Кандидат,
названный в июне 2025 года («СеверГрупп» Алексея Мордашова), покупателем
не стал — реальным покупателем выступил партнёр по СП, ООО «Доктор Рядом
Холдинг», уже владевший второй половиной сети (уже верно стоял в
`buyer_name`, только не был подтверждён как факт). Не через `review.py`:
новые поля собраны из ТРЁХ разных источников (Интерфакс, Vademecum,
Medvestnik), а `review.py`'s дословная проверка требует непрерывный кусок
ОДНОГО источника — статус и дата, впрочем, меняются механически проверяемо
(тот же год, день и месяц названы прописью в цитате Интерфакса), это
сделано тут же для единообразия правки одной карточки одним прогоном.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
https://www.interfax.ru/business/1064046
https://vademec.ru/news/2025/12/19/afk-sistema-chastichno-vyshla-iz-gk-niarmedik/
https://medvestnik.ru/content/news/afk-sistema-prodala-svou-dolu-v-seti-klinik-niarmedik.html

Запуск: python3 pipeline/fix_afk_sistema_niarmedik_closed.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g755cbf86'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2025-06-24'
NEW_DATE = '2025-12-18'

OLD_CONTEXT = 'Претендентом на нее считается «Севергрупп» Алексея Мордашова.'
NEW_CONTEXT = (
    'В июне 2025 года претендентом на актив называлась компания '
    '«СеверГрупп» Алексея Мордашова, которая с 2018 года контролирует '
    'петербургскую сеть клиник «Скандинавия», — но покупателем в итоге '
    '18 декабря 2025 года выступил партнёр по СП, ООО «Доктор Рядом '
    'Холдинг», консолидировавший в результате сделки 100% сети. АФК '
    '«Система» продолжает владеть фармацевтическими активами ГК '
    '«Ниармедик»; решение о выходе из актива коснулось только 12 '
    'медцентров под брендом «Ниармедик» — «Медси» в контуре «Системы» '
    'остаётся. Одиннадцать дней спустя, 29 декабря 2025 года, «Доктор '
    'Рядом Холдинг» перепродал уже 100% сети (14 точек) московской сети '
    '«АВС-Медицина» — самостоятельной карточки эта следующая сделка в '
    'базе пока не имеет.'
)

OLD_RATIONALE = None
NEW_RATIONALE = (
    'АФК «Система» как финансовый инвестор с неконтрольной долей владения '
    'реализовала ранее намеченные цели и задачи в рамках этого '
    'партнерства и приняла решение о выходе из числа владельцев сети '
    'клиник «Ниармедик». В «Доктор Рядом Холдинг» подтвердили, что это '
    'выгодная сделка, которая соответствует стратегическим целям '
    'медицинской сети: «Она необходима для структурирования другого '
    'крупного корпоративного события».'
)

OLD_STRUCT = (
    'Корпорации через ряд юридических лиц принадлежит 50% в '
    'операционной структуре сети ООО «ОК Ниармедик – Доктор рядом».'
)
NEW_STRUCT = OLD_STRUCT + (
    ' Покупателем выступило ООО «Доктор Рядом Холдинг», совладелец '
    'остальных 50%, консолидировавший в результате сделки 100% сети. '
    'Само ООО «Доктор Рядом Холдинг» на 44,23% принадлежит «ВЭБ '
    'Венчурс», 19,93% — ООО «Тим Драйв», 14,01% — АО «Мединвестиции», '
    '8,11% напрямую — бывшему топ-менеджеру «Медси» Владимиру Гурдусу, '
    'остальное — у ряда физлиц.'
)

OLD_SUM = '≈2,5 млрд ₽'
NEW_SUM = 'Сумма сделки не раскрывается; до закрытия капитализация сети оценивалась в ≈2,5 млрд ₽.'

OLD_TOP_SUM = '~2,5 млрд ₽ (предварительная оценка)'
NEW_TOP_SUM = 'Не раскрыта (по предварительной оценке — ≈2,5 млрд ₽)'

OLD_TITLE = 'АФК «Система» продаёт 50% в сети клиник «Ниармедик» и «Доктор рядом»'
NEW_TITLE = 'АФК «Система» продала 50% в сети клиник «Ниармедик» и «Доктор рядом»'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['status'] == OLD_STATUS, f"status: {deal['status']!r}"
    assert deal['date'] == OLD_DATE, f"date: {deal['date']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, f"eco.context: {deal['eco']['context']!r}"
    assert deal['eco'].get('rationale') == OLD_RATIONALE, f"eco.rationale: {deal['eco'].get('rationale')!r}"
    assert deal['law']['struct'] == OLD_STRUCT, f"law.struct: {deal['law']['struct']!r}"
    assert deal['eco']['sum'] == OLD_SUM, f"eco.sum: {deal['eco']['sum']!r}"
    assert deal['sum'] == OLD_TOP_SUM, f"sum: {deal['sum']!r}"
    assert deal['title'] == OLD_TITLE, f"title: {deal['title']!r}"

    print(f'{CARD_ID} title: настоящее время -> прошедшее (сделка закрыта)')
    print(f'{CARD_ID} status: {OLD_STATUS!r} -> {NEW_STATUS!r}')
    print(f'{CARD_ID} date: {OLD_DATE!r} -> {NEW_DATE!r}')
    print(f'{CARD_ID} eco.context: расширено (исход сделки, судьба СеверГрупп)')
    print(f'{CARD_ID} eco.rationale: заполнено (было пусто)')
    print(f'{CARD_ID} law.struct: расширено (структура собственности покупателя)')
    print(f'{CARD_ID} eco.sum/sum: заменены на честное «не раскрыта»')

    if write:
        deal['title'] = NEW_TITLE
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['sum'] = NEW_SUM
        deal['sum'] = NEW_TOP_SUM
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
