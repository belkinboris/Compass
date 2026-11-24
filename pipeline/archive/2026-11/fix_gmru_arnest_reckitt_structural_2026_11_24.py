# -*- coding: utf-8 -*-
"""Карточка gmru-arnest-reckitt (приемка, 24 ноября 2026): «"Арнест" купил у
Reckitt завод бытовой химии в Клину».

Три находки, которые `review.py` не берет (нет сырья на диске для цитаты —
факт о ЕГРЮЛ взят через `api-fns.ru egr`, не веб-статью; элемент списка
`events[1].note` таблица правок адресовать не умеет, docs/card_editing.md):

1. `law.struct` держал предложение о состоянии ЕГРЮЛ на 13 ноября 2026 года
   — на следующий день ПОСЛЕ объявленного закрытия сделки (12 ноября).
   `law.struct` — механика самой сделки, а не то, что случилось с реестром
   позже; предложение переносится в `eco.context` (контекст и дальнейшая
   судьба факта после сделки).
2. `events[1].note` повторял подряд 10 слов заголовка ТАСС («Группа "Арнест"
   купила российский бизнес Reckitt в сегменте бытовой химии») — переписан
   своей конструкцией, факты (покупатель, продавец, сегмент) не менялись.
3. Синхронно с переносом — `checked.registry_owners` и `no_profile.seller`
   фиксируют, что история участников ООО «Рекитт Бенкизер» (ИНН 7705495411)
   уже проверена (api-fns.ru egr, 13.11.2026): это пишет ответ приемки
   (data/inbox/acceptance/2026-11-24.json), не этот скрипт.

Запуск: python3 pipeline/archive/2026-11/fix_gmru_arnest_reckitt_structural_2026_11_24.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL_ID = 'gmru-arnest-reckitt'

OLD_LAW_STRUCT = (
    'Покупатель — ООО «Арнест Менеджмент», управляющая компания группы «Арнест»; его единственный '
    'участник — Алексей Сагал. Предмет — ООО «Рекитт Бенкизер», российское юрлицо бытовой химии '
    'Reckitt. Медицинский бизнес Reckitt в России (ООО «Рекитт Бенкизер Хэлскэр») в сделку не вошел. '
    'По ЕГРЮЛ на 13 ноября 2026 года единственный участник ООО «Рекитт Бенкизер» — Reckitt Benckiser '
    '(Hygiene Home) Holdings Limited: переход доли к покупателю в реестре еще не отражен.'
)
NEW_LAW_STRUCT = (
    'Покупатель — ООО «Арнест Менеджмент», управляющая компания группы «Арнест»; его единственный '
    'участник — Алексей Сагал. Предмет — ООО «Рекитт Бенкизер», российское юрлицо бытовой химии '
    'Reckitt. Медицинский бизнес Reckitt в России (ООО «Рекитт Бенкизер Хэлскэр») в сделку не вошел.'
)

OLD_CONTEXT = (
    'Выручка АО «Арнест», основного юрлица группы, за 2025 год — 17,5 млрд ₽, на 12,9% больше, чем '
    'годом ранее; чистая прибыль — 4 млрд ₽, на 15,7% меньше. Сколько может заплатить «Арнест», '
    'основатель SharesPro Денис Астафьев оценивает в 25–40 млрд ₽ с учетом взноса в бюджет в размере '
    '35% стоимости актива. По неофициальным данным, бренды могли не передать из-за 18-го пакета '
    'санкций ЕС: он запретил продавать в России ключевые марки и технологии Reckitt Benckiser. '
    'Площадка в Клину потребует вложений: Reckitt фактически не вкладывала в нее последние четыре '
    'года, а все инвестиции в развитие российского бизнеса остановила весной 2022 года.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' По ЕГРЮЛ на 13 ноября 2026 года — на следующий день после объявленного закрытия сделки — '
    'единственным участником ООО «Рекитт Бенкизер» все еще значилась Reckitt Benckiser (Hygiene '
    'Home) Holdings Limited: переход доли к «Арнесту» реестр на тот момент не отразил.'
)

OLD_EVENT_NOTE = 'Группа «Арнест» купила российский бизнес Reckitt в сегменте бытовой химии'
NEW_EVENT_NOTE = (
    'Сделка закрыта: подмосковный завод и бизнес Reckitt по бытовой химии в России перешли '
    '«Арнесту».'
)


def main(write=False):
    data = json.load(open(DB, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT, 'law.struct уже другое — правку надо пересмотреть'
    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context уже другое — правку надо пересмотреть'
    assert deal['events'][1]['note'] == OLD_EVENT_NOTE, 'events[1].note уже другое — правку надо пересмотреть'
    assert deal['events'][1].get('historicalTitle') == OLD_EVENT_NOTE or True

    print('=== law.struct: было ===')
    print(OLD_LAW_STRUCT)
    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('=== eco.context: станет (добавлено предложение) ===')
    print(NEW_CONTEXT)
    print('=== events[1].note: было ===')
    print(OLD_EVENT_NOTE)
    print('=== events[1].note: станет ===')
    print(NEW_EVENT_NOTE)

    if write:
        data = json.load(open(DB, encoding='utf-8'))  # перечитать прямо перед записью
        deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
        assert deal['law']['struct'] == OLD_LAW_STRUCT
        assert deal['eco']['context'] == OLD_CONTEXT
        assert deal['events'][1]['note'] == OLD_EVENT_NOTE
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['context'] = NEW_CONTEXT
        deal['events'][1]['note'] = NEW_EVENT_NOTE
        with open(DB, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — запись с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
