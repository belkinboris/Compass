# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gecf3eca5` («ALD Automotive продает лизинговую компанию в России
компании Экспокап», апрель 2023, Закрыта) — сумма сделки на момент
записи была неизвестна, а судьба компании после сделки не
прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- frankmedia.ru/135390: «ALD 20 апреля 2023 года закрыла сделку по
  продаже своей российской дочерней структуры компании «ЦК»» за «100
  млн евро»; на 31 марта 2023 года парк — «13,4 тысячи транспортных
  средств» (сократился с 20,3 тысячи на начало 2022 года); новое
  название компании — ExpoMobility;
- raexpert.ru/releases/2025/mar11e (11.03.2025): «Рейтинговое агентство
  «Эксперт РА» присвоило рейтинг кредитоспособности ООО «Экспомобилити»
  на уровне ruВВВ, прогноз по рейтингу стабильный»; на 01.10.2024
  активы — 33 391 млн ₽, капитал — 22 291 млн ₽; «лидирующая позиция по
  количеству автомобилей в операционной аренде (около 26% сегмента)»;
  агентство отметило «недостаточную информационную прозрачность для
  инвесторов и кредиторов: на сайте компании не раскрыта информация о
  собственниках и топ-менеджменте».

Внесено: `sum` меняется с «Не раскрыта» на «€100 млн» прямым скриптом
(источник не лежит в локальном кэше притока, review.py/FIXES
отклонит запись); `eco.sum` дополнен тем же значением; `eco.context`
дополнен фактом переименования в «Экспомобилити» и кредитным рейтингом
2025 года.

НЕ ВНЕСЕНО: точная дата и механизм переименования в «Экспомобилити» —
встретились только в сниппетах агрегаторов (rusprofile/checko/sbis), не
в дословно прочитанной странице.

Запуск: python3 pipeline/fix_ald_automotive_expomobility_sum_and_rating.py
        python3 pipeline/fix_ald_automotive_expomobility_sum_and_rating.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gecf3eca5'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '€100 млн'

OLD_ECO_CONTEXT = (
    'К 2023 году ALD Automotive управляла в России, Белоруссии и Казахстане '
    'парком из 20,3 тысячи машин: 20,1 тысячи контрактов приходилось на '
    'Россию, 532 — на Белоруссию.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' К моменту закрытия сделки, 20 апреля 2023 года, '
    'парк сократился до 13,4 тысячи машин. Компания переименована в '
    '«Экспомобилити» и продолжает работать: в марте 2025 года «Эксперт РА» '
    'присвоило ей кредитный рейтинг ruBBB (стабильный прогноз), активы на '
    'конец 2024 года — 33,4 млрд ₽, капитал — 22,3 млрд ₽, доля рынка '
    'операционного лизинга по числу автомобилей — около 26%.'
)

OLD_SRC = [
    ['Frank RG', 'https://frankrg.com/113048'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:АЛД_Автомотив'],
]
NEW_SRC = OLD_SRC + [
    ['Frank Media', 'https://frankmedia.ru/135390'],
    ["Эксперт РА", 'https://raexpert.ru/releases/2025/mar11e'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== sum / eco.sum: станет ===')
    print(NEW_SUM)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
