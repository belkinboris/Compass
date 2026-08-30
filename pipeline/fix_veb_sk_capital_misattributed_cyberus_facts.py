# -*- coding: utf-8 -*-
"""Найдено при выборе месячной очереди (REVISION_BRIEF, третий
уровень), карточка g139d522a («ВЭБ.РФ вошла в акционерный капитал
инвестиционной платформы Sk Capital») — карточка несла факты и
источники СОВСЕМ ДРУГОЙ, более поздней сделки. Тот же класс дефекта,
что уже описан в CLAUDE.md для карточки «Русал»/Pioneer Aluminium:
id собрал факты чужой сделки, а не своей.

Заголовок, `date` (2024-02-01), `buyer`/`target` (ВЭБ.РФ/SK Capital) и
`extra` карточки — про НАСТОЯЩЕЕ событие: 1 февраля 2024 года ВЭБ.РФ
вошла в акционерный капитал инвестплатформы Sk Capital на паритетных
началах (50/50) с Фондом «Сколково». Но поля `sum`, `eco.sum`,
`eco.val`, `eco.target_fin`, `eco.context`, `eco.rationale` и ЧЕТЫРЕ ИЗ
ПЯТИ записей `src` (Коммерсантъ doc/8293936, ТАСС, ComNews, SecurityLab,
TAdviser) — про ДРУГУЮ сделку: Sk Capital купила миноритарную долю в
АО «Сайберус» (венчурный фонд кибербезопасности) в ДЕКАБРЕ 2025 года,
на 5 млрд рублей. Источник ошибки — запись в `pipeline/ingest/fixes/
batch_agents100_r1.py` («партия 5 агентов 14.08.2026, источник
comnews.ru») сама указывает на comnews.ru статью про Сайберус, но её
не проверили на соответствие ЗАГОЛОВКУ карточки; поля `sum`/`eco.sum`
и `eco.rationale` были даже не через `review.py` (в таблице `FIXES`
для них записей нет вовсе) — то есть правились ещё менее
дисциплинированным путём.

Проверено лично прямым WebFetch пяти источников:
- comnews.ru/content/243034 (Сайберус, декабрь 2025) — дословно:
  «ООО "СК Капитал"... АО "Сайберус"... Сумма: 5 млрд рублей за
  миноритарную долю» — подтверждает, что все «факты» карточки о
  Сайберусе, а не о ВЭБ.РФ/Sk Capital.
- kommersant.ru/doc/8293936 (17.12.2025) — дословно: «Компания SK
  Capital, входящая в корпорацию ВЭБ.РФ, инвестировала 5 млрд руб. в
  фонд развития кибербезопасности "Сайберус"» — тот же вывод.
- comnews.ru/content/231374 (01.02.2024, НАСТОЯЩИЙ источник этой
  карточки) — дословно: «ВЭБ.РФ вошла в акционерный капитал
  инвестиционной платформы Sk Capital (ООО "СК Капитал")» на
  «паритетных началах с Фондом "Сколково"»; «В публикации не
  раскрывается конкретная стоимость сделки».
- cnews.ru/news/line/2024-02-01_vebrf_voshla_v_sostav_aktsionerov —
  независимо подтверждает то же самое: паритет 50/50 со «Сколково»,
  сумма не названа, цель — технологические стартапы в кибербезопасности,
  телекоме, нефтесервисе, беспилотниках; Sk Capital на тот момент
  управляла фондами на «6+ млрд руб.».

`sum`/`eco.sum` — «5 млрд ₽» (сумма ЧУЖОЙ сделки) заменены на «Не
раскрыта» (настоящая сделка суммы не называла).
`eco.val`, `eco.target_fin`, `eco.context`, `eco.rationale` — очищены
от фактов о Сайберусе; `eco.context` заполнен настоящим контекстом
(масштаб фондов Sk Capital на момент сделки, цели ВЭБ.РФ).
`src` — четыре записи про Сайберус удалены, добавлены два настоящих
источника события 1 февраля 2024 года.

НЕ ВКЛЮЧЕНО: сама сделка Sk Capital/«Сайберус» (декабрь 2025, 5 млрд
₽) — это отдельное, настоящее событие, достойное СВОЕЙ карточки, а не
чужой; заведение новой карточки — отдельная задача, не входит в этот
скрипт.

Запуск: python3 pipeline/fix_veb_sk_capital_misattributed_cyberus_facts.py
        python3 pipeline/fix_veb_sk_capital_misattributed_cyberus_facts.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g139d522a'

OLD_SUM = '5 млрд ₽'
NEW_SUM = 'Не раскрыта'

OLD_VAL = (
    'Аналитик финансовой группы «Финам» Леонид Делицын сообщил '
    'корреспонденту ComNews, что стоимость активов «Сайберуса» можно '
    'оценить в 20–25 млрд руб. По словам Леонида Делицына, инвестировав '
    '5 млрд руб., Sk Capital может получить долю от 20% до 25%.'
)
NEW_VAL = '—'

OLD_TARGET_FIN = (
    'По данным из одних открытых источников, АО «Сайберус» за 2024 г. '
    'не получило выручки, чистый убыток составил более 700 млн руб., '
    'но другие открытые источники оценивают совокупную стоимость его '
    'активов по итогам 2024 г. в 18,5 млрд руб.'
)
NEW_TARGET_FIN = '—'

OLD_CONTEXT = (
    'Портфель фонда состоит из восьми компаний, включая Positive '
    'Technologies и F6, центр развития индустрии кибербезопасности '
    '«Кибердом», а также другие проекты и стартапы.'
)
NEW_CONTEXT = (
    'На момент сделки Sk Capital управляла венчурными фондами объёмом '
    'свыше 6 млрд рублей. ВЭБ.РФ вошла в капитал на паритетных '
    'началах (50/50) с Фондом «Сколково» — цель объединить финансовый '
    'ресурс госкорпорации с технологической экспертизой «Сколково» '
    'для поддержки стартапов в кибербезопасности, телекоме, '
    'нефтесервисе и беспилотных аппаратах (ComNews, CNews).'
)

OLD_RATIONALE = (
    'SK Capital (дочерняя структура ВЭБ.РФ и фонда «Сколково») '
    'приобрела миноритарную неконтролирующую долю менее 25% в '
    'уставном капитале АО «Сайберус»; операционное управление фондом '
    'сохраняется за командой «Сайберуса». По оценке аналитика Freedom '
    'Finance Global, исходя из стоимости активов фонда в 18,5 млрд '
    'руб. (по итогам 2024 г.), стоимость фонда на момент сделки могла '
    'составлять около 21–23 млрд руб., а доля SK Capital — около '
    '22–24%. Сделка вписывается в стратегию ВЭБ.РФ до 2030 г., в '
    'рамках которой госкорпорация планирует направить на венчурные '
    'инвестиции 50 млрд руб.'
)
NEW_RATIONALE = (
    'Наблюдательный совет ВЭБ.РФ принял решение направить на горизонте '
    'двух-трёх лет на венчурные инвестиции 50 млрд рублей при активном '
    'вовлечении частного капитала — вхождение в капитал Sk Capital '
    'вписывается в эту стратегию.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8293936'],
    ['ТАСС', 'https://tass.ru/ekonomika/25934911'],
    ['ComNews', 'https://www.comnews.ru/content/243034/2025-12-18/2025-w51/1008/sk-capital-kupil-minoritarnuyu-dolyu-ao-sayberus-za-5-mlrd-rub'],
    ['SecurityLab', 'https://www.securitylab.ru/news/567318.php'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/%D0%9A%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F:Cyberus_(%D0%A1%D0%B0%D0%B9%D0%B1%D0%B5%D1%80%D1%83%D1%81)'],
]
NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/231374/2024-02-01/2024-w05/1010/vebrf-voshla-akcionernyy-kapital-investicionnoy-platformy-sk-capital-ooo-sk-kapital'],
    ['CNews', 'https://www.cnews.ru/news/line/2024-02-01_vebrf_voshla_v_sostav_aktsionerov'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM, deal['sum']
    assert deal['eco']['sum'] == OLD_SUM, deal['eco']['sum']
    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['eco']['rationale'] == OLD_RATIONALE
    assert deal['src'] == OLD_SRC, deal['src']

    print('=== sum/eco.sum: было / станет ===')
    print(OLD_SUM, '->', NEW_SUM)
    print('\n=== eco.val: станет ===')
    print(NEW_VAL)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== eco.rationale: станет ===')
    print(NEW_RATIONALE)
    print('\n=== src: станет ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['val'] = NEW_VAL
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
