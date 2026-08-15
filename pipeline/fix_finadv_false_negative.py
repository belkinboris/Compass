# -*- coding: utf-8 -*-
"""Каталог вычитки, класс E1: «Не привлекался» в eco.finadv без опоры в
источнике — 1201 карточка (77% заполненных).

«Не привлекался» — категорическое отрицание («консультанта точно не
было»), а не пустота; урок уже записан в CLAUDE.md на примере ГАП
«Ресурс»/Granmulino, где источник прямо называл советника, хотя поле несло
«Не привлекался». Второй круг вычитки (18 августа 2026, 5 параллельных
агентов) проверил это поле у 5 карточек из 10 против живых источников — ни
в одной статья не подтверждала отсутствие консультанта, все просто молчали
о нём. При таком единообразии (1201 карточка — фактически дефолт
автоматического разбора, а не проверенный факт) неверно оставлять
категорическое отрицание как есть.

«Публично не сообщалось» — уже принятый в проекте плейсхолдер того же
смысла («мы не знаем», а не «точно не было»): регулярка `LAW_PLACEHOLDER` в
test_data.py распознаёт оба значения как равноценные заглушки, значит
замена не меняет форму инвариантов, только смысл сообщения читателю.

Правка НЕ трогает карточки, где finadv несёт что-то, кроме буквально «Не
привлекался» (реальное имя консультанта, «Не раскрывался» и т. п.) —
затрагивается только точное совпадение строки.

Запуск:
    python3 pipeline/fix_finadv_false_negative.py            # сухой прогон
    python3 pipeline/fix_finadv_false_negative.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD = 'Не привлекался'
NEW = 'Публично не сообщалось'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))

    plan = [d for d in data['deals'] if (d.get('eco') or {}).get('finadv') == OLD]
    print('Карточек с eco.finadv == %r: %d' % (OLD, len(plan)))
    for d in plan[:8]:
        print('  %s' % d['id'])

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for d in plan:
        d['eco']['finadv'] = NEW

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
