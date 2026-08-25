# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g2469d33a («СберИнвест»
приобрёл 12% акций «Аквариуса»): дельта-поиск нашёл структуру сделки
(«Сбер» — финансовый инвестор, одно место в совете директоров, право
вето по ключевым вопросам) и то, что доля выросла до 24% вторым траншем
к июню 2025 года. Точная дата второго транша нигде не названа. Не
переносится сюда: последующая продажа контроля (76-79%) S8 Capital и
«МТ-Интеграция» в 2025 году — это отдельная, уже заведённая в базу
сделка (`g139db8c2`), не эта. Не через review.py: цитаты из ДВУХ новых
источников (deloros.ru, cnews.ru) в разных полях.

Запуск: python3 pipeline/fix_sberinvest_akvarius_stake_context.py
        python3 pipeline/fix_sberinvest_akvarius_stake_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2469d33a'

OLD_STRUCT = '—'
NEW_STRUCT = (
    '«Сбер» не участвует в управлении компанией, но имеет одно место в '
    'совете директоров и согласующую функцию — право вето по ряду '
    'ключевых вопросов развития компании. «СберИнвест» выступает как '
    'финансовый инвестор, предоставивший деньги на развитие.'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'К июню 2025 года доля «СберИнвеста» выросла до 24% — вторым '
    'траншем ещё на 12% (точная дата второго приобретения не '
    'раскрывалась). Гендиректор «Аквариуса» Алексей Калинин не '
    'исключил, что в будущем «Сбер» может увеличить долю дальше: '
    '«любой бизнес продаётся и покупается», хотя «на сегодняшний день '
    'об этом разговоров нет».'
)

NEW_SRC = [
    ['deloros.ru', 'https://deloros.ru/press-centr/publikacii/glava-akvariusa-rbk-nam-dali-takoy-pinok-chto-my-khorosho-poleteli/'],
    ['cnews.ru', 'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_STRUCT
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.struct: станет ===')
    print(NEW_STRUCT)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['struct'] = NEW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
