"""Казначейский выкуп: buyer_is_target=True на gc816c617 (docs/card_parties.md,
«Казначейский выкуп общество собственной доли», 2026-11-14/15/22). Профиль
«Красная звезда» уже стоит в target — тестом запрещено ставить его и в buyer
(test_one_company_holds_one_role_in_a_deal), поэтому роль покупателя
остается пустой по защите схемы, а не потому, что он не известен. Явный флаг
говорит format_post.py, что печатать вместо «не раскрыт» (не трогает buyer/
target сами, не задевает ROLE_PAIRS). Структурная пометка, не цитата — вне
таблицы FIXES, как и прежние разовые скрипты для kind=custody/management.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = data.get('cards', data) if isinstance(data, dict) else data
    found = False
    for card in cards:
        if card.get('id') == 'gc816c617':
            found = True
            if card.get('buyer_is_target'):
                print('gc816c617: buyer_is_target уже стоит, ничего не меняю.')
                return
            if not write:
                print('gc816c617: поставил бы buyer_is_target=True (сухой прогон).')
                return
            card['buyer_is_target'] = True
            print('gc816c617: buyer_is_target=True записано.')
    if not found:
        print('gc816c617 не найдена в pending.json.')
        return
    if write:
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')


if __name__ == '__main__':
    main()
