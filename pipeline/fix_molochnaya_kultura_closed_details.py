# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g236a9b88` («Фонд Глеба Фетисова может приобрести ГК «Молочная
культура»», статус уже стоял «Закрыта», 2023) — заголовок остался в
форме предположения («может приобрести»), хотя сделка закрылась;
дочитывание нашло подтверждение одобрения ФАС, точную дату закрытия,
оценку стоимости и последующее прекращение банкротства группы.

Проверено (по докладу саб-агента, дословные цитаты):
- dp.ru/a/2023/12/04/nevesjolij-molochnik-kreditori (уже в src): «В
  августе Федеральная антимонопольная служба дала предварительное
  согласие московскому ООО "Продукты Питания" на покупку доли» — то
  есть согласование, запрошенное по kommersant.ru/doc/6123358,
  реально было дано.
- goodnessfoods-fund.com/sobytiya/kompaniya-zpif-goodness-foods-
  capital-fond-rosta-investirovala-v-gruppu-molochnaya-kultura —
  собственный пресс-релиз фонда-покупателя: «24 ноября 2023 г.» —
  точная дата закрытия сделки.
- newprospect.ru/news/articles/molochnaya-kultura-mezhdu-prodazhey-i-
  bankrotstvom/: «цена может быть около 100 млн рублей»; «Выручка
  головной компании ООО «Молочная культура» за прошлый год составила
  1,1 млрд рублей»; «объем ее заемных средств превышает 1,46 млрд
  рублей» — независимая оценка и финансовая нагрузка головной
  компании группы (это не то же юрлицо, что ТД «Молочная культура» из
  уже стоящего в карточке eco.target_fin — там другие цифры за 2022
  год для другой структуры группы).
- milknews.ru/index/Prekrashheno-bankrotstvo-GK-Molochnaja-kultura.html
  (08.04.2024): «Арбитражный суд Санкт-Петербурга и Ленобласти
  остановил процедуру банкротства ООО «Молочная культура» и АО
  «Сельцо». Производство по делу прекращено, поскольку структуры ГК
  «Молочная культура» погасили задолженность перед Россельхозбанком»
  — на сумму «около 1,1 млрд рублей». Это отдельное, более позднее
  событие (апрель 2024), а не часть самой сделки ноября 2023 года —
  добавлено как продолжение сюжета, без изменения структурных полей.

НЕ ВНЕСЕНО: (1) механизм сделки (пресс-релиз фонда говорит об
«увеличении капитала» компаний группы — это может означать cash-in, а
не выкуп долей у уже стоящих в карточке продавцов; dp.ru при этом
прямо пишет «ООО "Продукты Питания" приобрела X%» без уточнения
механизма) — расхождение не разрешено, поле `seller` (уже верно
сверено в прошлой правке с профилем-двойником `ga133cd89` по другой
сделке) не трогается, пока источники не согласованы; (2) юридический/
финансовый консультант — ноль по всем проверенным источникам,
включая собственный пресс-релиз покупателя; (3) точная дата подачи
ходатайства в ФАС (известен только месяц одобрения — август 2023).

Запуск: python3 pipeline/fix_molochnaya_kultura_closed_details.py
        python3 pipeline/fix_molochnaya_kultura_closed_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g236a9b88'
BUYER_ID = 'g260800fc'

OLD_DATE = '2023'
NEW_DATE = '2023-11-24'

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'В августе 2023 года Федеральная антимонопольная служба дала '
    'предварительное согласие ООО «Продукты питания» на покупку доли.'
)

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'По оценке отраслевого издания Newprospect, сделка могла составить '
    'около 100 млн ₽. Выручка головной компании ООО «Молочная культура» '
    'на тот момент составляла 1,1 млрд ₽, а её заёмные средства '
    'превышали 1,46 млрд ₽.'
)

OLD_ECO_CONTEXT = (
    '«Сигнет-Инвестиции 1» владеет также ООО «Иррико», которое '
    'управляет агрохолдингом «Яхрома» с активами в Подмосковье и '
    'Тамбовской области и ставропольской ГК «Иррико». Общий земельный '
    'банк — более 40 тыс. га: там выращивают картофель, овощи '
    'открытого грунта и зерно.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В апреле 2024 года арбитражный суд прекратил '
    'дело о банкротстве ООО «Молочная культура» и АО «Сельцо»: '
    'структуры группы погасили перед Россельхозбанком задолженность '
    'около 1,1 млрд ₽.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6123358'],
    ['dp.ru', 'https://www.dp.ru/a/2023/12/04/nevesjolij-molochnik-kreditori'],
]
NEW_SRC = OLD_SRC + [
    ['Newprospect.ru', 'https://newprospect.ru/news/articles/molochnaya-kultura-mezhdu-prodazhey-i-bankrotstvom/'],
    ['Milknews.ru', 'https://milknews.ru/index/Prekrashheno-bankrotstvo-GK-Molochnaja-kultura.html'],
    ['Goodnessfoods-fund.com', 'https://goodnessfoods-fund.com/sobytiya/kompaniya-zpif-goodness-foods-capital-fond-rosta-investirovala-v-gruppu-molochnaya-kultura'],
]

OLD_COMPANY_DESC = (
    'Покупатель, подконтрольный ЗПИФ «Сигнет-Инвестиции 1» и связанный '
    'с фондом Глеба Фетисова; в 2023 году обсуждал покупку 79% в трёх '
    'структурах ГК «Молочная культура», подано ходатайство в ФАС.'
)
NEW_COMPANY_DESC = (
    'Покупатель, подконтрольный ЗПИФ «Сигнет-Инвестиции 1» и связанный '
    'с фондом Глеба Фетисова; в ноябре 2023 года закрыл сделку по '
    'приобретению 25,1% ООО «Молочная культура» и по 79% в двух её '
    'структурах — ООО «ТД «Молочная культура» и ООО «Висмар Эстейт».'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    company = data['companies'][BUYER_ID]

    assert deal['date'] == OLD_DATE
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC
    assert company['desc'] == OLD_COMPANY_DESC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)
    print('\n=== company.desc: станет ===')
    print(NEW_COMPANY_DESC)

    if write:
        deal['date'] = NEW_DATE
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        company['desc'] = NEW_COMPANY_DESC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
