# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g010ece87` («Игорь Ким продал сербский Expobank A.D. Belgrade
компании Adriatic Bank», год-заглушка «2022», Закрыта) — год сделки
не совпадает с годом, который называет собственный источник карточки,
а судьба банка после продажи (ребрендинг) не была внесена.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/5939524 (УЖЕ был в `src` карточки, использован для
  law.struct/eco.context, но его дата не была сверена с полем `date`)
  — статья опубликована «17.04.2023», а соглашение о продаже описано
  как подписанное «на прошлой неделе», то есть в апреле 2023 года, а
  не в 2022-м. Карточка путает эту дату с ДРУГИМ, более ранним шагом
  того же сюжета — продажей чешского Expobank CZ в сентябре 2022 года
  (после которой сербская «дочка» перешла к российскому Экспобанку;
  этот факт уже верно стоит в `law.struct` и относится к другой,
  предшествующей сделке, а не к продаже Adriatic Bank);
- b92.net/eng/news/business.php?yyyy=2023&mm=09&dd=01&nav_id=116537:
  «earlier this year in April, the majority owner of Adriatic Bank
  acquired Expobank A.D. Belgrade» — независимо подтверждает апрель
  2023 года; «As of today, September 1st, Expobank A.D. Beograd will
  officially operate under the new name, Adriatic Bank A.D. Beograd» —
  ребрендинг вступил в силу 1 сентября 2023 года.

Внесено: `date` исправлена с «2022» на «2023» (только год — точный день
источник не называет, месяц известен из контекста статьи, но не из
прямой цитаты с числом, поэтому в поле идёт год, а месяц — текстом в
`eco.context`, тот же принцип, что и у других дат-заглушек); в
`eco.context` добавлен факт ребрендинга. Правка года — не через
`review.py` (его `date_is_supported()` не переносит сделку в другой
год) и не через таблицу `FIXES` — прямая правка с `assert` на исходное
значение, тот же приём, что и `fix_osnova_sviblovo_date.py`.

НЕ ВНЕСЕНО: точный день подписания соглашения — ни один источник его
не называет, только «на прошлой неделе» относительно публикации
17.04.2023; финансовые показатели Adriatic Bank за 2025 год (прибыль,
активы) — встретились только в непроверенном сниппете поиска
(adriaticbank.rs, PDF годового отчёта), не в дословно прочитанной
странице, не переносится без прямой проверки.

Запуск: python3 pipeline/fix_expobank_belgrade_date_and_rebrand.py
        python3 pipeline/fix_expobank_belgrade_date_and_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g010ece87'

OLD_DATE = '2022'
NEW_DATE = '2023'

OLD_ECO_CONTEXT = (
    'Черногорский Adriatic Bank, купивший сербский банк, основан в 2016 '
    'году. Сначала он принадлежал Azmont Investment — структуре '
    'азербайджанской инвестиционной компании Azerbaijan Global '
    'Investments. В 2020 году Azmont Investment продал черногорский банк '
    'американской Adriatic Capital.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Сделка закрылась в апреле 2023 года, а с 1 '
    'сентября 2023 года сербский банк официально сменил вывеску — '
    'Expobank A.D. Belgrade стал называться Adriatic Bank A.D. Beograd.'
)

OLD_SRC = [
    ['Frank RG', 'https://frankrg.com/120349'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5939524'],
]
NEW_SRC = OLD_SRC + [
    ['B92', 'https://www.b92.net/eng/news/business.php?yyyy=2023&mm=09&dd=01&nav_id=116537'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
