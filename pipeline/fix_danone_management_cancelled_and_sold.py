# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `c7fd83d05`
(«Переход акций Danone Россия под управление Росимущества», июль 2023)
описывала только САМ факт передачи во временное управление; дальнейшая
судьба — отмена этого управления и продажа бизнеса конкретному
покупателю — не была отражена вовсе.

Личный WebFetch подтвердил дословно (Коммерсантъ,
https://www.kommersant.ru/doc/6563546): «Президент РФ Владимир Путин
отменил передачу долей в российских структурах... Danone во временное
управление Росимуществу. Указ опубликован 13 марта [2024]». Ведомости
(https://www.vedomosti.ru/business/articles/2024/03/13/1025133-putin-otmenil-peredachu-rossiiskih-aktivov-danone-v-upravlenie-rosimuschestva):
юристы связывают отмену с подготовкой продажи российских активов Danone
конкретному покупателю и с желанием избежать исков в международный
инвестиционный арбитраж.

Сама продажа (ООО «Вамин Р», 17,7 млрд ₽, закрытие 17 мая 2024 года) —
ОТДЕЛЬНАЯ сделка с другими сторонами и суммой, для неё в базе нет
карточки; здесь добавлена только краткая ссылка на то, что произошло
дальше, без пересказа деталей чужой сделки. Заведение отдельной
карточки — задача приточной рутины (см. CLAUDE.md, «Известные
проблемы»).

Запуск:
    python3 pipeline/fix_danone_management_cancelled_and_sold.py            # сухой прогон
    python3 pipeline/fix_danone_management_cancelled_and_sold.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Компанию переименовали в Life & Nutrition, её генеральным '
    'директором назначен Якуб Закриев — племянник главы Чечни Рамзана '
    'Кадырова. В совет директоров вошли приближённые Кадырова.'
)

NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' 13 марта 2024 года президент отдельным указом отменил временное '
    'управление Росимущества этими активами — юристы связывали это с '
    'подготовкой продажи бизнеса конкретному покупателю. Позже, 17 мая '
    '2024 года, Danone закрыла продажу российского бизнеса структуре '
    '«Вамин Р» — это отдельная сделка со своими сторонами и суммой.'
)

NEW_EVENTS = [
    {
        'date': '2024-03-13',
        'kind': 'other',
        'note': (
            'Президент РФ отдельным указом отменил временное управление '
            'Росимущества активами Danone в России.'
        ),
        'source': 'Коммерсантъ',
    },
]

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6563546'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/03/13/1025133-putin-otmenil-peredachu-rossiiskih-aktivov-danone-v-upravlenie-rosimuschestva'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c7fd83d05']

    assert d['eco'].get('context') == OLD_ECO_CONTEXT, 'eco.context изменился с момента написания скрипта: %r' % (d['eco'].get('context'),)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]
    existing_dates = {e.get('date') for e in d.get('events', [])}
    for ev in NEW_EVENTS:
        assert ev['date'] not in existing_dates, 'событие на эту дату уже есть'

    print('c7fd83d05: eco.context дополнен (отмена временного управления '
          '13.03.2024, ссылка на продажу «Вамин Р»); добавлено 1 событие; '
          'добавлено 2 источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d.setdefault('events', []).extend(NEW_EVENTS)
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
