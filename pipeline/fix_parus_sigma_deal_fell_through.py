# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g573b8819
(Parus Asset Management (Central Properties) покупает логопарк «Сигма»
у группы Accent) — единственный источник был Telegram-агрегатором
(@dealsma), статус — «Обсуждается» (только ходатайство в ФАС). Найден
настоящий первоисточник, и он говорит обратное: сделка сорвалась ПОСЛЕ
одобрения ФАС.

Проверено лично прямым WebFetch (РБК Уфа, 21.02.2025, 10:14,
ufa.rbc.ru/ufa/21/02/2025/67b81fd99a79475dee0e2962): «в феврале ФАС
России согласовала московской инвестиционной компании Parus Asset
Management приобретение уфимского ООО "Складской комплекс "Сигма""» —
но «сделка не была завершена по независящим от нас причинам» (Антон
Комаров, директор департамента складской недвижимости Accent Capital).
Оценка эксперта (Елена Андреева, «Эксперт»): «цена сделки может
составить сотни миллионов» — не факт, а предположение о несостоявшейся
сделке.

`status`: «Обсуждается» → «Не состоялась» — прямая цитата
представителя ПРОДАВЦА о незавершении сделки сильнее, чем формальное
совпадение со словами из `STATUS_WORDS` review.py (тот же класс, что
уже применялся к БКС/«Форштадт»: перенос через отдельный скрипт, а не
через review.py, потому что естественный язык отказа не обязан
дословно совпадать со словарём). `src` заменён: Telegram-агрегатор — на
РБК Уфа. `eco.context` дополнен фактом срыва.

НЕ ВКЛЮЧЕНО: точная сумма сделки — не раскрыта (только предположение
эксперта о порядке величины, «сотни миллионов», не переносится как
факт). Дальнейшая судьба актива — по данным поиска, группа Accent
продолжает искать нового покупателя, свежих (позже марта 2025) новостей
о продаже кому-то ещё не нашлось; сам склад в марте 2025 получил нового
арендатора (Nemiroff) — это аренда, не сделка M&A, к карточке не
относится.

Запуск: python3 pipeline/fix_parus_sigma_deal_fell_through.py
        python3 pipeline/fix_parus_sigma_deal_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g573b8819'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_SRC = [['@dealsma (Telegram)', 'https://t.me/dealsma/5565']]
NEW_SRC = [
    ['РБК Уфа', 'https://ufa.rbc.ru/ufa/21/02/2025/67b81fd99a79475dee0e2962'],
]

OLD_CONTEXT = (
    'Принадлежащая Самонову группа Accent с партнерами давно хотели '
    'продать этот актив, но до сих ни с кем договориться не удавалось.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Сделка не состоялась: «в феврале ФАС России согласовала '
    'московской инвестиционной компании Parus Asset Management '
    'приобретение уфимского ООО "Складской комплекс "Сигма""», но '
    '«сделка не была завершена по независящим от нас причинам» (Антон '
    'Комаров, директор департамента складской недвижимости Accent '
    'Capital, РБК Уфа, 21 февраля 2025 года).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['src'] == OLD_SRC
    assert deal['eco']['context'] == OLD_CONTEXT

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== src: станет ===')
    for s in NEW_SRC:
        print(s)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['status'] = NEW_STATUS
        deal['src'] = NEW_SRC
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
