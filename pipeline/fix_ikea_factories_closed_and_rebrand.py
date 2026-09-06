# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g50d455bb` («Продажа фабрик IKEA в России компаниям Слотекс и
Лузалес», 2022, «Обсуждается») — сделка закрылась в марте 2023 года,
статус не был обновлён.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/5899090 (24.03.2023): «закрыла сделку по покупке» —
  про новгородский завод (структура Вадима Осипова, «Инвест Плюс»/
  Slotex); «на прошлой неделе сделку по покупке двух предприятий IKEA —
  в Тихвине Ленинградской области и Красной Поляне Кировской области —
  закрыла лесоперерабатывающая компания «Лузалес»»; «общая сумма всех
  сделок могла составить около 15 млрд руб.» (при первоначальной оценке
  IKEA около 20 млрд ₽, скидка до 25%; суммы по отдельным заводам
  сторонами не раскрывались);
- realty.ria.ru/20240605/zavod-1950685063.html (05.06.2024): новгородский
  завод переименован в «ООО «Экстраверт»»; «в марте 2023 года компания
  "Инвест Плюс"... приобрела производственную площадку IKEA»; на
  модернизацию направят «около 2,2 миллиарда рублей».

Внесено: `status` меняется с «Обсуждается» на «Закрыта» — не через
`review.py`/FIXES (источники не лежат в локальном кэше притока), а
прямым скриптом с `assert`. Дословное «закрыла сделку по покупке»
подтверждает переход без домысливания.

НЕ ВНЕСЕНО: судьба и ребрендинг тихвинского и кировского заводов
(«Лузалес») — ни название нового бренда, ни финансовые показатели не
встретились ни в одном из проверенных источников; отдельная проверка
реестров (СПАРК/«Рулевой») не проводилась.

Запуск: python3 pipeline/fix_ikea_factories_closed_and_rebrand.py
        python3 pipeline/fix_ikea_factories_closed_and_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g50d455bb'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_ECO_CONTEXT = (
    'В отчёте за 2022 финансовый год IKEA указывала, что рассчитывает '
    'завершить продажу четырёх заводов в РФ в начале 2023 года.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Так и вышло: в марте 2023 года все сделки '
    'закрылись — новгородский завод достался структуре Вадима Осипова '
    '(«Инвест Плюс»/Slotex), тихвинский и кировский — «Лузалесу»; общая '
    'сумма могла составить около 15 млрд ₽ (примерно на четверть меньше '
    'первоначальной оценки IKEA), суммы по отдельным заводам не '
    'раскрывались. Новгородский завод переименован в «Экстраверт» и к '
    '2024 году направил на модернизацию ещё около 2,2 млрд ₽.'
)

OLD_SRC = [
    ['Forbes', 'https://www.forbes.ru/biznes/485010-minpromtorg-nazval-pokupatelej-fabrik-usedsej-iz-rossii-svedskoj-ikea'],
]
NEW_SRC = OLD_SRC + [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5899090'],
    ['РИА Недвижимость', 'https://realty.ria.ru/20240605/zavod-1950685063.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
