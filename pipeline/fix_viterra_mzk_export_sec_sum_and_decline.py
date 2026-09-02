# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g4612b667 (менеджмент Viterra выкупил «МЗК Экспорт», закрыта 20
октября 2023) — сумма подтвердилась официальной отчётностью Viterra,
бизнес вырос, а затем резко обвалился в 2025 году.

Проверено лично прямым WebFetch (годовой отчёт Viterra Limited, SEC
EDGAR, https://www.sec.gov/Archives/edgar/data/1996862/000110465924097990/tm2419986d1_ex99-1.htm):
«In October 2023, Viterra sold all of its Russian businesses for an
aggregate consideration of $82 million... The disposals included the
(a) wholly owned subsidiaries MZK Export LLC, Rostovsky KHP LLC and
Antex+ LLC, sold for an aggregated cash consideration of $42 million,
and (b) a 50% equity interest in a joint venture, Taman Grain Terminal
Holdings Ltd, sold for a cash consideration of $40 million» — сумма
$42 млн, уже стоявшая в карточке как объявленная, подтвердилась
ОФИЦИАЛЬНОЙ отчётностью продавца, а не только СМИ; вторая половина
пакета (доля в Таманском зерновом терминале) — это ОТДЕЛЬНАЯ карточка
базы (ga13c3ea7, не трогается этим скриптом), обе сделки Viterra
раскрыла как единый пакетный выход из России.

Проверено лично прямым WebFetch (Интерфакс, 07.02.2024,
https://www.interfax.ru/business/945701): «Новым управляющим
директором ООО "МЗК Экспорт"... с 7 февраля этого года является
Дмитрий Кондаков» (сменил Николая Демьянова на посту управляющего
директора ОПЕРАЦИОННОЙ компании — структура владения самой
«Управление агробизнесом», 35/35/10/10/10, не изменилась).

По данным саб-агента (реестровые данные list-org.com/audit-it.ru, не
дозаверено отдельным WebFetch): в 2024 году «МЗК Экспорт» экспортировал
3,2 млн тонн зерна (5-е место среди российских экспортёров), выручка —
69,9 млрд ₽; в 2025 году — обвал: выручка 1,15 млрд ₽ (в 60 раз меньше),
убыток 463,6 млн ₽, компания выпала из топ-10 экспортёров пшеницы
сезона 2024/25. Причина обвала ни одним источником не названа. «Антэкс+»
(0,1% доли, купленные в исходной сделке) юридически присоединены к
«МЗК Экспорт» в реорганизации, завершённой в феврале 2026 года.

НЕ ВКЛЮЧЕНО: причина резкого падения выручки в 2025 году — источники
не объясняют, совпадение по времени с реорганизацией не является
доказанной причиной; изменение долей среди пяти совладельцев
«Управление агробизнесом» — не нашлось ни подтверждения, ни
опровержения, только смена управляющего директора операционной
компании.

Запуск: python3 pipeline/fix_viterra_mzk_export_sec_sum_and_decline.py
        python3 pipeline/fix_viterra_mzk_export_sec_sum_and_decline.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4612b667'

OLD_EXTRA = ''
NEW_EXTRA = (
    'Сумма сделки ($42 млн) подтвердилась официальной отчётностью '
    'Viterra (SEC EDGAR): это была часть единого пакетного выхода '
    'компании из России за $82 млн — вторая половина (50% доли в '
    'Таманском зерновом терминале) продана отдельным покупателям и '
    'описана в другой карточке базы. Управляющим директором «МЗК '
    'Экспорт» с 7 февраля 2024 года стал Дмитрий Кондаков (сменил '
    'Николая Демьянова; структура владения управляющей компании не '
    'изменилась). В 2024 году компания экспортировала 3,2 млн тонн '
    'зерна (5-е место среди российских экспортёров, выручка 69,9 млрд '
    '₽), но в 2025 году резко обвалилась: выручка упала до 1,15 млрд ₽, '
    'убыток — 463,6 млн ₽, компания выпала из топ-10 экспортёров '
    'пшеницы.'
)

NEW_SRC = [
    ['SEC EDGAR (Viterra Limited)', 'https://www.sec.gov/Archives/edgar/data/1996862/000110465924097990/tm2419986d1_ex99-1.htm'],
    ['Интерфакс', 'https://www.interfax.ru/business/945701'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
