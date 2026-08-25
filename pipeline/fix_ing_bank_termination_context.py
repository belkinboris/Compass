# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g2d90c4d5 (ING Group
расторгла соглашение о продаже ИНГ Банка «Глобал Девелопмент»):
дельта-поиск нашёл официальный пресс-релиз ING (первичный источник) и
разбор Moscow Times, объясняющий, ЧЬЁ именно одобрение не смог получить
покупатель — президента РФ (с 2022 года такие сделки требуют личного
согласования). Банк после срыва сделки продолжает работать: лицензия
ЦБ действует, рейтинг подтверждён в марте 2026 года, нового покупателя
источники не называют. Не через review.py: цитаты из ДВУХ новых
источников (ing.com, themoscowtimes.com) в разных полях.

Запуск: python3 pipeline/fix_ing_bank_termination_context.py
        python3 pipeline/fix_ing_bank_termination_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2d90c4d5'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'С 2022 года продажа крупными иностранными компаниями российских '
    'активов требует личного согласования президента РФ. По данным The '
    'Moscow Times, именно такое разрешение не смог получить покупатель '
    '(АО «Глобал Девелопмент») — это и стало причиной, по которой ING '
    'не увидела «реалистичных ожиданий» на одобрение сделки.'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'После срыва сделки ИНГ Банк продолжает работать как действующее '
    'юрлицо: банковская лицензия ЦБ РФ действует, банк участвует в '
    'системе страхования вкладов, кредитный рейтинг «Эксперт РА» '
    '(ruAA-, стабильный) подтверждён 10 марта 2026 года. Новый '
    'покупатель в открытых источниках не назван; ING заявляет, что '
    'по-прежнему намерена выйти из российского бизнеса и оценивает '
    'альтернативные варианты. Офшорная экспозиция ING к российским '
    'клиентам (вне периметра самого банка) на конец 2025 года снизилась '
    'почти на 90%, до €0,6 млрд, из них €0,3 млрд — под покрытием ECA '
    'или CPRI.'
)

NEW_SRC = [
    ['ing.com', 'https://ing.com/news/press-releases/ing-has-terminated-sale-agreement-for-its-russian-business.html'],
    ['themoscowtimes.com', 'https://www.themoscowtimes.com/2026/04/07/ing-terminates-sale-of-russian-business-a92442'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
