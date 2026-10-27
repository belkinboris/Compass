# -*- coding: utf-8 -*-
"""«1С»/«Райтек» (g685f1e39): после приемки `asset` достался авто-заглушкой
(`accept_card.apply_answer` берет имя профиля предмета, когда `asset` в
ответе не передан) — пост печатал «Предмет: Райтек» вслед за «Участники
СП: 1С и Райтек», предмет повторял имя одного из участников. Заменено
описанием того, что создается (докстрока fix_g685f1e39_1c_raytek_jv —
источник CNews, 22 сентября 2026).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD = 'Райтек'
NEW = 'совместное предприятие «1С» и «Райтек» для автоматизации промышленных предприятий'


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g685f1e39')
    if card['asset'] == NEW:
        print('g685f1e39: уже применено')
        return 0
    assert card['asset'] == OLD, card['asset']
    card['asset'] = NEW
    print('g685f1e39: asset %r -> %r' % (OLD, NEW))
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
