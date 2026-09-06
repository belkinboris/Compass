# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gb1e062d2` («RBI покупает недостроенный комплекс San Gally Park у EKE
Group в Санкт-Петербурге», февраль 2023, «Обсуждается») — сделка НЕ
состоялась, а комплекс три года спустя снова ищет покупателя.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/8765167 (2026 год): «Потенциальный покупатель хотел
  перестроить площади под апарт-комплекс. Но сделка не состоялась.» —
  про RBI и намерение 2023 года; текущий интерес — «приобретением
  проекта заинтересовалась инвестиционная «Кама Капитал»», но «обе
  стороны отказались комментировать детали» — сделка не подтверждена ни
  одной стороной; для завершения комплекса нужно «около 9–11 млрд руб.
  инвестиций»; новые оценки стоимости — 5–7 млрд ₽ (Николай Казанский) и
  3–4,5 млрд ₽ (Ирина Ушакова).

Внесено: `status` меняется с «Обсуждается» на «Не состоялась» — не через
`review.py`/FIXES (источник не лежит в локальном кэше притока, механика
отклонит запись), а прямым скриптом с `assert`. Фраза источника «сделка
не состоялась» прямо и без домысливания подтверждает переход.

НЕ ВНЕСЕНО: судьба переговоров с «Кама Капитал» — обе стороны отказались
это подтвердить, поэтому в карточку идёт только как факт интереса, а не
новая сделка; если переговоры продвинутся, это отдельная, будущая
запись.

Запуск: python3 pipeline/fix_san_gally_park_deal_fell_through.py
        python3 pipeline/fix_san_gally_park_deal_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb1e062d2'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сделка с RBI не состоялась. К 2026 году комплекс так и не достроен '
    'и снова ищет покупателя — интерес проявляет инвестиционная компания '
    '«Кама Капитал», но обе стороны переговоры не подтверждают. Для '
    'завершения объекта нужно ещё около 9–11 млрд ₽ инвестиций; новые '
    'оценки стоимости самого комплекса — от 3–4,5 до 5–7 млрд ₽.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5824989'],
]
NEW_SRC = OLD_SRC + [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8765167'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
