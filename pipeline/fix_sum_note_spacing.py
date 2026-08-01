# -*- coding: utf-8 -*-
"""Пробел между значком валюты и следующим словом.

ЧТО СЛОМАНО. У 2 карточек («Danone/Вамин Р», «СУЭК — Туапсинский и Мурманский
терминалы») в `sum`/`eco.val` значок `$` стоит вплотную к следующему русскому
слову: «191,5 млн $по данным Financial Times», «168 млн $за Мурманский
терминал». Само число и правило «валюта значком» (`normalize_sum.py`) тут ни
при чём — это обычный пропущенный пробел при склейке текста, и на экране
цифра с валютой и следующее слово выглядят одним слипшимся куском.

ЧТО ДЕЛАЕМ. Вставляем пробел между `$`/`€` и следующей русской буквой, если
между ними пробела нет. Не трогаем `$`/`€`, за которыми сразу цифра (это
и есть верный порядок «значок перед числом» — «$191,5 млн»), и не трогаем
ничего, кроме `sum`, `eco.sum`, `eco.val` — только эти поля показывают сумму
на экране.

Запуск:
    python3 pipeline/fix_sum_note_spacing.py            # сухой прогон
    python3 pipeline/fix_sum_note_spacing.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'
GLUED = re.compile(r'([\$€])([а-яёА-ЯЁ])')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    changes = []
    for d in data['deals']:
        eco = d.get('eco') or {}
        targets = [('sum', d, 'sum'), ('eco.sum', eco, 'sum'), ('eco.val', eco, 'val')]
        for label, obj, key in targets:
            old = obj.get(key)
            if not old or not GLUED.search(old):
                continue
            new = GLUED.sub(r'\1 \2', old)
            assert new != old
            changes.append((d['id'], label, old, new))
            if write:
                obj[key] = new

    print(f'карточек затронуто (полей): {len(changes)}')
    for did, label, old, new in changes:
        print(f'  {did} [{label}]')
        print(f'    было:  {old!r}')
        print(f'    стало: {new!r}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
