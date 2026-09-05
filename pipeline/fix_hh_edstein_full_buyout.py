# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g5fb345dc` («hh Ventures инвестировал в HRTech-стартап Edstein»,
2022-12-26, Закрыта, тип «Инвестиция») — `law.terms` уже называл опцион
HeadHunter на выкуп контрольной доли; дальнейшая судьба (реализован ли
опцион) не прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты)
vedomosti.ru/technology/articles/2025/05/07/1108766-headhunter-vikupila-100-hr-tech-kompanii-edstein:
- «В декабре 2024 г. рекрутинговый сервис увеличил свою долю в ООО
  "Эдштейн" с 25 до 100%»;
- «Большинство экспертов оценивают сумму этой сделки в 200–350 млн
  рублей»;
- «в январе 2025 г. структуры HeadHunter увеличили долю владения в ещё
  одном HR-стартапе Skillaz с 25 до 90,72%»;
- «В марте ООО "Эдштейн" было переименовано в ООО "Скилаз-ЛМС"».

НЕ ВНЕСЕНО: (1) финансовые показатели Edstein за 2024 год (выручка/
убыток) — саб-агент нашёл их только через WebSearch-пересказ, личный
WebFetch той же статьи Ведомостей их не подтвердил («в статье такая
информация не содержится»); (2) конфликт HeadHunter—Skillaz—VK —
целенаправленный поиск дал ноль, только неродственные споры
(«Робот Вера», ФАС/job.ru); (3) официальная сумма инвестиции 2022 года
(за 25%) — источник карточки прямо пишет «стороны не раскрывают объём
инвестиций», это уже отражено честной заглушкой в `sum`.

Запуск: python3 pipeline/fix_hh_edstein_full_buyout.py
        python3 pipeline/fix_hh_edstein_full_buyout.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5fb345dc'

OLD_ECO_CONTEXT = (
    'В 2020 году Edstein привлёк первый раунд инвестиций от фонда '
    'Kirov Group Ventures, который выступил операционным фондом и '
    'помог проекту выйти на устойчивую бизнес-модель.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' HeadHunter реализовал опцион полностью: в '
    'декабре 2024 года его доля в Edstein выросла с 25% до 100% '
    '(оценка сделки экспертами — 200–350 млн ₽, официально сумма не '
    'называлась). В марте 2025 года Edstein переименован в '
    '«Скилаз-ЛМС» и интегрирован в платформу Skillaz, в которой '
    'HeadHunter к январю 2025 года довёл долю до 90,72%.'
)

OLD_SRC = [['CNews', 'https://www.cnews.ru/news/line/2022-12-26_headhunter_investiroval_v_hr-tech']]
NEW_SRC = OLD_SRC + [['Ведомости', 'https://www.vedomosti.ru/technology/articles/2025/05/07/1108766-headhunter-vikupila-100-hr-tech-kompanii-edstein']]


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
