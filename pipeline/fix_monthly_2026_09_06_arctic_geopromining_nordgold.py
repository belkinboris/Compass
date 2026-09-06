# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), три карточки:
`gmru-nordline-totalenergies-arctic`, `gmru-geopromining-zabaikalie`,
`gmru-nordgold-chukotka` — по каждой нашёлся новый факт вне кэша притока.

1) gmru-nordline-totalenergies-arctic («НордЛайн»/TotalEnergies/«Арктик
   СПГ 2», стояла «Согласование получено» с 23 июля 2026 — было только
   президентское распоряжение). Проверено ЛИЧНО прямым WebFetch
   (interfax.ru/business/1111538, 27 августа 2026, 11:06): «Французская
   TotalEnergies завершила передачу своей 10-процентной доли в ООО
   "Арктик СПГ 2" ООО "НордЛайн"»; «Сама стоимость передачи доли не
   раскрыта»; «Французская компания сохраняет свои права на возврат
   своей доли заемного финансирования проекта на сумму около $1,3 млрд.
   Такое возмещение может быть осуществлено в будущем с учетом
   применимых санкций». Сделка закрыта — статус и дата обновлены;
   сумма (`sum`/`eco.sum`) НЕ проставлена — источник прямо говорит, что
   она не раскрыта. $1,3 млрд — это право взыскать заёмное
   финансирование ПОЗЖЕ, а не цена доли (родня уже записанного урока
   про TotalEnergies/$4,1 млрд списание 2022 года, которое тоже не было
   ценой сделки, — тот же покупатель второй раз рискует спутать разные
   числа).

2) gmru-geopromining-zabaikalie («ГеоПроМайнинг»/«Золотоноша», Закрыта,
   20 июля 2026) — сумма по-прежнему не названа нигде; проверено ЛИЧНО
   прямым WebFetch (kommersant.ru/doc/8829974): та же статья, что уже
   в `src`, называет закрытие «концом мая» 2026 года — это НЕ совпадает
   с датой самой карточки (20 июля). НЕ РАЗРЕШЕНО механически: неясно,
   что именно означают эти два месяца (дата подписания против даты
   регистрации перехода доли, или ошибка одного из шагов разбора) —
   расхождение зафиксировано честно в `eco.context`, `date` карточки НЕ
   тронута.

3) gmru-nordgold-chukotka (Nordgold/«Новая сырьевая компания»/Чукотка,
   Закрыта, 15 июля 2026) — точная доля/сумма M&A-сделки по-прежнему не
   названы; проверено ЛИЧНО прямым WebFetch (gold.1prime.ru/20260901/
   chukotka-1786018.html): на ВЭФ 1 сентября 2026 года Чукотка и
   Nordgold подписали ОТДЕЛЬНОЕ соглашение об инвестициях в постройку
   ГОКа на месторождении Ленотап — «достаточно большое соглашение — на
   70 миллиардов (рублей)», «более тысячи рабочих мест». Это заявленный
   ОБЪЁМ ИНВЕСТИЦИЙ В РАЗРАБОТКУ будущего актива, а НЕ цена самой
   M&A-сделки по покупке компании (в статье прямо нет ни слова о цене
   или доле покупки компании как отдельной сделки) — та же граница, что
   уже проведена для Arctic LNG 2 выше и раньше для TotalEnergies
   2022 года: крупная объявленная сумма инвестиций/списания — не цена
   сделки, пока источник не называет её именно так.

Все три поля `eco.context` уже прошли вычитку (`proofread_absorbed`) —
за основу слияния взят ТЕКУЩИЙ (уже вычитанный) текст поля, а не старый
`new` записей FIXES; сами записи (`batch_2026_c.py`,
`applied_before_2026_08_10.py`) обновлены тем же приёмом отдельно.

`buyer`/`seller`/`title`/`target`-структура всех трёх карточек НЕ
тронута.

Запуск: python3 pipeline/fix_monthly_2026_09_06_arctic_geopromining_nordgold.py
        python3 pipeline/fix_monthly_2026_09_06_arctic_geopromining_nordgold.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# --- gmru-nordline-totalenergies-arctic ---
