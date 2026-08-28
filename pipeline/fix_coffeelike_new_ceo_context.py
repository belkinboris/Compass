# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf9df9712 (Invellect
приобрела 100% сети кофеен Coffee Like, октябрь 2024): дельта-поиск нашёл
смену гендиректора сети в июле 2025 года — Алексей Чижов, ранее возглавлял
ООО «Эй Кей Раша» (один из крупнейших франчайзи Rostic's/KFC в России,
~100 заведений), назначен явно для масштабирования бизнеса после смены
владельца. Заодно — финансовые показатели управляющей компании ООО «Кофе
Лайк» за 2024 год: выручка выросла на 26,3%, до 376,1 млн руб., чистая
прибыль — на 4,2%, до 177,1 млн руб. Обе цифры подтверждены лично прямым
WebFetch. `eco.context` был прочерком.

Запуск: python3 pipeline/fix_coffeelike_new_ceo_context.py
        python3 pipeline/fix_coffeelike_new_ceo_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf9df9712'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'В июле 2025 года новым генеральным директором сети назначен Алексей '
    'Чижов, ранее возглавлявший ООО «Эй Кей Раша» — одного из крупнейших '
    'франчайзи сети фастфуда Rostic\'s (ранее KFC), под управлением '
    'которого в России находилось около 100 заведений. Сам Чижов пояснил '
    'назначение так: «в конце 2024 года компанию купили новые инвесторы» '
    'и позвали его, «чтобы кратно масштабировать бизнес». В 2024 году '
    'выручка управляющей компании ООО «Кофе Лайк» выросла на 26,3% год к '
    'году, до 376,1 млн руб., чистая прибыль — на 4,2%, до 177,1 млн руб. '
    '(Коммерсантъ).'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7907166'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
