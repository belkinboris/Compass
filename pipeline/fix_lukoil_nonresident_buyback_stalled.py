# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g75837e8b` («ЛУКОЙЛ выкупает до 25% акций у нерезидентов», август
2022, статус «Обсуждается») — план держится без движения почти 4 года;
проверка показала сильный признак, что он застопорился на этапе заявки,
не дойдя даже до рассмотрения президентом.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- finance.rambler.ru/business/53598596-minfin-ne-poluchal-zayavku-lukoyla-na-vykup-aktsiy-u-nerezidentov/
  (18.10.2024, зам. министра финансов Алексей Моисеев в кулуарах
  Московского финансового форума): «На рассмотрении такого запроса
  нет. У нас ее в банке заявок на очереди нет» — спустя более года
  после первой заявки (2022–2023) Минфин заявил, что заявки от ЛУКОЙЛа
  на выкуп акций у нерезидентов у него НЕТ ВООБЩЕ, ни на рассмотрении,
  ни в очереди.

Прямого подтверждения ни закрытия, ни официального отказа не нашлось —
`STATUS_WORDS` не даёт механического основания сменить статус:
«заявки нет в очереди» не эквивалентно «отказал»/«отменен». Статус НЕ
менялся — находка внесена только в `eco.context`, а вопрос вынесен в
раздел «Известные проблемы» CLAUDE.md для решения человека (родня уже
описанных случаев БКС/«Форштадт», «Мать и дитя»/«Инвитро»).

НЕ ВНЕСЕНО: (1) отдельный, не связанный с этим планом buyback ЛУКОЙЛа
у Леонида Федуна в 2025 году (90,75 млн акций, ≈654 млрд ₽) — по
инвест-сводкам, не проверен личным чтением первоисточника, и это
структурно другая операция (выкуп у совладельца, а не у нерезидентов
со счетов типа «С»), не относится к предмету этой карточки; (2)
текущая доля нерезидентов в капитале ЛУКОЙЛа — не нашлась ни в одном
проверенном источнике.

Запуск: python3 pipeline/fix_lukoil_nonresident_buyback_stalled.py
        python3 pipeline/fix_lukoil_nonresident_buyback_stalled.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g75837e8b'

OLD_ECO_CONTEXT = 'Уставный капитал «ЛУКОЙЛа» состоит из 692 млн 865 тыс. 762 акций.'
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Спустя более двух лет после этой заявки, 18 '
    'октября 2024 года, замминистра финансов Алексей Моисеев заявил '
    'журналистам про заявку ЛУКОЙЛа: «На рассмотрении такого запроса '
    'нет. У нас ее в банке заявок на очереди нет» — то есть план так и '
    'не дошёл даже до рассмотрения, не говоря об одобрении президента.'
)

OLD_SRC = [['Интерфакс', 'https://www.interfax.ru/amp/917325']]
NEW_SRC = OLD_SRC + [
    ['Rambler Finance', 'https://finance.rambler.ru/business/53598596-minfin-ne-poluchal-zayavku-lukoyla-na-vykup-aktsiy-u-nerezidentov/'],
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
