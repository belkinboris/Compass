# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gbb0a5366» («Avito приобрел 100% сервиса по поиску новостроек
«Румбери»») — дочитывание нашло судебный иск, но не факт для
структурных полей.

Проверено лично прямым WebFetch:
- ComNews, https://www.comnews.ru/content/227340/2023-07-11/2023-w28/frii-otozval-isk-k-osnovatelyu-prodannogo-avito-servisa-poiska-zhilya,
  11.07.2023: в июле 2023 года ФРИИ (Фонд развития интернет-инициатив)
  подал иск к основателю «Румбери» Михаилу Хайкину, утверждая, что он
  ввёл фонд в заблуждение перед продажей контрольного пакета сервиса
  компании Avito; иск был впоследствии отозван после того, как Хайкин
  выплатил фонду компенсацию (сумма не раскрывалась).
- Rusbase, https://rb.ru/news/avito-roomberry/: оба сооснователя
  «Румбери» — Михаил Хайкин (60,48%) и Ольга Бочкова (39,52%) —
  покинули проект после сделки с Avito.

ВАЖНО — НЕ ВНОСИТСЯ И НЕ МЕНЯЕТСЯ структурными полями: отдельная,
независимая проверка (audit-it.ru, ЕГРЮЛ-агрегатор) обнаружила прямое
противоречие премисе карточки — по состоянию на последнее обновление
реестра (30.06.2026) Михаил Хайкин по-прежнему числится ЕДИНСТВЕННЫМ
учредителем и гендиректором ООО «Румбери», а Avito/ООО «КЕХ еКоммерц»
не встречается среди текущих или прежних участников вовсе. Это
серьёзное расхождение с `buyer`/`title` карточки — записано отдельно
как новая находка в CLAUDE.md, «Известные проблемы»: решение о том,
как поступить со структурными полями, оставлено человеку. Здесь
вносится ТОЛЬКО безопасный, аддитивный факт судебного иска, не
затрагивающий вопрос о структуре сделки.

НЕ ВНЕСЕНО: сумма компенсации Хайкина ФРИИ — источник её не называет;
судьба долей Хайкина/Бочковой после ухода — не выяснялась отдельно
от факта самого иска, это за рамками данной правки.

Запуск: python3 pipeline/fix_avito_rumberi_frii_lawsuit_context.py
        python3 pipeline/fix_avito_rumberi_frii_lawsuit_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gbb0a5366'

OLD_ECO_CONTEXT = (
    'Румбери" консолидируется под проект «Авито Недвижимость». '
    'Финансовые параметры сделки в пресс-службе Avito не раскрывают.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' В июле 2023 года ФРИИ подал иск к основателю'
    ' «Румбери» Михаилу Хайкину, утверждая, что он ввёл фонд в'
    ' заблуждение перед продажей сервиса Avito; иск был отозван после'
    ' того, как Хайкин выплатил фонду компенсацию (сумма не'
    ' раскрывалась). Оба сооснователя — Хайкин и Ольга Бочкова —'
    ' покинули проект после сделки.'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/227340/2023-07-11/2023-w28/frii-otozval-isk-k-osnovatelyu-prodannogo-avito-servisa-poiska-zhilya'],
    ['Rusbase', 'https://rb.ru/news/avito-roomberry/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
