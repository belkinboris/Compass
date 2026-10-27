# -*- coding: utf-8 -*-
"""Поле `sum` у двух карточек не проходит проверку формата суммы
(test_data.py::test_cover_sum_uses_currency_symbol,
`review.py`'s `sum_is_supported` — обе подряд) — вне квотного механизма
review.py, потому что их формат сам по себе не укладывается в шаблон
«N[-M] млн|млрд [₽]»: тут не правка значения по цитате, а приведение
формата к принятому в базе написанию ТОГО ЖЕ факта.

gd0139978: `sum` стоит как тире-заглушка «—», что тест не распознаёт как
«не раскрыта» (497 карточек базы используют строку «Не раскрыта», не
тире) — сумма сделки (Denum Tech/«Альфа-Деньги») действительно не
раскрывалась, значение приводится к принятому написанию.

g6c2af36f: `sum` несёт валюту словом («224,8 тыс. евро») и единицу
«тыс.», которую `sum_is_supported()` не разбирает (только млн|млрд) —
причина, по которой правка идёт этим скриптом, а не таблицей FIXES.
Значение приводится к принятому написанию (значок перед числом), факт
не меняется: 224,8 тыс. евро ≈ 20,3 млн ₽, то же число, что уже стояло.

Запуск: python3 pipeline/fix_gd0139978_g6c2af36f_sum_format.py [--write]
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'deals_promoted.json'

CHANGES = {
    'gd0139978': {'old': '—', 'new': 'Не раскрыта'},
    'g6c2af36f': {'old': '224,8 тыс. евро (≈20,3 млн ₽)', 'new': '€224,8 тыс. (≈20,3 млн ₽)'},
}


def main(write: bool) -> None:
    data = json.loads(BASE.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    for cid, ch in CHANGES.items():
        card = deals[cid]
        assert card.get('sum') == ch['old'], (
            '%s: sum изменился (%r), правка устарела' % (cid, card.get('sum')))
        print('%s: sum  %r -> %r' % (cid, ch['old'], ch['new']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    data = json.loads(BASE.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    for cid, ch in CHANGES.items():
        card = deals[cid]
        assert card.get('sum') == ch['old'], (
            '%s: sum изменился (%r) между чтением и записью' % (cid, card.get('sum')))
        card['sum'] = ch['new']
    BASE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
