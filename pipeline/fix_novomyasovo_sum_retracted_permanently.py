# -*- coding: utf-8 -*-
"""Приток 18.09.2026, часовой прогон 12:20 МСК — `enrich.py --write` ТРЕТИЙ
раз подряд вернул на карточку g5599430f (CPF/«Новомясово») сумму
«2,05 млрд ₽»: это уставный капитал вновь созданного SPV «Новомясово»,
совпавший по величине с ценой в заголовке TAdviser (не цена сделки — см.
pipeline/ingest/fixes/batch_2026_09_18_hourly_run.py и
pipeline/fix_novomyasovo_sum_reverted_by_enrich.py, где это уже дважды
снималось руками).

На этот раз, помимо снятия значения, оно записывается в новое поле
`retracted` — механизм, добавленный в этом же прогоне в `enrich.py`
(`is_retracted()`): «поле пусто» и «поле сознательно очищено» — разные
состояния, и без этой записи то же TAdviser-объявление, попадись оно в
ленте ещё раз завтра, тихо восстановило бы ту же ошибку в четвёртый раз.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

WRONG_SUM = '2,05 млрд ₽'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g5599430f']
    assert len(target) == 1, target
    card = target[0]
    assert card['sum'] == WRONG_SUM, repr(card['sum'])
    card['sum'] = None
    card.setdefault('retracted', {}).setdefault('sum', [])
    if WRONG_SUM not in card['retracted']['sum']:
        card['retracted']['sum'].append(WRONG_SUM)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Сумма g5599430f снята и записана в retracted. ЗАПИСАНО.')
    else:
        print('Сухой прогон: снял бы сумму и записал retracted. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
