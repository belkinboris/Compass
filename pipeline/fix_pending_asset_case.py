# -*- coding: utf-8 -*-
"""Разовая правка: падеж предмета у четырёх карточек, ждущих решения.

ЧТО СЛОМАНО. Карточки собраны притоком ДО того, как правило падежа
(`pipeline/ingest/casing.py`) научилось видеть предмет с названием в хвосте.
На экране и в проекте поста стояло «Предмет: бывшую лизинговую «дочку»
Mercedes-Benz» — ровно тот дефект, который владелец нашёл 9 августа в живых
постах канала. В базе таких не осталось (её починил `fix_asset_case.py`),
а очередь модерации тогда ещё была пуста.

ТРИ ИЗ ЧЕТЫРЁХ ЧИНИТ САМО ПРАВИЛО — и именно так они здесь и чинятся: скрипт
не переписывает значения от руки, а вызывает `to_nominative_asset` и сверяет
результат с ожидаемым. Если правило изменится, скрипт упадёт, а не тихо
запишет что-то другое.

ЧЕТВЁРТУЮ ПРАВИМ РУКАМИ, И ЭТО ОСОЗНАННО. «контролирующей "Домодедово"
компании» правило не берёт: между прилагательным и головой стоит имя
собственное в кавычках, и склонять голову через него — риск испортить имя.
Отказ правила верен; значение вписано явно и сверено с заголовком карточки.

Запуск:
    python3 pipeline/fix_pending_asset_case.py            # сухой прогон
    python3 pipeline/fix_pending_asset_case.py --write    # применить
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
sys.path.insert(0, os.path.join(HERE, 'ingest'))

from casing import to_nominative_asset  # noqa: E402

# id -> (что стоит сейчас, что должно стоять, чинит ли это само правило)
EXPECTED = {
    'gab0f3dde': ('бывшую лизинговую «дочку» Mercedes-Benz',
                  'бывшая лизинговая «дочка» Mercedes-Benz', True),
    'g7f6d55a9': ('частную сеть АЗС Elke Auto в Томске',
                  'частная сеть АЗС Elke Auto в Томске', True),
    'g18a6d375': ('казахстанскую ИТ-компанию Bilim Group',
                  'казахстанская ИТ-компания Bilim Group', True),
    # Правило отказывается (имя собственное между прилагательным и головой) —
    # вписано руками по заголовку карточки: «"Внуково" приобрело 25,01% в
    # контролирующей "Домодедово" компании».
    'g94268c8d': ('контролирующей "Домодедово" компании',
                  'контролирующая "Домодедово" компания', False),
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}

    plan, refused = [], []
    for cid, (old, new, by_rule) in EXPECTED.items():
        card = cards.get(cid)
        if not card:
            refused.append((cid, 'карточки нет в очереди'))
            continue
        cur = str(card.get('asset') or '')
        if cur != old:
            refused.append((cid, 'предмет уже другой: %r' % cur[:60]))
            continue
        got, changed = to_nominative_asset(old)
        if by_rule and not (changed and got == new):
            refused.append((cid, 'правило даёт %r, ожидали %r' % (got, new)))
            continue
        if not by_rule and changed:
            refused.append((cid, 'правило внезапно берётся за фразу: %r' % got))
            continue
        plan.append((cid, card, old, new, by_rule))

    for cid, why in refused:
        print('  ОТКАЗ %s: %s' % (cid, why))
    for cid, _card, old, new, by_rule in plan:
        print('  %s  %s' % (cid, 'правилом' if by_rule else 'руками'))
        print('        было: %s' % old)
        print('        стало: %s' % new)

    print('\nправок %d, отказов %d' % (len(plan), len(refused)))
    if refused:
        print('Есть отказы — не пишем НИЧЕГО.')
        return 1
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for _cid, card, _old, new, _by in plan:
        card['asset'] = new
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: поправлено предметов %d.' % len(plan))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
