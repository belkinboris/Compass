# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g4d7ccec0` («JPMorgan Chase приобрел First Republic Bank») — сама
ссылка на источник мертва (см. CLAUDE.md, «Известные проблемы»):
Fastly-прокси `mscwtimes.global.ssl.fastly.net` отдаёт DNS ENOTFOUND /
«500 Domain Not Found» в обеих проверенных сессиях.

Проверено лично прямым WebFetch: та же статья того же слага (`a41774`)
живёт на актуальном зеркале издания:
https://ru.themoscowtimes.com/2023/05/01/eto-ne-istoriya-2008-goda-krah-first-republic-zavershaet-bankovskuyu-paniku-a41774
— заголовок и первый абзац совпадают дословно с тем, что уже
процитировано по этой карточке в CLAUDE.md.

Это не решение вопроса о судьбе самой карточки (нероссийский сюжет без
российского элемента — см. отдельную запись в «Известные проблемы»,
решение за человеком) — только замена мёртвой ссылки на живую того же
источника, чтобы карточка не выглядела ссылкой в никуда, пока решение
не принято.

Запуск: python3 pipeline/fix_jpmorgan_first_republic_dead_source_link.py
        python3 pipeline/fix_jpmorgan_first_republic_dead_source_link.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4d7ccec0'

OLD_SRC = [
    ['The Moscow Times', 'https://mscwtimes.global.ssl.fastly.net/2023/05/01/eto-ne-istoriya-2008-goda-krah-first-republic-zavershaet-bankovskuyu-paniku-a41774'],
]
NEW_SRC = [
    ['The Moscow Times', 'https://ru.themoscowtimes.com/2023/05/01/eto-ne-istoriya-2008-goda-krah-first-republic-zavershaet-bankovskuyu-paniku-a41774'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['src'] == OLD_SRC

    print('=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
