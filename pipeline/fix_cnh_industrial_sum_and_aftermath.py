# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `g531446fe`
(«CNH Industrial продал российский бизнес по производству сельхозтехники
менеджменту», закрыта 25.04.2023) — `sum`/`eco.sum` стояли «Не раскрыта»,
хотя `eco.rationale` этой же карточки уже год как называет цену
дословной цитатой.

Проверено лично прямым WebFetch:
- Интерфакс, https://www.interfax.ru/business/896947, 20.04.2023, 15:38:
  «CNH Industrial объявил об уходе с российского рынка и продаже локальных
  активов за $60 млн»; «Среди активов CNH в РФ – производственные площадки
  по выпуску сельскохозяйственного оборудования и инвентаря, строительной
  техники, склад запчастей»; «Покупатель не называется» — то есть цена
  объявлена САМОЙ КОМПАНИЕЙ за неделю до закрытия (25.04.2023), охватывает
  весь российский бизнес (сельхоз- и стройтехника), а не только его часть.
- HeavyQuip Magazine, https://www.heavyquipmag.com/2023/04/20/cnh-exits-from-russia-business-activities-sold-for-60-million/,
  20.04.2023: «CNH Industrial announces the divestiture of its business
  activities in Russia for a total consideration of approximately $60
  million».
- Krasnodarmedia.su, https://krasnodarmedia.su/news/2309399/, 27.11.2025:
  «Компания Юнайтед Индастриал, официальный дистрибьютор современной
  сельскохозяйственной техники брендов McCormick, New Holland и Сase IH в
  России, озвучила ближайшие планы по открытию в декабре 2025 года
  филиала в Краснодаре площадью 3700 квадратных метров» — компания жива и
  расширяется спустя более двух лет после сделки.

НЕ ВНЕСЕНО: независимого подтверждения, что финальная цена ПРИ ЗАКРЫТИИ
(25.04.2023) совпала с объявленной 20.04.2023 (а не изменилась за неделю
между объявлением и закрытием), не нашлось — но и ни один источник её не
оспаривает, а других цифр в обороте нет; финансовые показатели
компании-правопреемника (по данным агрегатора checko.ru, недоступного
прямому WebFetch) — не вношу: под похожими именами («Юнайтед Индастриал»
и «Юнайтед Индастриал Дистрибушен») в реестре, похоже, числятся РАЗНЫЕ
юрлица одной группы, и без выписки ЕГРЮЛ нельзя быть уверенным, к какому
из них относятся найденные показатели (родня урока CLAUDE.md о
профилях-омонимах). Согласование ФАС/правкомиссии — ни один источник не
упоминает.

Запуск: python3 pipeline/fix_cnh_industrial_sum_and_aftermath.py
        python3 pipeline/fix_cnh_industrial_sum_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g531446fe'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '$60 млн'

OLD_ECO_SUM = 'Не раскрыта'
NEW_ECO_SUM = NEW_SUM

OLD_ECO_CONTEXT = (
    'Лизинговую и факторинговую «дочки» CNH Industrial в России (ООО '
    '«СиЭнЭйч Индастриал Файненшиал Сервисез Руссия» и ООО «СиЭнЭйч '
    'Индастриал Капитал Руссия») в феврале приобрела структура '
    'бизнесмена Игоря Кима (ООО «Экспокап»).'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Спустя более двух лет после сделки компания '
    'продолжает работать как официальный дистрибьютор McCormick, New '
    'Holland и Case IH в России и расширяется: в декабре 2025 года '
    'открыла филиал в Краснодаре площадью 3700 кв. м.'
)

NEW_SRC = [
    ['HeavyQuip Magazine', 'https://www.heavyquipmag.com/2023/04/20/cnh-exits-from-russia-business-activities-sold-for-60-million/'],
    ['Краснодар Медиа', 'https://krasnodarmedia.su/news/2309399/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_ECO_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_ECO_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
