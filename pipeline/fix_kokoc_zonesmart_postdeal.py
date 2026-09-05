# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gbbad8e7c` («Kokoc Group купила сервис ZoneSmart для e-commerce и
маркетплейсов», 2023-01-24, Закрыта) — `eco.context` был пуст,
дальнейшая судьба предмета сделки (2024-2025) не прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты, audit-it.ru/
contragent/1197746227755_ooo-zonsmart):
- «Учредителями ООО "ЗОНСМАРТ" являются: Шокуров Александр Викторович
  (с 10.01.2023) и Косилов Вячеслав Владимирович (с 19.06.2025)»;
- за 2025 год: выручка «73,9 млн руб.» (снизилась на 63,4%), результат
  — «убыток в размере 54,4 млн руб.»;
- за 2024 год: выручка ≈202 млн руб., результат — «прибыль 28 млн
  руб.»;
- «Чистые активы ООО "ЗОНСМАРТ" по состоянию на 31.12.2025 были
  отрицательные» (точная сумма не раскрыта источником).

НЕ ВНЕСЕНО: (1) Артём Косилов, основатель сервиса, — по докладу
саб-агента, ушёл в 2022 году (только LinkedIn, WebFetch на LinkedIn
недоступен — ошибка 999, не проверено дословно); (2) возможная связь
Артёма Косилова с Вячеславом Косиловым (учредитель с 19.06.2025) — имена
разные (Артём/Вячеслав), общей фамилии недостаточно для вывода о
родстве или об одном лице, не утверждается; (3) достигнут ли earn-out
(до 140 млн ₽ за два года по `law.terms`) — ни один источник не
раскрывает; (4) более ранняя находка саб-агента о выручке 2025 года
через clickfile.ru — заменена личной проверкой того же факта на
audit-it.ru, которая совпадает по цифрам.

Запуск: python3 pipeline/fix_kokoc_zonesmart_postdeal.py
        python3 pipeline/fix_kokoc_zonesmart_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gbbad8e7c'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'По данным ЕГРЮЛ, учредителями ООО «Зонсмарт» числятся Александр '
    'Шокуров (с 10 января 2023 года — момента сделки) и Вячеслав '
    'Косилов (с июня 2025 года). Выручка сервиса выросла до 202 млн ₽ '
    'в 2024 году при чистой прибыли 28 млн ₽, но в 2025 году упала до '
    '73,9 млн ₽ (-63%) с убытком 54,4 млн ₽; чистые активы на конец '
    '2025 года стали отрицательными.'
)

OLD_SRC = [['RB.ru', 'https://rb.ru/news/kokoc-zonesmart/']]
NEW_SRC = OLD_SRC + [['Audit-it', 'https://www.audit-it.ru/contragent/1197746227755_ooo-zonsmart']]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
