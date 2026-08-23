# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g0a2088ba (MGC Group /
Grupo Antolin): прямых новых фактов о самих заводах «Альта Северо-Запад»
и «Альта Поволжье» под управлением MGC не нашлось, но нашёлся релевантный
контекст о самой группе-покупателе — она продолжает консолидировать
автокомпонентные/автосборочные активы в России. Не через review.py: поле
уже занято текстом из другого источника.

Кандидат «Grupo Antolin подала на банкротство в Испании/США» НЕ внесён:
единственный источник (plasticstoday.com) вернул 403 при прямой
перепроверке (та же ошибка, что и у саб-агента) — по установленному
правилу непроверяемый источник в карточку не идёт.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
Интерфакс (30 мая 2026, business/1092800).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g0a2088ba'
OLD_CONTEXT = (
    'Заводы Antolin достались группе MGC не сразу после того, как от них '
    'избавился иностранный владелец. Группа приобрела их у лизинговой '
    'компании «Дельта» красноярского бизнесмена Василия Германа. '
    '«Дельта», согласно ЕГРЮЛ, выкупила эти активы у испанцев в марте '
    '2023 года.'
)
ADDITION = (
    'MGC Group продолжает расширять портфель автокомпонентных и '
    'автосборочных активов: 30 мая 2026 года стало известно, что MGC '
    'Group приобрел контроль в управляющей структуре калужского завода, '
    'собирающего Haval M6 — сделка закрыта 28 мая 2026 года, MGC '
    'приобрела 100% ООО «Автотех», управляющего заводом PSMA Rus.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += продолжение экспансии MGC Group в автопроме")
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
