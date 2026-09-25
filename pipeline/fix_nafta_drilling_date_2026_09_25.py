# -*- coding: utf-8 -*-
"""Качество, 25 сентября 2026 (ежедневный прогон 21:37 МСК) — очередь находок
аудита (DATE_MISMATCH), карточка `g3d815d6f` (АО «Бурсервис» купило ООО
«Нафта Дриллинг Компани»). `date` карточки стоял 2024-12-16 — день подачи
ходатайства в ФАС (Коммерсантъ, doc/7380799), а не переход прав. Сама
карточка в своём же поле `law.struct` уже называет дату по ЕГРЮЛ:
«единственным участником общества покупатель стал по данным ЕГРЮЛ
21 февраля 2025 года». `review.py`'s `date_is_supported()` намеренно не
позволяет менять год через обычную запись FIXES (только день внутри
известного года) — правка года идёт одноразовым скриптом с `assert`, как и
предполагает эта защита.

Заодно поправлен профиль компании `gc06dddd1` («Нафта Дриллинг Компани»):
описание называло 2024 год вместо 2025 для той же сделки.

Запуск:
    python3 pipeline/fix_nafta_drilling_date_2026_09_25.py            # сухой прогон
    python3 pipeline/fix_nafta_drilling_date_2026_09_25.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_DATE = '2024-12-16'
NEW_DATE = '2025-02-21'
OLD_DESC = 'Буровая компания; в 2024 году её у Отгая Асланова купила ГК «Бурсервис» (преемник российского бизнеса Halliburton) для расширения услуг «Газпромнефти-Ноябрьскнефтегаза».'
NEW_DESC = 'Буровая компания; в 2025 году её у Отгая Асланова купила ГК «Бурсервис» (преемник российского бизнеса Halliburton) для расширения услуг «Газпромнефти-Ноябрьскнефтегаза».'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g3d815d6f']
    assert len(target) == 1, target
    card = target[0]
    assert card['date'] == OLD_DATE, repr(card['date'])
    assert '21 февраля 2025 года' in card['law']['struct']
    card['date'] = NEW_DATE

    company = data['companies']['gc06dddd1']
    assert company['desc'] == OLD_DESC, repr(company['desc'])
    company['desc'] = NEW_DESC

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Дата g3d815d6f и описание gc06dddd1 исправлены на 2025 год. ЗАПИСАНО.')
    else:
        print('Сухой прогон: поправил бы дату карточки и описание профиля. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
