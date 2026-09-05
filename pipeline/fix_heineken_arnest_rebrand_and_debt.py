# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g64eb0e04` («Heineken продал активы в России ГК «Арнест» за 1 евро»,
август 2023, Закрыта) — судьба бизнеса и обещанный долг перед Heineken
после сделки не прослеживались.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/8160444: холдинг «Объединенные пивоварни» (ОПХ)
  переименован в «Пивоварни Бочкарев» — «согласно ЕГРЮЛ, смена
  произошла 23 октября, а с 1 ноября компания начнет использовать
  новое наименование в публичных коммуникациях»; выручка 2024 года
  «увеличилась на 18,73% до 48,45 млрд руб.», чистая прибыль «составила
  2,48 млрд руб. (против 13,8 млн руб. в 2023 году)»; «третье место по
  объему продаж в России с долей 10,9%», восемь заводов, более 20
  брендов;
- new-retail.ru/novosti/retail/novyy_vladelets_zavodov_heineken_pogasil_dolg_pered_gollandskoy_kompaniey/:
  гендиректор «Объединенных пивоварен» Анна Миронова на ПМЭФ 20 июня
  2025 года — «Арнест» вложил в компанию 28 млрд ₽, из них 17 млрд ₽ —
  на модернизацию производств, 11 млрд ₽ — на погашение долга перед
  голландской Heineken (обещанные при покупке €100 млн полностью
  выплачены); до 2030 года компания планирует вложить ещё «порядка 40
  млрд руб.» в расширение, модернизацию и маркетинг.

НЕ ВНЕСЕНО: (1) официальный сайт rbc.ru той же новости (20.06.2025) не
открылся напрямую (401) — использован независимый источник с той же
цитатой (new-retail.ru), дословность проверена; (2) спор или опцион на
обратный выкуп — не найдено ни слова, поле `law.terms` уже честно
говорит «Сделка не предусматривает опциона на обратный выкуп активов»
и не трогается.

Запуск: python3 pipeline/fix_heineken_arnest_rebrand_and_debt.py
        python3 pipeline/fix_heineken_arnest_rebrand_and_debt.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g64eb0e04'

OLD_ECO_CONTEXT = (
    'Долю компании на рынке Infoline оценивает в 10%, долю «Балтики» — '
    'в 27,3%, AB InBev Efes — в 25%. До июля 2023 года «Балтика» '
    'принадлежала Carlsberg.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Бизнес продолжает работать и расти: выручка '
    '2024 года — 48,45 млрд ₽ (+18,7%), прибыль — 2,48 млрд ₽ (против '
    '13,8 млн ₽ годом ранее). С ноября 2025 года холдинг переименован '
    'из «Объединённых пивоварен» в «Пивоварни Бочкарев». Обещанный '
    'Heineken долг в €100 млн полностью погашен — по словам гендиректора '
    'компании на ПМЭФ в июне 2025 года, «Арнест» вложил в бизнес 28 '
    'млрд ₽, из них 11 млрд ₽ ушли на погашение долга, 17 млрд ₽ — на '
    'модернизацию производств.'
)

OLD_SRC = [
    ['Forbes', 'https://www.forbes.ru/biznes/495208-heineken-prodal-svoi-aktivy-v-rossii'],
    ['РИА Новости', 'https://ria.ru/20230825/prodazha-1892149466.html'],
]
NEW_SRC = OLD_SRC + [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8160444'],
    ['New Retail', 'https://new-retail.ru/novosti/retail/novyy_vladelets_zavodov_heineken_pogasil_dolg_pered_gollandskoy_kompaniey/'],
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
