# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g6a4b0a2a («Сергей Шишкарев выкупит 49%
УК «Дело» у «Росатома» и продаст «Ростеху»»): дельта-поиск нашёл, что
сюжет развернулся ПРОТИВОПОЛОЖНО заголовку карточки. `eco.context` уже
нёс факт отказа Шишкарева (26 июня 2026) — новые источники дают, что
случилось ПОСЛЕ: право выкупа перешло не к третьей стороне, а к самому
«Росатому», который теперь выкупает 51% САМОГО Шишкарева (обратное
направление сделки), а меморандум с «Ростехом» (СП на 74 млрд ₽) из-за
отказа Шишкарева не состоялся. На 8 июля 2026 (последний найденный
источник) сделка ещё оформлялась, не закрыта — статус карточки
«Обсуждается» остаётся верным.

Не через `review.py`: источники новые (Коммерсантъ, finance.mail.ru),
не образуют с уже записанным текстом `eco.context` непрерывный кусок.
Роли buyer/seller/type МЕХАНИЧЕСКИ не меняются — см. новую запись в
«Известных проблемах» CLAUDE.md, решение по структуре карточки за
человеком.

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.kommersant.ru/doc/8797464
https://finance.mail.ru/article/fas-soglasovala-hodatajstva-rosatoma-i-shishkareva-o-priobretenii-dolej-v-uk-delo-69207448/

Запуск: python3 pipeline/fix_shishkarev_delo_rosatom_reversal_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g6a4b0a2a'

OLD_CONTEXT = (
    'В ближайшие дни истекает срок, установленный корпоративным '
    'договором с Госкорпорацией "Росатом" для выкупа мною их доли… '
    'Выкупать пакет не буду'
)
CONTEXT_ADDITION = (
    ' Право покупки было согласовано ФАС заранее в обе стороны: '
    '4 мая 2026 года ведомство рассмотрело ходатайства АО '
    '«Атомэнергопром» (входит в «Росатом») и Сергея Шишкарева «о '
    'приобретении до 100% долей в уставном капитале ООО УК "Дело"» и '
    'приняло решение об их согласовании. После отказа Шишкарева право '
    'выкупа перешло к «Росатому»: по словам главы госкорпорации Алексея '
    'Лихачёва, «Корпоративное решение о том, что мы покупаем, принято» '
    '— то есть «Росатом» выкупает долю самого Шишкарева, а не наоборот. '
    'На начало июля 2026 года оформление сделки продолжалось и могло '
    '«продлиться до конца месяца». Меморандум о взаимопонимании с '
    '«Ростехом» по созданию СП (пакет 49% оценивался в 74 млрд ₽), '
    'заключённый Шишкаревым в апреле 2026 года, из-за его отказа не '
    'состоялся.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += сюжет развернулся — Росатом '
          f'выкупает долю Шишкарева')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal.setdefault('src', [])
        for entry in (
            ['Коммерсантъ', 'https://www.kommersant.ru/doc/8797464'],
            ['finance.mail.ru', 'https://finance.mail.ru/article/fas-soglasovala-hodatajstva-rosatoma-i-shishkareva-o-priobretenii-dolej-v-uk-delo-69207448/'],
        ):
            if entry not in deal['src']:
                deal['src'].append(entry)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
