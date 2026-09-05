# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g0dedddbd` («Goldman Sachs продал 9% акций ЦИАН компании Broomfield
International», 2022-12-01, Закрыта) — кто такая Broomfield и
дальнейшая судьба ЦИАН не прослеживались.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- pravo.ru/news/245035: «Broomfield International Limited
  зарегистрирована в августе прошлого года на Сейшелах»; «Управляющий
  директор Европейской специальной ситуационной группы Goldman Sachs
  Максим Климов и управляющий директор Goldman Sachs в России Антон
  Шрейдер» предположительно выкупили часть активов; «сделка, вероятно,
  была убыточной для банка»;
- cnews.ru/news/top/2023-07-25_tsian_izgnali_s_amerikanskoj:
  «сразу после начала специальной военной операции России на Украине,
  NYSE приостановила торги акциями компании» (начало 2022); решение о
  делистинге — июль 2023 года;
- cnews.ru/news/top/2025-01-31_tsian_raskryl_svoih_aktsionerov:
  список акционеров на январь 2025 — «Дмитрий Крюков владеет 80% в
  сейшельском оффшоре Solvi Holdings, который через гонконгскую Ronder
  HK владеет 19,74%» (и ещё две цепочки, итого 36,88%), «Дмитрий Демин
  — 7,95% в прямом владении», «Максим Мельников — 6,26% через MM Asia
  Invest»; Broomfield International упомянута только «в историческом
  контексте (владела 9,4% в 2023 году)», в актуальном списке на январь
  2025 года НЕ значится;
- kommersant.ru/doc/8535353: «выручка [ЦИАН, 2025] увеличилась на
  16,7%, до 15,2 млрд руб.»; «чистая прибыль увеличилась на 16,2% — до
  2,9 млрд руб.»; «Скорректированная EBITDA в 2025 году составила 3,6
  млрд руб. ... 23,6%».

НЕ ВНЕСЕНО: (1) прямое подтверждение личности бенефициаров Broomfield
(Климов/Шрейдер) от них самих или Goldman Sachs — во всех источниках
это атрибуция «по данным РБК», не прямое признание сторон; (2) точная
судьба доли Broomfield между 2023 и январём 2025 года (продана,
размыта, скрыта в другой структуре) — источники не разрешают вопрос,
известно только, что к январю 2025 её нет в раскрытом списке; (3)
связь Broomfield с «Эльбрус Капиталом»/Дёминым/менеджментом ЦИАН — не
найдена; (4) редомициляция «Циан Технолоджи Лтд» в САР на о. Октябрьский
— только через WebSearch-пересказ, не проверена мной лично дословно.

Запуск: python3 pipeline/fix_goldman_cian_broomfield_postdeal.py
        python3 pipeline/fix_goldman_cian_broomfield_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0dedddbd'

OLD_ECO_CONTEXT = (
    'И в HeadHunter, и в ЦИАН Goldman Sachs вкладывался вместе с '
    'фондом «Эльбрус Капитал». На начало 2022 года «Эльбрус Капитал» '
    'владел 45,1% акций ЦИАН, ещё 8% принадлежали основателю площадки '
    'Дмитрию Дёмину, который держит свой пакет через компанию MPOC '
    'Technologies с Британских Виргинских островов.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Broomfield International — сейшельская '
    'структура, по данным РБК связанная с бывшими топ-менеджерами '
    'Goldman Sachs Максимом Климовым и Антоном Шрейдером (сами они и '
    'банк это не подтверждали); к январю 2025 года её нет в раскрытом '
    'списке акционеров ЦИАН — доля Broomfield упоминается только «в '
    'историческом контексте». Сама ЦИАН была исключена с NYSE в июле '
    '2023 года после приостановки торгов в начале 2022-го. Крюков '
    '(«Эльбрус Капитал») из капитала не вышел — на январь 2025 года '
    'контролирует 36,88% через сейшельские структуры. Выручка ЦИАН в '
    '2025 году выросла на 16,7% до 15,2 млрд ₽, чистая прибыль — на '
    '16,2% до 2,9 млрд ₽.'
)

OLD_SRC = [['CNews', 'https://www.cnews.ru/news/top/2023-02-14_goldman_sachs_prodal_aktsii_tsian']]
NEW_SRC = OLD_SRC + [
    ['Право.ru', 'https://pravo.ru/news/245035/'],
    ['CNews', 'https://www.cnews.ru/news/top/2023-07-25_tsian_izgnali_s_amerikanskoj'],
    ['CNews', 'https://www.cnews.ru/news/top/2025-01-31_tsian_raskryl_svoih_aktsionerov'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8535353'],
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
