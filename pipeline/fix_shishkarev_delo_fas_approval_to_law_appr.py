# -*- coding: utf-8 -*-
"""Карточка g6a4b0a2a (Шишкарев/УК «Дело»/«Росатом»): предыдущий скрипт
(`fix_shishkarev_delo_rosatom_reversal_context.py`) дописал в
`eco.context` факт о согласовании ФАС — `test_approval_is_not_left_in_
prose` справедливо это отклонил (упомянут госорган ФАС + слово
«согласование» в прозе, а `law.appr` при этом оставался заглушкой).
Переносит ИМЕННО согласование ФАС в `law.appr`, остальной текст
`eco.context` не трогает.

Запуск: python3 pipeline/fix_shishkarev_delo_fas_approval_to_law_appr.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g6a4b0a2a'

FAS_SENTENCE = (
    'Право покупки было согласовано ФАС заранее в обе стороны: 4 мая '
    '2026 года ведомство рассмотрело ходатайства АО «Атомэнергопром» '
    '(входит в «Росатом») и Сергея Шишкарева «о приобретении до 100% '
    'долей в уставном капитале ООО УК "Дело"» и приняло решение об их '
    'согласовании.'
)

OLD_CONTEXT = (
    'В ближайшие дни истекает срок, установленный корпоративным '
    'договором с Госкорпорацией "Росатом" для выкупа мною их доли… '
    'Выкупать пакет не буду ' + FAS_SENTENCE + ' После отказа '
    'Шишкарева право выкупа перешло к «Росатому»: по словам главы '
    'госкорпорации Алексея Лихачёва, «Корпоративное решение о том, что '
    'мы покупаем, принято» — то есть «Росатом» выкупает долю самого '
    'Шишкарева, а не наоборот. На начало июля 2026 года оформление '
    'сделки продолжалось и могло «продлиться до конца месяца». '
    'Меморандум о взаимопонимании с «Ростехом» по созданию СП (пакет '
    '49% оценивался в 74 млрд ₽), заключённый Шишкаревым в апреле 2026 '
    'года, из-за его отказа не состоялся.'
)
NEW_CONTEXT = OLD_CONTEXT.replace(FAS_SENTENCE + ' ', '')

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = FAS_SENTENCE


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['law']['appr'] == OLD_APPR, \
        f"law.appr: неожиданное значение {deal['law']['appr']!r}"

    print(f'{CARD_ID} eco.context: ФАС-предложение вырезано')
    print(f'{CARD_ID} law.appr: {OLD_APPR!r} -> согласование ФАС')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['law']['appr'] = NEW_APPR
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
