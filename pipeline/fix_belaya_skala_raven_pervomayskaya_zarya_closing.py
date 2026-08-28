# -*- coding: utf-8 -*-
"""«Белая скала»/Raven Russia (`g323cf076`): один из 16-17 юрлиц лота — ООО
«Первомайская заря» (на балансе бизнес-центр Kellermann Center, 25 000 кв. м,
Санкт-Петербург) — перешёл новому собственнику позже остальных, только
19 августа 2026 года (источник: t.me/dealsma/7318). Дописано в eco.context
как уточнение хронологии закрытия сделки; бенефициары «Белой скалы» (Сергей
Винокуров и Елена Кузнецова) в источнике совпадают с уже записанными в
law.struct — не новый факт, не переносится повторно.

Цитата не лежит в тексте старых источников — тот же приём, что и в прежних
правках этого поля: старое значение сохраняется, дописывается предложение
со ссылкой на новый источник.

Запуск: python3 pipeline/fix_belaya_skala_raven_pervomayskaya_zarya_closing.py           # проверка
        python3 pipeline/fix_belaya_skala_raven_pervomayskaya_zarya_closing.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g323cf076'
OLD_CONTEXT = (
    'Активы Raven Property Group были обращены в доход государства в '
    'начале 2025 года по иску Генпрокуратуры, признавшей передачу бизнеса '
    'российскому менеджменту в 2022 году притворной сделкой. Портфель '
    'выставлялся на торги пять раз: стартовая цена составляла 92,5 млрд '
    'руб., цена отсечения — 46,27–46,3 млрд руб.; итоговая цена 47,2 млрд '
    'руб. составляет около 30% от рыночной оценки активов в 120–160 млрд '
    'руб. (дисконт ~70%). На объектах имеются кредитные обременения на '
    '61,9 млрд руб.: 6 объектов в залоге у ВТБ, 5 — у Сбербанка, 2 — у '
    'Raiffeisen Bank, по 1 — у Unicredit и Кредит Европа Банка.'
)
ADDITION = (
    'Одно из юрлиц лота — ООО «Первомайская заря», на балансе которого '
    'находится бизнес-центр Kellermann Center (25 000 кв. м) в '
    'Санкт-Петербурге, — перешло «Белой скале» позже остальных: сделка по '
    'его покупке закрыта только 19 августа 2026 года.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['Сделки M&A (@dealsma)', 'https://t.me/dealsma/7318']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
