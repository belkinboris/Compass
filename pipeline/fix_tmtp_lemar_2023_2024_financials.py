# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gb6b5625e` («Владимир Лисин продал Таганрогский морской торговый порт
ООО «Лемар»», 2022, Закрыта) — финансовая судьба порта после сделки не
прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- portnews.ru/news/361408/ (01.04.2024): «Чистый убыток АО
  «Таганрогский морской торговый порт» (ТагМТП) в 2023 году сократился
  в 2,96 раза по сравнению с предыдущим годом и составил 27,57 млн
  рублей»; выручка «на 13,4%, до 494 млн рублей»; чистые активы выросли
  с 720,6 млн ₽ до 727,3 млн ₽;
- gorodn.ru/.../taganrogskiy-torgovyy-port-uvelichil-vyruchku...: «Выручка
  АО «Таганрогский морской торговый порт» (ТМТП) в 2024 году выросла в
  1,87 раза, до 925,2 млн рублей, чистая прибыль общества достигла 402,4
  млн рублей»; рост связан с «восстановлением грузоперевозки в
  Азово-Донском бассейне» — источник не относит рост к смене владельца.

НЕ ВНЕСЕНО: личность конечного бенефициара ООО «Лемар» — ни один из
проверенных источников (2022-2025 годов) её не называет; попытка найти
профиль «Лемар» в реестре (rusprofile.ru/list-org.com) заблокирована
капчей, независимой проверки не получилось. Смена гендиректора порта в
апреле 2023 года (Сергей Нарышкин → Виктор Чертов, interfax.ru/business/
895666) — уже отражённый в других источниках факт, не проверялся заново
для этой карточки.

Запуск: python3 pipeline/fix_tmtp_lemar_2023_2024_financials.py
        python3 pipeline/fix_tmtp_lemar_2023_2024_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb6b5625e'

OLD_ECO_CONTEXT = (
    'АО «Таганрогский морской торговый порт» имеет семь грузовых причалов с '
    'максимальной осадкой пять метров. Общая площадь складов всесезонного '
    'порта составляет 46,6 тыс. кв. м. В 2021 году грузооборот предприятия '
    'составил 1,231 млн т.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' После сделки порт прошёл через убыточный период и '
    'вышел из него: в 2023 году чистый убыток сократился почти втрое — до '
    '27,6 млн ₽ (выручка выросла на 13,4%, до 494 млн ₽), а в 2024 году порт '
    'уже показал чистую прибыль 402,4 млн ₽ при выручке 925,2 млн ₽ — рост '
    'источники связывают с восстановлением грузоперевозок в Азово-Донском '
    'бассейне, а не со сменой владельца.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5873898'],
]
NEW_SRC = OLD_SRC + [
    ['PortNews', 'https://portnews.ru/news/361408/'],
    ['ГородN', 'https://gorodn.ru/razdel/novosti_kompaniy/praktika_biznesa/taganrogskiy-torgovyy-port-uvelichil-vyruchku-na-fone-vosstanovleniya-gruzoperevozok-v-azovo_donskom/'],
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
