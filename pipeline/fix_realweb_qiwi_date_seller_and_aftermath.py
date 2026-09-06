# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g0a6f7569` («Qiwi купила рекламное агентство Realweb», Закрыта) — дата
стояла годом без месяца и дня, продавец не был заполнен вовсе, а судьба
Realweb внутри распродажи активов Qiwi в 2024 году не была отражена.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/5719709 (12.12.2022 16:57): «7 декабря 2022 года
  Qiwi заключила соглашение о приобретении 78% акций RealWeb», «а
  оставшиеся 22% будут приобретены в течение следующих шести месяцев».
- arka.am/.../qiwi_kupila_u_emina_avetisyana... (12.12.2022 17:31):
  «Сумму сделки компании не раскрывают, однако, по словам совладельца
  Realweb Эмина Аветисяна, она находится «в пределах рыночной
  стоимости»»; «Помимо iTech Capital, у группы Realweb пятеро
  совладельцев — Василий Лазука, Максим Виноградов, Иван Хмелевской, а
  также Эмин и Олеся Аветисяны».
- fomag.ru/news-streem/qiwi-prodaet-rossiyskie-aktivy-menedzhmentu-za-
  pochti-24-mlrd-rubley/ (20.01.2024): Qiwi продала российские активы
  «гонконгской компании Fusion Factor Fintech Limited, принадлежащей
  текущему CEO Qiwi Андрею Протопопову» за «23,75 млрд рублей», в пакет
  вошли «"Киви банк", "Киви кошелек", Qiwi Business, ... Rowi и Realweb,
  Flocktory, "Таксиагрегатор", IntellectMoney и другие проекты».
- sostav.ru/publication/gk-realweb-stanovitsya-gruppoj-rw-73236.html
  (18.02.2025): «От группы компаний к платформе: ГК Realweb становится
  группой RW+»; ребрендинг отражает «переход к новому этапу развития
  бизнеса, который за последние 3 года расширился благодаря запуску
  новых направлений и M&A сделок» (гендиректор на тот момент — Олеся
  Ромодина).

НЕ ВНЕСЕНО: смена гендиректора RW+ в 2025 году (Ромодина → Сергей
Яралян) и итоговая сумма расчёта Fusion Factor с Qiwi после пересмотра
условий в декабре 2025 — встретились только в заголовках/сниппетах
WebSearch, не подтверждены дословным чтением; отдельно не подтверждено
(и не опровергнуто), сохранился ли Realweb в периметре Fusion Factor
после 2024 года или перепродан ещё раз, как это произошло с Flocktory
из того же пакета.

`buyer`/`status` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_realweb_qiwi_date_seller_and_aftermath.py
        python3 pipeline/fix_realweb_qiwi_date_seller_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0a6f7569'

OLD_DATE = '2022'
NEW_DATE = '2022-12-07'

OLD_SELLER = None
NEW_SELLER = (
    'Совладельцы Realweb — Эмин и Олеся Аветисян, Василий Лазука, '
    'Максим Виноградов, Иван Хмелевской, а также фонд iTech Capital'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Qiwi купила сразу 78% акций, остальные 22% — в течение полугода. '
    'В январе 2024 года Qiwi продала все российские активы (включая '
    'Realweb, «Киви банк», «Киви кошелёк», Contact, Rowi, Flocktory и '
    'другие проекты) гонконгской Fusion Factor Fintech Limited, '
    'принадлежащей тогдашнему CEO Qiwi Андрею Протопопову, за 23,75 млрд '
    '₽. В феврале 2025 года ГК Realweb ребрендировалась в группу RW+.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal.get('seller') == OLD_SELLER
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['date'] = NEW_DATE
        deal['seller'] = NEW_SELLER
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
