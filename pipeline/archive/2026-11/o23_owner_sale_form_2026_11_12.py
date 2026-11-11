# -*- coding: utf-8 -*-
"""Карточка очереди g90767425 («О23» / Ozon): решение владельца 12 ноября 2026 — это сделка с продавцом.

Владелец: «если у него был этот пакет и больше он не контролирует, значит он отчуждение тем
или иным образом совершил… в рамках нашего подхода к карточкам: Чачава продавец, покупатель
не раскрыт, предмет — контролирующий пакет АО «О23»».

Заголовок и продавец поставлены таблицей правок (fixes/o23_control_structural_2026_11_11.py).
Здесь — то, что `review.py` не ставит:
  * предмет «Контролирующий пакет акций АО «О23»» — слов «контролирующий пакет» в источниках
    нет, это квалификация владельца, а не цитата (запись `asset` в таблице правок приведена
    к этому значению тем же коммитом);
  * снят `no_parties` (у сделки теперь есть продавец) и `post_override` (пост собирается
    обычным шаблоном: продавец, покупатель «не раскрыт», предмет).
Отменяет o23_no_sale_parties_2026_11_11.py.

    python3 pipeline/archive/2026-11/o23_owner_sale_form_2026_11_12.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'g90767425'
OLD_ASSET, NEW_ASSET = 'АО «О23»', 'Контролирующий пакет акций АО «О23»'


def apply(doc):
    c = next(x for x in doc['cards'] if x['id'] == CID)
    if c.get('asset') == NEW_ASSET and 'no_parties' not in c and 'post_override' not in c:
        return False
    assert c.get('seller') == 'Александр Чачава', c.get('seller')   # сначала review.py --write
    assert c.get('asset') in (OLD_ASSET, NEW_ASSET), c.get('asset')
    assert str(c.get('no_parties') or '').startswith('Утрата контроля, а не продажа') or 'no_parties' not in c
    c['asset'] = NEW_ASSET
    c.pop('no_parties', None)
    c.pop('post_override', None)
    return True


def main(write):
    raw = open(PENDING, encoding='utf-8').read()
    changed = apply(json.loads(raw))
    if not write:
        print('Сухой прогон: %s. Запись — с ключом --write.' % ('предмет, no_parties и post_override будут изменены'
                                                              if changed else 'уже записано'))
        return 0
    fresh_raw = open(PENDING, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    if apply(fresh):
        with open(PENDING, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
