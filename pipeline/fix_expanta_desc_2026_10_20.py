"""Профиль «Экспанты» (g8fdefffc) — описание словами партнера, 20 октября 2026.

Партнер переписал строку покупателя в посте «Стакселя»: «…вкладывается в
разработчиков CPM-платформ, систем цифровизации промышленности». Пост берет
эту строку из `desc` профиля, поэтому правка — в профиле, а не в одном посте.
Без ключа — сухой прогон; --write перечитывает базу прямо перед записью.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = ('Инвестиционное подразделение ГК «Ультиматек», вкладывается в разработчиков корпоративного ПО — '
       'CPM-платформы, системы цифровизации промышленности.')
NEW = ('Инвестиционное подразделение ГК «Ультиматек», вкладывается в разработчиков CPM-платформ, '
       'систем цифровизации промышленности.')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies']['g8fdefffc']
    if comp.get('desc') == NEW:
        print('уже исправлено'); return
    assert comp.get('desc') == OLD, comp.get('desc')
    comp['desc'] = NEW
    print('g8fdefffc desc ->', NEW)
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
