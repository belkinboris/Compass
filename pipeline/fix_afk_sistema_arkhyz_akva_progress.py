# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g2c2e274b
(АФК «Система» передала 100% «Архыз VITA» группе «Холдинг Аква»).
Проверено лично прямым WebFetch.

`eco.context` — дополнено судьбой объединённого холдинга. РБК Компании,
дословно: «прибыль компании составляет — 439 938 000 ₽», «выручка за
2025 год — 12 214 350 000 ₽».
Источник: https://companies.rbc.ru/id/1172651025788-ooo-obschestvo-s-ogranichennoj-otvetstvennostyu-holding-akva/

НЕ ВКЛЮЧЕНО: независимая оценка ЦЕНЫ именно этой сделки — не найдена
(источники повторяют только оценку Шумова для «Холдинг Аква» целиком,
уже стоящую в `eco.val`); консультанты — не найдены; стратегическое
объяснение объединения брендов (Коммерсантъ через rb.ru, ноябрь 2021
года — «объединение брендов позволит оптимизировать затраты на
логистику... «Ессентуки» в более высоком, а «Архыз» — в более
демократичном» ценовом сегменте) не включено: это план, озвученный до
самой покупки «Архыза» в 2022 году, а не постфактум-объяснение сделки
июня 2024 года — переносить план как причину закрытия значило бы
смешать два разных момента времени.

Запуск: python3 pipeline/fix_afk_sistema_arkhyz_akva_progress.py
        python3 pipeline/fix_afk_sistema_arkhyz_akva_progress.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2c2e274b'

OLD_CONTEXT = (
    'ООО «Аква Инвестиции», владеющее 100% ООО «Холдинг Аква», получило '
    'полный контроль над ООО «Архыз Оригинал», производителем воды '
    '«Архыз VITA», которого «дочка» «Системы» купила в 2022 году за 450 '
    'млн рублей.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' По итогам 2025 года «прибыль компании составляет — 439 938 000 '
    '₽», «выручка за 2025 год — 12 214 350 000 ₽» (РБК Компании).'
)

NEW_SRC = [
    ['РБК Компании', 'https://companies.rbc.ru/id/1172651025788-ooo-obschestvo-s-ogranichennoj-otvetstvennostyu-holding-akva/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
