# -*- coding: utf-8 -*-
"""Вычитка 9 ноября 2026, хвост (г): форма предмета у двух карточек.

После того как профилям сторон поставлено имя с правовой формой (fix_reread_2026_11_09_tail.py),
приемка увидела, что `eco.share` написан без формы общества (находка share_form):
  * berizaryad: «100% АО «Заряд!»» → «100% акций АО «Заряд!»» (у АО — акции, docs/card_parties.md);
  * gmru-svoj-kredit-evropa-strah: «100% долей «Кредит Европа лайф».» → доля в ООО с полным
    именем (ПРАЙМ: «купила 100% долей страховой компании "Кредит Европа лайф"»; реестр:
    ООО «Страховая компания «Кредит Европа Лайф»», ИНН 7705784734).
Записи FIXES этих полей получают отпечатки в proofread_absorbed.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_09_tail_d.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OPS = [('berizaryad', '100% АО «Заряд!»', '100% акций АО «Заряд!»'),
       ('gmru-svoj-kredit-evropa-strah', '100% долей «Кредит Европа лайф».',
        '100% доли в ООО «Страховая компания «Кредит Европа Лайф»».')]


def _apply(data):
    import review
    by = {d['id']: d for d in data['deals']}
    for cid, old, new in OPS:
        card = by[cid]
        assert card['eco']['share'] == old, (cid, card['eco']['share'])
        card['eco']['share'] = new
        for f in review.FIXES:
            if (f['id'], f['field']) == (cid, 'eco.share') and f['new'] is not None and f['new'] != new:
                marks = card.setdefault('proofread_absorbed', {}).setdefault('eco.share', [])
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data)
    print('eco.share: %d карточки' % len(OPS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))
    _apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
