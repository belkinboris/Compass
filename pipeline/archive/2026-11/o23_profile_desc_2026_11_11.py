# -*- coding: utf-8 -*-
"""Профиль «О23» (g8a3b7795): из описания убрано «конечный бенефициар — Александр Чачава».

11 ноября 2026 Ozon сообщил, что структуры Чачавы утратили контроль над АО «О23»
(карточка g90767425 в очереди). Пост берет первую фразу описания профиля в строку
«Предмет» — и выходил бы со словами «конечный бенефициар — Александр Чачава» под
заголовком о том, что Чачава компанию больше не контролирует. Нового контролирующего
акционера, по сообщению Ozon, нет — в описании владелец не называется вовсе.
Карточки прошлых сделок (g01b8b8f6, g320f3f3f) не трогаются: там Чачава назван
владельцем на дату тех сделок.

    python3 pipeline/archive/2026-11/o23_profile_desc_2026_11_11.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'g8a3b7795'
OLD = ('Московская холдинговая компания, крупнейший акционер Ozon; конечный бенефициар — '
       'Александр Чачава. Юрлицо — АО «О23».')
MID = 'Московская холдинговая компания, крупнейший акционер Ozon. Юрлицо — АО «О23».'
# Второе чтение, 11 ноября 2026: слов «московская холдинговая» в источниках карточки нет,
# а пост ставит первую фразу описания в строку «Предмет». Юрлицо теперь в legal_short.
NEW = 'Акционерное общество, крупнейший акционер Ozon.'


def apply(data):
    prof = data['companies'][CID]
    if prof['desc'].startswith(NEW):   # приемка дописывает «Юрлицо — АО «О23».»
        return False
    assert prof['desc'] in (OLD, MID), prof['desc']
    prof['desc'] = NEW
    return True


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    changed = apply(json.loads(raw))
    if not write:
        print('Сухой прогон: описание профиля %s %s. Запись — с ключом --write.'
              % (CID, 'будет заменено' if changed else 'уже заменено'))
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    if apply(fresh):
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    else:
        print('Уже записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
