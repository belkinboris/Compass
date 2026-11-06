# -*- coding: utf-8 -*-
"""White Square — юридический консультант в двух карточках, где фирма не была
отмечена (правки фирмы к странице, 6 ноября 2026; разбор — посты канала
t.me/whitesquarenews 907 и 911, перепосты @LawFirms 10854 и 10856).

gf9b54ee7 (Tasty Coffee): law.adv была заглушка «консультанты не раскрывались» —
неверно: пост 911 от 30.04.2026 — «White Square выступила юридическим
консультантом инвестиционного холдинга «Восток Инвестиции» в рамках сделки по
приобретению 20% в российском спешелти-обжарщике кофе «Tasty Coffee»».

g13d60ebc (Callisto Vision): к VERBA LEGAL добавляется White Square — пост 907
от 29.04.2026: «White Square выступила юридическим консультантом ведущего
российского разработчика решений для маркировки и контроля качества продукции
«Каллисто» (бренд Callisto Vision) по вопросам инвестиций со стороны
инвестиционной компании Kama Flow».

law.adv — список, review.py его не пишет (как fix_gf6c084b9_birch_2026_11_06.py).

    python3 pipeline/archive/2026-11/fix_whitesquare_adv_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TASTY_OLD = [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']]
TASTY_NEW = [['Консультант покупателя', 'White Square',
              'Юридический консультант инвестиционного холдинга «Восток Инвестиции» при покупке 20% Tasty Coffee. '
              'Источник: t.me/whitesquarenews/911']]
CALLISTO_ROW = ['Консультант Callisto Vision', 'White Square',
                'Юридический консультант «Каллисто» (Callisto Vision) по инвестициям Kama Flow. '
                'Источник: t.me/whitesquarenews/907']
SRC = {'gf9b54ee7': ['White Square (Telegram)', 'https://t.me/whitesquarenews/911'],
       'g13d60ebc': ['White Square (Telegram)', 'https://t.me/whitesquarenews/907']}


def apply(base):
    D = {d['id']: d for d in base['deals']}
    t, c = D['gf9b54ee7'], D['g13d60ebc']
    assert t['law']['adv'] == TASTY_OLD, t['law']['adv']
    assert [r[1] for r in c['law']['adv']] == ['VERBA LEGAL'], c['law']['adv']
    t['law']['adv'] = TASTY_NEW
    c['law']['adv'].append(CALLISTO_ROW)
    for i, s in SRC.items():
        assert s[1] not in json.dumps(D[i]['src']), (i, 'источник уже есть')
        D[i]['src'].append(s)


def main(argv):
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base)
    print('gf9b54ee7: law.adv -> White Square (покупатель); g13d60ebc: + White Square; + 2 источника')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(BASE, encoding='utf-8'))
    apply(base)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
