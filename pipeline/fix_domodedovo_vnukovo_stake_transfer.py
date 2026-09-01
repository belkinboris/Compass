# -*- coding: utf-8 -*-
"""`domodedovo-aukcion` (Шереметьево приобрёл активы Домодедово на
аукционе на понижение, январь 2026) — продолжение сюжета, найденное
почасовым притоком 1 сентября 2026 (сырьё d81125950, Коммерсантъ,
19 августа): Шереметьево уступило Внуково 25,01% акций ООО «Перспектива»
(владеет активами Домодедово) за 16,5 млрд руб., сделка закрыта к
7 августа 2026 года.

Это ОТДЕЛЬНАЯ, более поздняя коммерческая сделка (другой покупатель —
Внуково, другой продавец — Шереметьево, своя сумма) поверх исходной
консолидации Шереметьево. Дополнение — не через review.py (поле `extra`
уже занято текстом из ДРУГОГО источника, дословная проверка целиком не
пройдёт), а прямым скриптом с ассертом на исходное значение. Структурные
поля исходной карточки (`buyer`/`seller`/`sum`/`status`) НЕ трогаются —
они по-прежнему описывают сделку Шереметьево/Домодедово января 2026 года,
а не последующую передачу доли Внуково. Решение, заводить ли отдельную
карточку на эту сделку, — за человеком (записано в PRODUCT_ROADMAP.md,
раздел «Известные проблемы»).

Запуск: python3 pipeline/fix_domodedovo_vnukovo_stake_transfer.py           # проверка
        python3 pipeline/fix_domodedovo_vnukovo_stake_transfer.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'domodedovo-aukcion'
OLD_EXTRA = (
    'Продажа государственного имущества (не банкротство: актив обращён в '
    'доход государства по иску Генпрокуратуры в июне 2025 года), торги на '
    'электронной площадке РТС-Тендер'
)
ADDITION = (
    'Аэропорт Внуково стал владельцем 25,01% акций ООО «Перспектива», '
    'которая контролирует активы аэропорта Домодедово. Доля аэропорта '
    'Шереметьево в капитале компании снизилась до 74,99%, свидетельствуют '
    'данные ЕГРЮЛ. Шереметьево и Внуково подтвердили планы совместного '
    'управления Домодедово 21 июля. Шереметьево уступало четверть акций '
    'компании за 16,5 млрд руб. Сделка закрыта к 7 августа 2026 года '
    '(Коммерсантъ).'
)
NEW_EXTRA = OLD_EXTRA + ' ' + ADDITION


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('extra') == OLD_EXTRA, 'extra уже другое: %r' % card.get('extra')

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['extra'] = NEW_EXTRA
    src = card.setdefault('src', [])
    kom_url = 'https://www.kommersant.ru/doc/8865213'
    if not any(len(s) > 1 and s[1] == kom_url for s in src):
        src.append(['Коммерсантъ', kom_url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
