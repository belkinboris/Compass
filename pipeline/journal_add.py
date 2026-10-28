# -*- coding: utf-8 -*-
"""Запись в журнал PRODUCT_ROADMAP.md без чтения файла целиком.

Зачем. Журнал пишут рутины каждый час, а чтобы вставить запись правкой
файла, агент сначала читает весь PRODUCT_ROADMAP.md (68 тыс. токенов на
28 октября 2026) — это главный расход токенов каждого прогона. Скрипт
вставляет запись сразу под заголовком «## 5. Журнал работ», файл агент не
открывает.

Запуск:
    python3 pipeline/journal_add.py --file запись.md [--write]
    printf '...' | python3 pipeline/journal_add.py --write

Запись: первая строка «### ГГГГ-ММ-ДД (рутина, ЧЧ:ММ МСК) — что сделано»,
последняя — «Знание: docs/<тема>.md#<раздел>» или «Знание: нет — <почему>»
(CLAUDE.md). Без этого запись не принимается.
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, 'PRODUCT_ROADMAP.md')
HEADER = '## 5. Журнал работ'
FIRST = re.compile(r'^### \d{4}-\d{2}-\d{2} \(.+\) — \S')
KNOW = re.compile(r'^Знание:\s*\S', re.M)


def check(entry):
    lines = [l for l in entry.strip('\n').split('\n')]
    if not lines or not FIRST.match(lines[0]):
        return 'первая строка должна быть «### ГГГГ-ММ-ДД (рутина, время МСК) — что сделано»'
    if not lines[-1].startswith('Знание:'):
        return 'последняя строка должна начинаться с «Знание: …» (CLAUDE.md)'
    if 'ё' in entry or 'Ё' in entry:
        return 'в тексте для людей буква «е» вместо «ё»'
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--file', help='файл с записью; без него — читается stdin')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    entry = io.open(a.file, encoding='utf-8').read() if a.file else sys.stdin.read()
    entry = entry.strip('\n')
    problem = check(entry)
    if problem:
        print('Запись не принята: %s' % problem)
        return 1
    text = io.open(ROADMAP, encoding='utf-8').read()
    i = text.index(HEADER)
    j = text.index('\n', i) + 1
    if entry.split('\n', 1)[0] in text:
        print('Такая запись уже есть — ничего не делаю.')
        return 0
    new = text[:j] + '\n' + entry + '\n' + text[j:]
    print('Запись: %s' % entry.split('\n', 1)[0][:120])
    if not a.write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    io.open(ROADMAP, 'w', encoding='utf-8').write(new)
    print('Записано в PRODUCT_ROADMAP.md под «%s».' % HEADER)
    return 0


if __name__ == '__main__':
    sys.exit(main())