NORDLINE_ID = 'gmru-nordline-totalenergies-arctic'
NORDLINE_OLD_STATUS = 'Согласование получено'
NORDLINE_NEW_STATUS = 'Закрыта'
NORDLINE_OLD_DATE = '2026-07-23'
NORDLINE_NEW_DATE = '2026-08-27'
NORDLINE_OLD_ECO_CONTEXT = (
    'Французская TotalEnergies в 2022 году списала свои активы в России '
    'на $4,1 млрд — главным образом акции «Арктик СПГ 2».'
)
NORDLINE_NEW_ECO_CONTEXT = (
    NORDLINE_OLD_ECO_CONTEXT + ' Сделку завершили 27 августа 2026 года: '
    'TotalEnergies передала свою 10-процентную долю «Нордлайну», сумму '
    'стороны не раскрыли. Французская компания сохраняет право позже '
    'взыскать вложенные в проект заёмные средства — около $1,3 млрд, '
    'если это позволят санкции.'
)
NORDLINE_OLD_SRC = [
    ['mergers.ru', 'https://mergers.ru/news/TotalEnergies-ozhidaet-skorogo-zaversheniya-processa-prodazhi-10-Arktik-SPG-kompanii-Nordlajn-87257'],
    ['mergers.ru', 'https://mergers.ru/news/Putin-razreshil-NordLajn-kupit-u-TotalEnergies-10-v-Arktik-SPG-2-87029'],
]
NORDLINE_NEW_SRC = NORDLINE_OLD_SRC + [
    ['interfax.ru', 'https://www.interfax.ru/business/1111538'],
]

# --- gmru-geopromining-zabaikalie ---
GEOPRO_ID = 'gmru-geopromining-zabaikalie'
GEOPRO_OLD_ECO_CONTEXT = (
    '«ГеоПроМайнинг» разведывает, добывает и перерабатывает сурьму, '
    'золото, серебро, цинк, свинец и другие металлы, работает в Якутии '
    'и Забайкальском крае. Основные активы — месторождения Сарылах, '
    'Сентачан, Верхне-Менкече и Железный кряж. На последнем группа '
    'строит ГОК мощностью 2,5 млн тонн железной руды и 850 тыс. тонн '
    'золотосодержащей руды в год. Бенефициар «ГеоПроМайнинга», как '
    'следует из отчётности, — Александр Орехов, бывший деловой партнёр '
    'основателя AEON Романа Троценко.'
)
GEOPRO_NEW_ECO_CONTEXT = (
    GEOPRO_OLD_ECO_CONTEXT + ' Источник называет закрытие сделки «концом '
    'мая» 2026 года — это расходится с датой самой карточки (20 июля '
    '2026 года), расхождение не разрешено.'
)

# --- gmru-nordgold-chukotka ---
NORDGOLD_ID = 'gmru-nordgold-chukotka'
NORDGOLD_OLD_ECO_CONTEXT = (
    'По последним опубликованным данным, в 2021 году Nordgold '
    'произвела около 1 млн унций золота, выручка составила $1,8 млрд, '
    'чистая прибыль — $374,5 млн. Активы сосредоточены в Амурской '
    'области, Якутии, Казахстане и Африке. В 2025 году Nordgold '
    'приобрела компании с лицензиями на рудопроявления в Магаданской '
    'области, а в 2026 году стала совладельцем структуры с правами на '
    'изучение участков с золотом на Камчатке.'
)
NORDGOLD_NEW_ECO_CONTEXT = (
    NORDGOLD_OLD_ECO_CONTEXT + ' 1 сентября 2026 года на ВЭФ Чукотка и '
    'Nordgold подписали отдельное соглашение об инвестициях в '
    'строительство ГОКа на месторождении Ленотап — 70 млрд ₽, более '
    'тысячи рабочих мест; это заявленный объём инвестиций в разработку '
    'будущего актива, а не цена самой сделки по покупке компании, '
    'которая по-прежнему не раскрыта.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    nordline = by_id[NORDLINE_ID]
    geopro = by_id[GEOPRO_ID]
    nordgold = by_id[NORDGOLD_ID]

    assert nordline['status'] == NORDLINE_OLD_STATUS
    assert nordline['date'] == NORDLINE_OLD_DATE
    assert nordline['eco']['context'] == NORDLINE_OLD_ECO_CONTEXT
    assert nordline['src'] == NORDLINE_OLD_SRC

    assert geopro['eco']['context'] == GEOPRO_OLD_ECO_CONTEXT

    assert nordgold['eco']['context'] == NORDGOLD_OLD_ECO_CONTEXT

    print('=== nordline: status ===', NORDLINE_NEW_STATUS)
    print('=== nordline: date ===', NORDLINE_NEW_DATE)
    print('=== nordline: eco.context ===')
    print(NORDLINE_NEW_ECO_CONTEXT)
    print('=== nordline: src ===')
    print(NORDLINE_NEW_SRC)
    print()
    print('=== geopromining: eco.context ===')
    print(GEOPRO_NEW_ECO_CONTEXT)
    print()
    print('=== nordgold: eco.context ===')
    print(NORDGOLD_NEW_ECO_CONTEXT)

    if write:
        nordline['status'] = NORDLINE_NEW_STATUS
        nordline['date'] = NORDLINE_NEW_DATE
        nordline['eco']['context'] = NORDLINE_NEW_ECO_CONTEXT
        nordline['src'] = NORDLINE_NEW_SRC

        geopro['eco']['context'] = GEOPRO_NEW_ECO_CONTEXT

        nordgold['eco']['context'] = NORDGOLD_NEW_ECO_CONTEXT

        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
