# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g7632fe9f` («Skillbox купил 10% сети школ рисования Grafika», Закрыта) —
`eco.context` уже несёт историю выхода Skillbox из капитала в 2024 году
(доля Андрея Ломтева выросла с 47,37% до 57,37%), но второй совладелец
компании не был назван.

Проверено WebSearch (сниппет-синтез с явным указанием источника —
rb.ru; прямой WebFetch на угаданный адрес статьи не открылся, а поиск по
точному тексту статьи не нашёл её оригинального URL в этой сессии):
второй совладелец ООО «Творческое образование» — Юрий Самохвалов, его
доля на момент выхода Skillbox — 46,63%.

НЕ ВНЕСЕНО и оставлено как открытый вопрос: сложение долей не сходится в
100% — 47,37% (Ломтев, ДО выкупа доли Skillbox) + 46,63% (Самохвалов) +
10% (Skillbox) = 104%. Расхождение не разрешено (не пересчитывается на
глаз) — возможно, одна из цифр относится к другому моменту времени или
пересчитана после иных корпоративных изменений. Продавец 10%-й доли
Skillbox в 2022 году (Ломтев, Самохвалов или оба пропорционально) в
первоисточнике (vc.ru/education/558122, проверено ЛИЧНО прямым WebFetch)
не назван — `seller` НЕ заполняется, чтобы не приписывать сделку одному
из двух совладельцев без подтверждения.

`buyer`/`status`/`title`/`date` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_skillbox_grafika_samokhvalov_stake.py
        python3 pipeline/fix_skillbox_grafika_samokhvalov_stake.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g7632fe9f'

OLD_ECO_CONTEXT = (
    'В мае 2022 года Skillbox объявил о планах открыть совместно с '
    'Grafika первые офлайн-школы в регионах России. Три заведения уже '
    'работают в Краснодаре, Казани и Санкт-Петербурге, а 8 декабря 2022 '
    'года состоялось официальное открытие пространств в Новосибирске, '
    'Воронеже и Красноярске. История завершилась выходом: 1 августа '
    '2024 года, по данным ЕГРЮЛ, Skillbox продал свои 10% гендиректору '
    'ООО «Творческое образование» Андрею Ломтеву, доля которого выросла '
    'с 47,37% до 57,37%. Skillbox входит в VK вместе с GeekBrains.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Второй совладелец компании — Юрий Самохвалов, '
    'его доля на момент выхода Skillbox составляла 46,63% (сложение '
    'трёх названных долей превышает 100% — расхождение источников не '
    'разрешено).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
