# -*- coding: utf-8 -*-
"""Второе чтение карточки g0158e326 (МГКЛ/инвестор) нашло: `eco.context`
не отвечает на свой вопрос («история и окружение», а не риск-оценка) и
почти дословно повторяет подпись к фото в источнике без атрибуции. Факт
перенесён в `extra` (переписан другими словами, FIXES-запись отдельная) —
здесь честная пустота вместо повтора.

Запуск:
    python3 pipeline/fix_g0158e326_eco_context_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_g0158e326_eco_context_2026_10_15.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g0158e326'

OLD = 'Главный риск для инвестора в этой сделке — репутационный: вокруг группы МГКЛ случались скандалы.'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['eco']['context'] == OLD, card['eco']['context']

    print('СНИМАЕМ %s: eco.context (перенесено в extra, неверное поле + почти дословный повтор)' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fresh_card = next(c for c in fresh['cards'] if c['id'] == CARD_ID)
    assert fresh_card['eco']['context'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh_card['eco']['context'] = '—'
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
