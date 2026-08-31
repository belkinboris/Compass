# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g4762fc3d
(Kama Flow, RBF Ventures и инвесторы привлекают 130 млн рублей в
DentalPro, статус «Обсуждается» с 2024 года) — раунд давно закрыт,
подтверждено и пресс-релизом инвестора, и реестром; заодно почищен
битый источник.

Закрытие раунда — проверено лично прямым WebFetch (Kama Flow,
09.01.2024): «Российский разработчик МИС DentalPRO (ООО "Дион-софт"...)
закрыл инвестиционный раунд на 130 млн рублей.» Подтверждено реестром
— проверено лично прямым WebFetch (audit-it.ru): среди текущих
учредителей ООО «ДИОН СОФТ» — «ДОГОВОР ИНВЕСТИЦИОННОГО ТОВАРИЩЕСТВА
"ВЕНЧУРНЫЙ ФОНД НАЦИОНАЛЬНОЙ ТЕХНОЛОГИЧЕСКОЙ ИНИЦИАТИВЫ" (уполномоченный
управляющий: ООО "КФ ВЕНЧУРС")» и «ООО "РАПИД ТЕХНОЛОДЖИ"» — новые
участники, вошедшие в капитал уже после раунда.

Рост показателей — проверено лично прямым WebFetch (audit-it.ru):
«В 2025 году организация получила выручку в сумме 174 млн руб., что на
68,6 млн руб., или на 65,1%, больше, чем годом ранее» (2024 год —
~106 млн руб.).

`status`: «Обсуждается» → «Закрыта» — раунд закрыт словом самого
инвестора и подтверждён составом участников в реестре.

Битый источник — первый элемент `src` (подписан «TAdviser») хранил URL
с ДВОЙНЫМ процентным кодированием кириллицы и хвостом от поля
гиперссылки Word (`" \\o "`) — при декодировании дважды адрес ведёт на
`Компания:Венчурный_фонд_Национальной_технологической_инициативы_(НТИ)»
— страницу о самом ФОНДЕ Kama Flow, а не о сделке DentalPro, и в
исходном виде URL нерабочий (страница не откроется по буквальным
`%25`). Рабочая ссылка на чужую страницу хуже удалённой битой — снят,
источник Kama Flow остаётся действующим (`test_every_deal_has_a_source_
link` по-прежнему выполняется), добавлен audit-it.ru за независимую
проверку выручки и состава учредителей.

Запуск: python3 pipeline/fix_dentalpro_round_closed_and_growth.py
        python3 pipeline/fix_dentalpro_round_closed_and_growth.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4762fc3d'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_EXTRA = (
    'Инвестиционный раунд привлечения капитала. Инвесторы: Kama Flow '
    '(управляет Венчурным фондом НТИ при участии РВК), Российско-'
    'белорусский фонд венчурных инвестиций (RBF Ventures), а также '
    'группа неназванных профильных отраслевых инвесторов. Размер доли '
    'не раскрывается, изменения в ЕГРЮЛ пока не произошли. (DentalPro '
    '(ООО «ДИОН СОФТ»))'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Раунд закрыт: по данным реестра, в капитал ООО «ДИОН СОФТ» вошли '
    'новые участники, включая структуру Kama Flow и ООО «Рапид '
    'Технолоджи». Выручка компании выросла со 106 млн руб. в 2024 году '
    'до 174 млн руб. в 2025 году (+65,1%).'
)

OLD_TADVISER_URL = 'https://www.tadviser.ru/index.php/%25D0%259A%25D0%25BE%25D0%25BC%25D0%25BF%25D0%25B0%25D0%25BD%25D0%25B8%25D1%258F:%25D0%2592%25D0%25B5%25D0%25BD%25D1%2587%25D1%2583%25D1%2580%25D0%25BD%25D1%258B%25D0%25B9_%25D1%2584%25D0%25BE%25D0%25BD%25D0%25B4_%25D0%259D%25D0%25B0%25D1%2586%25D0%25B8%25D0%25BE%25D0%25BD%25D0%25B0%25D0%25BB%25D1%258C%25D0%25BD%25D0%25BE%25D0%25B9_%25D1%2582%25D0%25B5%25D1%2585%25D0%25BD%25D0%25BE%25D0%25BB%25D0%25BE%25D0%25B3%25D0%25B8%25D1%2587%25D0%25B5%25D1%2581%25D0%25BA%25D0%25BE%25D0%25B9_%25D0%25B8%25D0%25BD%25D0%25B8%25D1%2586%25D0%25B8%25D0%25B0%25D1%2582%25D0%25B8%25D0%25B2%25D1%258B_(%25D0%259D%25D0%25A2%25D0%2598)%22%20%5Co%20%22%C3%82%C3%A5%C3%AD%C3%B7%C3%B3%C3%B0%C3%AD%C3%BB%C3%A9%20%C3%B4%C3%AE%C3%AD%C3%A4%20%C3%8D%C3%A0%C3%B6%C3%A8%C3%AE%C3%AD%C3%A0%C3%AB%C3%BC%C3%AD%C3%AE%C3%A9%20%C3%B2%C3%A5%C3%B5%C3%AD%C3%AE%C3%AB%C3%AE%C3%A3%C3%A8%C3%B7%C3%A5%C3%B1%C3%AA%C3%AE%C3%A9%20%C3%A8%C3%AD%C3%A8%C3%B6%C3%A8%C3%A0%C3%B2%C3%A8%C3%A2%C3%BB%20(%C3%8D%C3%92%C3%88)'

NEW_SRC = [
    ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1211600006287_ooo-dion-soft'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['extra'] == OLD_EXTRA
    assert deal['src'][0][1] == OLD_TADVISER_URL

    new_src = [deal['src'][1]] + NEW_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: станет (битый TAdviser снят) ===')
    for s in new_src:
        print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
