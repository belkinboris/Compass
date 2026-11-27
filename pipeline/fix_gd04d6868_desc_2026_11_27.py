# -*- coding: utf-8 -*-
"""Профиль фонда brainbox_I (gd04d6868): платформа в описании была названа «brainbox VC»
и «экосистемы Brainbox», а в заголовке карточки g93a5e014 и в источниках — «brainbox.VC».
Находка второго чтения 27 ноября 2026: в одном посте два написания. Приведено к одному.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'gd04d6868'
OLD = 'Посевной венчурный фонд экосистемы Brainbox (в нее входит и краудинвестинговая платформа brainbox VC), вкладывающий в российские ИТ-компании на ранней стадии. Управляющий партнер — Сергей Егоров, он же — член совета директоров brainbox VC.'
NEW = 'Посевной венчурный фонд группы brainbox.VC (в нее входит и одноименная краудинвестинговая платформа), вкладывающий в российские ИТ-компании на ранней стадии. Управляющий партнер — Сергей Егоров, он же — член совета директоров brainbox.VC.'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    if comp['desc'] == NEW:
        print('уже применено')
        return 0
    assert comp['desc'] == OLD, comp['desc']
    comp['desc'] = NEW
    print('%s: desc -> %r' % (CID, NEW))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    assert comp['desc'] == OLD, comp['desc']
    comp['desc'] = NEW
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
