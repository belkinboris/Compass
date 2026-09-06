# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gfc260e10` («Ростелеком ведет переговоры по приобретению МегаФона»,
январь 2023, «Обсуждается») — одна из крупнейших потенциальных сделок
на телеком-рынке РФ так и осталась только переговорами: спустя более
трёх лет МегаФон работает независимо.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/russia/921787 (20.09.2023): глава Минцифры Максут Шадаев
  на прямой вопрос журналистов о сделке ответил — «Это не на повестке
  вопрос точно»;
- vedomosti.ru/investments/news/2026/08/21/1222839-megafon-viruchku-msfo
  (21.08.2026): МегаФон отчитался за первое полугодие 2026 года
  самостоятельно — выручка «264,6 млрд руб.» (+9,7%), чистая прибыль
  «19,4 млрд руб.» (+13%) — Ростелеком в материале не упоминается
  вовсе, МегаФон продолжает существовать как независимый оператор
  спустя более трёх лет после первых сообщений о переговорах.

Внесено: `status` меняется с «Обсуждается» на «Не состоялась» — не
через `review.py`/FIXES (фраза источника не входит буквально в
STATUS_WORDS, а сам источник и не лежит в локальном кэше притока), а
прямым скриптом с `assert`. Основание для перехода — не одно слово, а
совокупность: явное опровержение профильного министра на официальном
уровне ПЛЮС три с половиной года независимой отчётности цели без
единого признака смены контроля.

НЕ ВНЕСЕНО: причина, по которой переговоры не продвинулись (в
непроверенных сниппетах упоминается разногласие в цене между
«Ростелекомом» и USM Group) — не подтверждено дословным чтением;
структура собственников МегаФона (USM Group/USM Telecom/AF Telecom
Holding, контроль Алишера Усманова) — тоже только сниппет, не
проверено лично для этой карточки.

Запуск: python3 pipeline/fix_rostelecom_megafon_talks_fell_through.py
        python3 pipeline/fix_rostelecom_megafon_talks_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfc260e10'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Переговоры ничем не закончились. В сентябре 2023 года глава Минцифры '
    'Максут Шадаев на прямой вопрос о сделке ответил: «Это не на повестке '
    'вопрос точно». К августу 2026 года МегаФон по-прежнему отчитывается '
    'как независимая компания (выручка первого полугодия — 264,6 млрд ₽, '
    'чистая прибыль — 19,4 млрд ₽) без единого признака смены владельца.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5796556'],
]
NEW_SRC = OLD_SRC + [
    ['Интерфакс', 'https://www.interfax.ru/russia/921787'],
    ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/08/21/1222839-megafon-viruchku-msfo'],
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
