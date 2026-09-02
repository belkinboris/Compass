# -*- coding: utf-8 -*-
"""`gaee6179c` («Самолет» выкупает долю партнёра в ЖК «Сабанеева 125»,
2 сентября 2026) — дополнение к `law.appr`, уже занятому фактом о
согласовании Газпромбанком схемы выкупа (см. `pipeline/ingest/fixes/
batch_2026_09_02_samolet_sabaneeva_liderstroy.py`). PrimaMedia (4 августа
2026) даёт две детали, которых нет в основном источнике (ПРАЙМ): точную
дату оспариваемого собрания и факт проверки прокуратуры с формальным
предостережением гендиректору застройщика.

Дополнение — не через review.py (поле уже занято, цитата покрывает
только новую часть, а не старое+новое целиком).

Запуск: python3 pipeline/fix_samolet_sabaneeva_prosecutor_check.py           # проверка
        python3 pipeline/fix_samolet_sabaneeva_prosecutor_check.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gaee6179c'
OLD_APPR = (
    'По его словам, Газпромбанк согласовал схему выкупа «Самолетом» доли '
    'партнера в проекте. Ожидается, что во второй половине октября '
    'возобновится финансирование строительства.'
)
ADDITION = (
    '«Лидер строй» оспорила в арбитражном суде решение общего собрания от '
    '21 ноября 2025 года, на котором планировалось одобрить крупные сделки '
    'с Газпромбанком. По результатам проверки прокуратуры Первореченского '
    'района Владивостока выявлены факты нарушения сроков строительства, в '
    'связи с чем генеральному директору организации-застройщика объявлено '
    'предостережение о недопустимости нарушений закона (PrimaMedia).'
)
NEW_APPR = OLD_APPR + ' ' + ADDITION


def _find_card(data, key):
    for c in data.get(key, []):
        if c['id'] == CARD_ID:
            return c
    return None


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = _find_card(pending, 'cards')
    path, key = PENDING, 'cards'
    if card is None:
        base = json.load(open(BASE, encoding='utf-8'))
        card = _find_card(base, 'deals')
        path, key = BASE, 'deals'
        data = base
    else:
        data = pending
    assert card is not None, '%r не найдена ни в pending.json, ни в базе' % CARD_ID
    assert card.get('law', {}).get('appr') == OLD_APPR, (
        'law.appr уже другое: %r' % card.get('law', {}).get('appr'))

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['law']['appr'] = NEW_APPR
    json.dump(data, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %r.' % path)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
