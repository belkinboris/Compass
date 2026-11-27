# -*- coding: utf-8 -*-
"""Имя с правовой формой (legal_short) профилю «Военно-строительная компания» (gc99d37c0).

ЗАЧЕМ. Профиль заведен приемкой карточки g121443b6 (указ № 601) 27 ноября 2026.
`accept_card.apply_answer` ставит `legal_short` только формам из SINGLE_LEGAL (ООО, АО,
ПАО…), а «ППК» (публично-правовая компания) в этом списке нет; `party_legal_names.py`
тоже не знает этой формы и к тому же читает боевой сайт, где профиля еще нет. Без
`legal_short` приемка держит находку party_legal_form:buyer. Образец — профиль
g6921da17 «ППК «Фонд развития территорий»», у которого legal_short записан так же.
Источник имени — указ № 601 («публично-правовой компании "Военно-строительная
компания"») и реестр (datanewton: ППК «ВСК», ИНН 9704016606, ОГРН 1207700151427).

    python3 pipeline/fix_vsk_legal_short_2026_11_27.py            # сухой прогон
    python3 pipeline/fix_vsk_legal_short_2026_11_27.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID, NAME, LEGAL = 'gc99d37c0', 'Военно-строительная компания', 'ППК «Военно-строительная компания»'


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    prof = base['companies'][CID]
    assert prof['name'] == NAME, prof['name']
    if prof.get('legal_short') == LEGAL:
        print('уже записано')
        return 0
    assert not prof.get('legal_short'), prof.get('legal_short')
    print('%s legal_short: None -> %s' % (CID, LEGAL))
    if '--write' in argv:
        prof['legal_short'] = LEGAL
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
