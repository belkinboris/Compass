# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c: второй круг второго чтения нашел, что `buyer_name`
подает платформу «Поток»/организатора BITL как факт ЗАКРЫТИЯ раунда, хотя
источник о закрытии (Ведомости) их вообще не называет — деталь целиком
из анонса (ComNews, июль 2025), как и доля/оценка, уже получившие
оговорку «при объявлении». Снимает деталь из buyer_name (остается просто
«частные инвесторы», это подтверждено и Ведомостями через «342
инвестора»); сама механика (платформа/организатор) переносится в
law.struct отдельно через write_card.py (нужна цитата в таблице FIXES).

Запуск:
    python3 pipeline/fix_visiology_buyer_struct_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_buyer_struct_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'

OLD_BUYER = 'частные инвесторы (платформа «Поток», организатор — BITL)'
NEW_BUYER = 'частные инвесторы'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in data['cards']}[CARD_ID]
    assert card.get('buyer_name') == OLD_BUYER, 'buyer_name уже не тот: %r' % card.get('buyer_name')
    print('%s: buyer_name %r -> %r' % (CARD_ID, OLD_BUYER, NEW_BUYER))
    print('party_evidence.buyer.value синхронизируется с новым buyer_name')
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc.get('buyer_name') == OLD_BUYER, 'buyer_name поменяли параллельно — перечитайте'
    fc['buyer_name'] = NEW_BUYER
    fc['party_evidence']['buyer'][0]['value'] = NEW_BUYER
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
