# -*- coding: utf-8 -*-
"""events[0].note у gde69fa27 (VVP Group / БЦ «Порта») — почти дословная копия
лида источника (Коммерсантъ): accept_card.py нашел 19 слов подряд и 91% основ
в том же порядке. Элемент списка `review.py` не адресует (card_editing_scripts.md),
поэтому правка — одноразовым скриптом с `assert` на старое значение.

    python3 pipeline/archive/2026-11/fix_events_note_gde69fa27_2026_11_08.py [--write]
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'gde69fa27'
OLD = ('Один из крупнейших в России дистрибуторов электроники — VVP Group — выкупил у '
       'девелопера Forma 4 тыс. кв. м офисных площадей в бизнес-центре «Порта», недалеко '
       'от «Москва-Сити». Сумма сделки могла составить 2–2,4 млрд руб.')
NEW = ('VVP Group закрыла покупку офисного блока у Forma: 4 тыс. кв. м в «Порте», '
       'цена — по оценкам экспертов рынка, стороны ее не подтвердили.')


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CID)
    assert card['events'][0]['note'] == OLD, card['events'][0]['note']
    card['events'][0]['note'] = NEW


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    print('%s: events[0].note переписана' % CID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    apply(data)
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main('--write' in sys.argv))
