# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ga3ca0cde` («Мосбиржа купила контроль в ООО «ПроКомплаенс»», закрыта
04.04.2023) — карточка уже год знает про опцион («В течение трех лет
доля может быть увеличена до 100%»), но не знает, что он реализован.

Проверено лично прямым WebFetch:
- Fomag.ru, https://fomag.ru/news/mosbirzha-delaet-stavku-na-sobstvennoe-po/,
  15.12.2025: «Мосбиржа увеличила долю в разработчике программного
  обеспечения "Прокомплаенс" до 100%. Изменения зафиксированы в ЕГРЮЛ
  12 декабря.»
- InvestFuture, https://investfuture.ru/articles/moskovskaya-birzha-zavershaet-pokupku-prokomplaens-dlya-usileniya-regtekha-1171753143,
  15.12.2025: «В апреле 2023 года Московская биржа приобрела 50,1% акций
  'Прокомплаенс' и объявила о намерении довести свою долю до 100% в
  течение трех лет» — подтверждает, что опцион исполнен даже раньше
  трёхлетнего срока (апрель 2023 -> декабрь 2025, менее 3 лет).

НЕ ВНЕСЕНО: точная сумма доплаты за оставшуюся долю — ни один источник
её не называет; независимая оценка компании — «сумма сделки не
раскрывается» во всех проверенных источниках; финансовые показатели
«ПроКомплаенс» за 2023-2025 годы — открытых публикаций с цифрами не
нашлось. Формулировка InvestFuture про «завершение приобретения
оставшихся 50%» (что арифметически не сходится с исходными 50,1%) не
используется — предпочтена более чистая формулировка Fomag.ru («доля...
до 100%»).

Запуск: python3 pipeline/fix_moex_procompliance_full_buyout.py
        python3 pipeline/fix_moex_procompliance_full_buyout.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga3ca0cde'

OLD_ECO_CONTEXT = (
    'до сделки компанию контролировал Александр Черепнин с долей в '
    'размере 53,23%, сейчас она сократилась до 26,56%. Остальные доли '
    'распределены между несколькими физлицами'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + '. Опцион на увеличение доли до 100% реализован '
    'раньше трёхлетнего срока: по данным ЕГРЮЛ, 12 декабря 2025 года '
    'Мосбиржа стала единственным владельцем «ПроКомплаенс».'
)

NEW_SRC = [
    ['Fomag.ru', 'https://fomag.ru/news/mosbirzha-delaet-stavku-na-sobstvennoe-po/'],
    ['InvestFuture', 'https://investfuture.ru/articles/moskovskaya-birzha-zavershaet-pokupku-prokomplaens-dlya-usileniya-regtekha-1171753143'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
