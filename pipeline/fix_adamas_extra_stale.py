# -*- coding: utf-8 -*-
"""Продолжение `fix_adamas_slh_closing.py`: поле `extra` карточки
`gcdec4f24` осталось со старым текстом («Переговоры... Сумма: 3–5 млрд
руб.») после того, как тот скрипт обновил `status`/`sum`/`date` на
данные закрытой сделки (28.01.2026, SLH Group, ~6,5 млрд ₽) — ровно тот
класс дефекта, о котором предупреждает REVISION_BRIEF («поле
противоречит другому полю той же карточки»): само поле `extra` не
входило в список полей, которые тот скрипт трогал, и я его пропустил
при первой записи.

Источник: kommersant.ru/doc/8380020 (уже в src карточки).

Запуск:
    python3 pipeline/fix_adamas_extra_stale.py            # сухой прогон
    python3 pipeline/fix_adamas_extra_stale.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'gcdec4f24'
OLD_EXTRA = ('Переговоры между MIUZ Diamonds и владельцем сети «Адамас». '
             'Источник: Kommersant. Сумма: 3–5 млрд руб. (оценка экспертов).')
NEW_EXTRA = ('Сделка закрыта 28 января 2026 года: сеть «Адамас» продана '
             'зарегистрированной в Гонконге SLH Group, созданной Шаем '
             'Шмая Леваевым (сын Льва Леваева, семья также контролирует '
             'MIUZ Diamonds). Продавец — Михаил Несветайло. Источник: '
             'Kommersant. Сумма: 6,5 млрд ₽ (по оценке экспертов).')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('extra') == OLD_EXTRA, \
        'extra уже другое: %r' % deal.get('extra')

    print('%s: extra -> %r' % (DEAL_ID, NEW_EXTRA))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['extra'] = NEW_EXTRA
    assert deal['extra'] == NEW_EXTRA, 'extra не записалось'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
