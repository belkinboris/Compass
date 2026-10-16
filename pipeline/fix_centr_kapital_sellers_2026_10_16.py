# -*- coding: utf-8 -*-
"""Пять карточек передачи активов во временное управление «Центр
Капиталу» собраны с приблизительными/отсутствующими продавцами —
нашёлся более точный и богатый источник (телеграм-канал @dealsma,
прямо цитирующий указ президента №738 от 15 октября 2026 года).
Правит продавцов на точных непосредственных владельцев ДО указа
(не всегда исходный международный бренд — у «Каппа Рус» и «Эвиосис
Пэкэджинг Кубань» структура сменилась ещё до указа):
  Tarkett       — Tarkett (без изменений, подтверждено）
  Каппа Рус     — Sverige International Holdings AB (шведская, купила
                  российский бизнес у Smurfit Kappa в 2023 году)
  Менсен        — Menshen Beteiligungs-GmbH (без изменений)
  Онтэкс РУ     — было пусто, теперь Ontex
  Эвиосис       — было пусто, теперь Sonoco Products Company (купила
                  Eviosys, прежнего владельца, в 2024 году)

Запуск:
    python3 pipeline/fix_centr_kapital_sellers_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_centr_kapital_sellers_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'

CHANGES = {
    'g19410fc2': (None, 'Sverige International Holdings AB'),
    'gb3837d4d': (None, 'Menshen Beteiligungs-GmbH'),
    'gfc3e1ae2': ('Ontex Group', 'Ontex'),
    'gf803c055': (None, 'Sonoco Products Company'),
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    for cid, (old, new) in CHANGES.items():
        card = cards[cid]
        assert card.get('seller') == old, '%s: seller %r, ожидали %r' % (cid, card.get('seller'), old)
        print('%s: seller %r -> %r' % (cid, old, new))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_cards = {c['id']: c for c in fresh['cards']}
    for cid, (old, new) in CHANGES.items():
        fc = fresh_cards[cid]
        assert fc.get('seller') == old, '%s: seller поменяли параллельно — перечитайте' % cid
        fc['seller'] = new
        fc['seller_src'] = 'text'
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
