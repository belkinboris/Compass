# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g47189119` («МТС приобрела 66% платформы Buzzoola», закрыта
21.02.2023) — находка: доля в заголовке и в `extra` НЕВЕРНА. Плюс
`sum`/`eco.sum`/`eco.val` пустовали, а финансы предмета и судьба доли
после сделки известны из открытых источников.

Проверено лично прямым WebFetch:
- Интерфакс (единственный источник самой карточки),
  https://www.interfax.ru/business/887334: «ПАО "МТС" стало владельцем
  67% группы Buzzoola» — не 66%, как было в заголовке и `extra`; «у
  компании предусмотрена возможность выкупа еще 33% Buzzoola в 2024
  году».
- CNews, https://www.cnews.ru/news/top/2023-06-27_mts_potratila_337_millionov:
  «Сумма сделки по покупке 67% доли в компании составила 371 млн.
  Таким образом, вся компания была оценена в 553 млн руб.»
- Runet.news, https://runet.news/articles/61865 (со ссылкой на годовой
  отчёт МТС, март 2025): «Компания... потратила 2,2 млрд руб. на
  установление контроля» (довела долю с 67% до 100% в мае 2024 года);
  «справедливая стоимость ранее приобретённой доли составляет 1,08
  млрд руб.»; «вся компания оценена в 3,28 млрд руб.».

Заголовок и `extra` исправлены с 66% на 67% — это не спорная роль
стороны, а простая числовая опечатка, противоречащая собственному
источнику карточки.

НЕ ВНЕСЕНО: чистая прибыль предмета за 2021 год (11,7 млн ₽, ADPASS) —
по докладу саб-агента, не перепроверена мной лично прямым WebFetch в
этом прогоне; данные о выручке Buzzoola/МТС AdTech за 2023-2025 годы и
реорганизация МТС AdTech в АО (январь 2026) — из агрегированной
поисковой выдачи, не подтверждены прямым чтением первички.

Запуск: python3 pipeline/fix_mts_buzzoola_stake_correction_and_sum.py
        python3 pipeline/fix_mts_buzzoola_stake_correction_and_sum.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g47189119'

OLD_TITLE = 'МТС приобрела 66% платформы Buzzoola для размещения нативной рекламы'
NEW_TITLE = 'МТС приобрела 67% платформы Buzzoola для размещения нативной рекламы'

OLD_EXTRA = (
    'МТС приобрела 66% долей в ООО «Баззула интернет технологии» '
    '(бренд Buzzoola). У МТС есть call-опцион на выкуп оставшихся 33% '
    'в 2024 году. Платформа предоставляет услуги видеорекламы и '
    'текстово-графических рекламных блоков при скроллинге с охватом '
    'более 100 млн человек в России и странах СНГ.'
)
NEW_EXTRA = OLD_EXTRA.replace('приобрела 66%', 'приобрела 67%')

OLD_SUM = 'Не раскрыта'
NEW_SUM = '371 млн ₽'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = 'Вся компания на момент сделки оценена в 553 млн ₽.'

OLD_ECO_CONTEXT = (
    'МТС развивает собственные рекламные решения на основе данных '
    'своей цифровой экосистемы, облачных технологий, алгоритмов '
    '«больших данных» и искусственного интеллекта под зонтичным '
    'брендом «МТС Маркетолог»'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + '. В мае 2024 года МТС довела долю в Buzzoola с'
    ' 67% до 100%, заплатив за оставшиеся 33% ещё 2,2 млрд ₽ — по'
    ' данным годового отчёта МТС (март 2025), справедливая стоимость'
    ' ранее приобретённой доли на этот момент оценена в 1,08 млрд ₽,'
    ' вся компания — в 3,28 млрд ₽.'
)

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2023-06-27_mts_potratila_337_millionov'],
    ['Runet.news', 'https://runet.news/articles/61865'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['title'] == OLD_TITLE
    assert deal['extra'] == OLD_EXTRA
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== title: станет ===')
    print(NEW_TITLE)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['title'] = NEW_TITLE
        deal['extra'] = NEW_EXTRA
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
