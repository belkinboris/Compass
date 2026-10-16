# -*- coding: utf-8 -*-
"""Леста/«Промышленные сооружения» (gd09e0945): профиль покупателя `g5303268b`
несёт два предложения в `desc` — содержательное («Консорциум частных
инвесторов...») и короткое «Юрлицо — АО «Промышленные Сооружения».» в
кавычках. `format_post._pick_novel_sentences` всегда берёт предложение в
кавычках первым кандидатом независимо от места — пост печатал «Покупатель:
Юрлицо — АО «Промышленные Сооружения».», теряя содержательное описание.
Третий случай этого класса за двое суток (после g162de6fb и gbe13372d,
KNOWN_ISSUES.md) — склеивает оба предложения в одно, как и предыдущие два.

Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

COMPANY_ID = 'g5303268b'
OLD = ('Консорциум частных инвесторов, зарегистрирован в ноябре 2024 года; '
       'структура владения не раскрывается. Юрлицо — АО «Промышленные Сооружения».')
NEW = ('Консорциум частных инвесторов, зарегистрирован в ноябре 2024 года; '
       'структура владения не раскрывается, юрлицо — АО «Промышленные Сооружения».')


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    company = data['companies'][COMPANY_ID]
    assert company['desc'] == OLD, company['desc']
    company['desc'] = NEW
    print('%s: desc merged' % COMPANY_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main())
