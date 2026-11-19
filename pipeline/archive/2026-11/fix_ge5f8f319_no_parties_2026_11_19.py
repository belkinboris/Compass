# -*- coding: utf-8 -*-
"""Второе чтение ge5f8f319 (турцентр на ул. Маяковского в Липецке): после
того как `pipeline/ingest/fixes/fixes_ge5f8f319_second_reading_2026_11_19.py`
очистил `seller` (министерство — истец, не владелец и не продавец; переход
права не произошел и прямо запрещен судом до рассмотрения дела по существу),
карточке нужна причина пустых сторон (`no_parties`) — по аналогии с
карточками судебных изъятий (g06adc4cc, gad9394d1, gd561d849, gb03ecf13:
`no_parties` = «Изъятие по решению суда: покупателя и продавца нет, актив
перешел государству.»). Здесь решения еще нет, поэтому формулировка другая.

Через review.py не проводится: `no_parties` — не факт из цитаты, а
объяснение пустоты поля (как `accepted_notes`), а механическая проверка
review.check для прозы требует цитату дословно или ее пересказ по
verbatim_check — это не тот случай (docs/card_editing_scripts.md).

Разовый, со сборкой assert на прежнее состояние. Запуск:
    python3 pipeline/archive/2026-11/fix_ge5f8f319_no_parties_2026_11_19.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

NOTE = ('Министерство — истец в суде об изъятии недостроя, а не владелец: '
        'переход права собственности не произошел и до рассмотрения дела по '
        'существу запрещен самим судом (предварительное заседание отложено '
        'на 2 декабря 2026 года). Покупателя и продавца нет, пока суд не '
        'решил дело.')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c.get('id') == 'ge5f8f319'), None)
    if card is None:
        print('карточка ge5f8f319 не найдена в pending.json — уже промоутнута?')
        return 1
    assert card.get('seller') is None, 'seller уже не пуст — проверьте вручную'
    assert not card.get('no_parties'), 'no_parties уже стоит: %r' % card.get('no_parties')
    assert card.get('seller_src') == 'text', 'seller_src неожиданный: %r' % card.get('seller_src')
    print('ПИШУ no_parties =', NOTE)
    print('УБИРАЮ seller_src (сирота после очистки seller)')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    card['no_parties'] = NOTE
    card.pop('seller_src', None)
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
