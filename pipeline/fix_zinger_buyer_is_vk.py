# -*- coding: utf-8 -*-
"""Покупатель сделки VK/«Зингер» не был записан ни ссылкой, ни текстом.

Что чинит. У карточки `gf23149cf` («VK приобрела 100% акций ЗАО «Зингер»»)
поля `buyer` и `buyer_name` пусты: имя покупателя стояло ТОЛЬКО в
заголовке. На экране это плашка сторон без покупателя, а в аналитике —
отказ текстовых правил мультипликатора с причиной «стороны не названы»
(`parties`), хотя чтение подтвердило и цену, и долю, и периметр.

Почему это нашлось только сейчас. Инвариант
`test_gold_verified_multiples_are_a_subset_of_rule_candidates` («чтение
подтверждает, но не расширяет») покраснел ровно в тот момент, когда
чтение впервые подтвердило факты этой карточки: до чтения она нигде не
претендовала на допуск, и пустой покупатель никого не беспокоил. Тест
сработал как задумано — как сигнал «проверьте обоих», а не как формальность.

Основание. Заголовок карточки и дословная цитата, уже сохранённая в
`facts.nature.quote` (РБК): «Интернет-холдинг VK приобрел 100% акций ЗАО
«Зингер»…». Профиль VK в базе есть (`g4e694234`), поэтому пишется ССЫЛКА,
а не текст: текстовое имя рядом со ссылкой перекрывается ссылкой на
экране (урок про `seller`/`seller_id`).

Запуск: python3 pipeline/fix_zinger_buyer_is_vk.py [--write]
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'deals_promoted.json'
DEAL_ID = 'gf23149cf'
VK_ID = 'g4e694234'


def main(write: bool) -> None:
    data = json.loads(BASE.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    card = deals[DEAL_ID]
    assert card.get('buyer') is None, 'покупатель уже проставлен — скрипт больше не нужен'
    assert card.get('buyer_name') is None, 'покупатель записан текстом — решите, что верно, руками'
    assert card['title'].startswith('VK приобрела'), 'заголовок изменился, основание правки пропало'
    assert VK_ID in data['companies'], 'профиль VK не найден'
    assert data['companies'][VK_ID]['name'] == 'VK'
    print(f"{DEAL_ID}: buyer  None → {VK_ID} ({data['companies'][VK_ID]['name']})")
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['buyer'] = VK_ID
    BASE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
