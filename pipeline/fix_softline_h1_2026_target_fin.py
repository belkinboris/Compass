# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g8ea6e559
(Sk Capital инвестировала 5 млрд ₽ в Softline, приобретая более 10% акций,
август 2025) — `eco.target_fin` (финансы предмета сделки, самой ПАО
«Софтлайн») стоял прочерком «—». Через год после инвестиции появилась
первая отчётность цели за период, следующий за сделкой. Проверено лично
прямым WebFetch (vedomosti.ru/investments/news/2026/08/27/1224061-gk-softline-vishla,
27.08.2026): «Чистая прибыль ПАО "Софтлайн" за первые шесть месяцев
составила 892 млн руб. против 88 млн руб. чистого убытка, полученного по
итогам аналогичного периода годом ранее» и «Оборот компании вырос на 15%
год к году до 53,1 млрд руб.».

Периметр не спутан с чужими цифрами Sk Capital: `target` карточки —
именно ПАО «Софтлайн» (`gda7d982b`, тот же профиль, что назван в статье),
а не одна из дочерних структур группы (FabricaONE.AI и подобные несут
собственные, отдельные обороты и сюда не подмешаны) — родня уже
записанного класса ошибки «Русал»/Pioneer Aluminium и ВЭБ.РФ/Sk
Capital-«Сайберус» (см. CLAUDE.md), проверено намеренно.

НЕ ВКЛЮЧЕНО: разбивка оборота по собственным/сторонним решениям и
EBITDA — не относится напрямую к вопросу «как чувствует себя цель после
сделки», раздуло бы поле сверх того, что нужно читателю карточки о
сделке (см. правило «Одно поле — одна линза»). Причины улучшения
результата (M&A с 2022 года, Buy&Build) уже отражены в `eco.context` этой
же карточки отдельным, более ранним фактом — не дублируются.

Запуск: python3 pipeline/fix_softline_h1_2026_target_fin.py
        python3 pipeline/fix_softline_h1_2026_target_fin.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8ea6e559'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'Чистая прибыль ПАО «Софтлайн» за первые шесть месяцев 2026 года '
    'составила 892 млн ₽ против 88 млн ₽ чистого убытка, полученного по '
    'итогам аналогичного периода годом ранее; оборот компании вырос на '
    '15% год к году, до 53,1 млрд ₽ (Ведомости, 27 августа 2026).'
)

NEW_SRC_VEDOMOSTI = [
    'Ведомости',
    'https://www.vedomosti.ru/investments/news/2026/08/27/1224061-gk-softline-vishla',
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN

    new_src = deal['src'] + [NEW_SRC_VEDOMOSTI]

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== src: добавится ===')
    print(NEW_SRC_VEDOMOSTI)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
