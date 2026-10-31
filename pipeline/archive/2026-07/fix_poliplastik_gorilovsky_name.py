# -*- coding: utf-8 -*-
"""Качество, 25 сентября 2026 (ежедневный прогон 21:37 МСК) — очередь находок
аудита (CONTRADICTION), карточка `gmru-prime-pervy-poliplastik`. Председателя
совета директоров «Группы Полипластик» зовут Лев Гориловский, не Михаил —
дословно в интервью «Интерфаксу» (interfax.ru/interview/1112426, уже
добавлено в `src` этим же прогоном через `review.py`). Правка — только имя
внутри уже написанного абзаца (остальной текст — из mergers.ru), поэтому не
через `review.py` (потребовал бы, чтобы весь абзац лежал в одной цитате) и
не через `proofread.py` (его же проверка намеренно не пропускает смену
имени между old/new — здесь это не искажение перевода, а исправление
фактической ошибки, для которой и нужен отдельный скрипт с `assert`).

Запуск:
    python3 pipeline/fix_poliplastik_gorilovsky_name.py            # сухой прогон
    python3 pipeline/fix_poliplastik_gorilovsky_name.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_TEXT = 'Михаил Гориловский'
NEW_TEXT = 'Лев Гориловский'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'gmru-prime-pervy-poliplastik']
    assert len(target) == 1, target
    card = target[0]
    assert OLD_TEXT in card['eco']['context'], card['eco']['context']
    card['eco']['context'] = card['eco']['context'].replace(OLD_TEXT, NEW_TEXT)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Имя председателя совета директоров «Полипластика» исправлено на Лев. ЗАПИСАНО.')
    else:
        print('Сухой прогон: исправил бы имя. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
