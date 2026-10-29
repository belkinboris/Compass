# -*- coding: utf-8 -*-
"""Карточка g3555ea6e («Логика молока» купила владельца бренда Velle): поля
`eco.context` и `eco.rationale` правились таблицей дважды — сначала
притоком (`written_g3555ea6e_2026_10_29.py`, из «—»), потом приемкой
(`accept_g3555ea6e_2026_10_29.py`: пересказ контекста; мотив — два раза,
второй раз сняли дословную цитату). `test_no_duplicate_fix_for_one_field`
допускает цепочку записей на одно поле, только если отпечатки всех записей,
кроме последней, лежат в `proofread_absorbed` карточки — так помечается
«поле переписано поверх прежней правки» (docs/card_editing.md). Скрипт
кладет недостающие отпечатки; текст карточки не меняет.

Запуск: python3 pipeline/fix_2026_10_29_g3555ea6e_absorbed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD = 'g3555ea6e'


def main(write):
    with open(PATH, encoding='utf-8') as fh:
        raw = fh.read()
    data = json.loads(raw)
    card = next(c for c in data['cards'] if c['id'] == CARD)
    absorbed = card.setdefault('proofread_absorbed', {})
    added = 0
    for field in ('eco.context', 'eco.rationale'):
        recs = [f for f in review.FIXES if (f['id'], f['field']) == (CARD, field)]
        assert len(recs) >= 2, (field, len(recs))
        marks = absorbed.setdefault(field, [])
        for f in recs[:-1]:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
                print('%s: отпечаток %s' % (field, fp))
    print('добавлено отпечатков: %d' % added)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    with open(PATH, 'w', encoding='utf-8') as fh:
        fh.write(out)
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
