# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gd5741cbd (1С приобрела
51% AIINS/«Адепт»): дельта-поиск нашёл, что платформа под управлением 1С
привлекла крупного страхового партнёра — «РЕСО-Гарантия» — и получила
публичный прогноз масштаба. Не через review.py: цитируемые куски не
идут единым непрерывным фрагментом текста источника (между ними —
абзацы с другими подробностями), а комбинировать их в одну «quote» для
review.py нельзя — там quote обязана быть непрерывным куском.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
CNews (safe.cnews.ru, 15.07.2026).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gd5741cbd'
OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В июле 2026 года AIINS объявила о стратегическом партнёрстве с '
    '«РЕСО-Гарантия»: «"РЕСО-Гарантия" и InsurTech-платформа AIINS '
    '(совместное предприятие с фирмой "1С") объявили о начале '
    'стратегического партнерства», пользователи платформы теперь могут '
    '«выбрать продукты страхования имущества юридических лиц, '
    'ответственности, грузоперевозок, автопарков, ДМС» от «РЕСО-Гарантия». '
    'По оценке AIINS, «синергия технологических решений и интеграции '
    'софта в учетные системы позволит аккумулировать на платформе AIINS '
    'более 20 млрд руб. страховых премий к 2028 г.»'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: заполнено (партнёрство с РЕСО-Гарантия)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
