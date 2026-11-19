# -*- coding: utf-8 -*-
"""«Медскан»/KDL (gb82efd9f, static/data/pending.json): sum/eco.sum — «Не раскрыта».

Ни один источник не называет и не оценивает цену именно этой продажи (49% «Медскан
Лаб»/KDL); оценка «31 млрд ₽» относится к другому, более раннему пакету (выход
«Сбербанк инвестиций» из 39% в октябре 2025 года) — docs/card_money.md, «что не
цена». `review.py` формат «Не раскрыта» не разбирает (sum_is_supported ждет число
с единицей и валютой), поэтому поле снимается разовым скриптом, как Purmo Group и
«Туту»/«Ракета» (pipeline/archive/2026-11/tutu_sum_undisclosed_2026_11_18.py).

    python3 pipeline/archive/2026-11/fix_gb82efd9f_sum_2026_11_19.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))      # перечитано прямо перед записью
    d = next(x for x in data['cards'] if x['id'] == 'gb82efd9f')
    if d.get('sum') == 'Не раскрыта' and d['eco'].get('sum') == 'Не раскрыта':
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    assert d.get('sum') is None, d.get('sum')
    assert d['eco'].get('sum') == '—', d['eco'].get('sum')
    d['sum'] = d['eco']['sum'] = 'Не раскрыта'
    print('gb82efd9f: sum/eco.sum -> Не раскрыта')
    if write:
        fresh = json.load(open(PENDING, encoding='utf-8'))
        fd = next(x for x in fresh['cards'] if x['id'] == 'gb82efd9f')
        assert fd.get('sum') is None and fd['eco'].get('sum') == '—', 'состояние поля изменилось'
        fd['sum'] = fd['eco']['sum'] = 'Не раскрыта'
        json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
