# -*- coding: utf-8 -*-
"""Профиль g87582016 («Ракета» и IBC Corporate Travel): ключ «интернейшнл бизнес центр»
снят — в нем слово «бизнес», и test_data.py::test_match_key_alias_is_a_name считает такой
ключ куском заголовка. Остается «ibc corporate travel»; юрлицо профиля — в legal_short.

    python3 pipeline/fix_ibc_match_key_2026_11_18.py            # сухой прогон
    python3 pipeline/fix_ibc_match_key_2026_11_18.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PID, KEY = 'g87582016', 'интернейшнл бизнес центр'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # читается прямо перед записью
    keys = data['match_keys'].get(PID)
    assert keys is not None, 'профиля %s нет в match_keys' % PID
    if KEY not in keys:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    assert 'ibc corporate travel' in keys, keys
    keys.remove(KEY)
    print('%s: ключи -> %s' % (PID, keys))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Применено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
